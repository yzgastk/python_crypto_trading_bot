#!/usr/bin/python3
# -*- coding: utf-8 -*-

###
# Part of python crypto trading bot available here : https://github.com/yzgastk/python_crypto_trading_bot
# Copyright (C) 2021  - Olivier DECOURBE - olivier.decourbe@protonmail.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
###

import requests
import datetime

import Orders
import BinanceAPI

import logging


logger = logging.getLogger(__name__)


class Wallet:
    commission_fee_taker = 0.04
    commission_fee_maker = 0.02
    spot_price_url = "https://api.binance.com/api/v3/ticker/price?symbol="
    future_price_url = "https://fapi.binance.com/fapi/v1/ticker/price?symbol="

    def __init__(self, name, wallet_dict, symbol_listing, base_symbol, futures=False, paper_trade=True):
        self.name = name
        self.wallet = wallet_dict
        self.quantity = {}
        self.symbol_gain = {}
        self.base_symbol = base_symbol
        self.futures = futures
        self.paper_trade = paper_trade
        self.orders = []
        self.active_long = []
        self.active_short = []
        self.exchange_info = Wallet.get_exchange_info()

        for symbol in symbol_listing:
            self.quantity[symbol] = 0.0
            self.symbol_gain[symbol] = 0.0

        if self.futures:
            self.base_price_url = Wallet.future_price_url
        else:
            self.base_price_url = Wallet.spot_price_url

    def get_value(self, symbol):
        return self.wallet[symbol]

    def get_base_balance(self):
        return self.wallet[self.base_symbol]

    def get_name(self):
        return self.name

    def get_quantity(self, symbol):
        return self.quantity[symbol]

    def get_actives(self):
        return [i for i in self.orders if i.get_active()]

    def get_inactives(self):
        return [i for i in self.orders if not i.get_active()]

    def get_order_by_symbol(self, symbol):
        for order in self.orders:
            if order.get_symbol() == symbol and order.get_active():
                return order
        return False

    def get_price(self, symbol="BTCUSDT"):
        r_json = requests.get(self.base_price_url+symbol, timeout=10)
        return float(r_json.json()['price'])

    @staticmethod
    def get_exchange_info():
        r_json = requests.get("https://api.binance.com/api/v3/exchangeInfo", timeout=10)
        return r_json.json()

    @staticmethod
    def get_spot_price(symbol="BTCUSDT"):
        r_json = requests.get(Wallet.spot_price_url+symbol, timeout=10)
        return float(r_json.json()['price'])

    def get_prices(self):
        price_dict = {}
        for key, value in self.quantity.items():
            price = self.get_price(key)
            price_dict[key] = price

        return price_dict

    def add_to_balance(self, value):
        buf = self.wallet[self.base_symbol]
        self.wallet[self.base_symbol] = buf + value

    def add_quantity(self, symbol, value):
        buf = self.quantity[symbol]
        self.quantity[symbol] = buf + value

    def order_exist(self, symbol, order_type):
        if order_type == 1:
            for order in self.active_long:
                if symbol == order.get_symbol():
                    return order
        elif order_type == 2:
            for order in self.active_short:
                if symbol == order.get_symbol():
                    return order
        return None

    def get_closed_profit(self):
        total = 0.0
        for i in self.symbol_gain:
            total += self.symbol_gain[i]
        return total

    def get_opened_profit(self):
        total = 0.0
        latest_prices = self.get_prices()
        for key, value in self.quantity.items():
            exist_short = self.order_exist(key, 2)
            exist_long = self.order_exist(key, 1)
            if exist_long:
                total += (latest_prices[exist_long.get_symbol()] * exist_long.get_quantity()) - (exist_long.get_price() * exist_long.get_quantity())
            elif exist_short:
                total += (exist_short.get_price() * exist_short.get_quantity()) - (latest_prices[exist_short.get_symbol()] * exist_short.get_quantity())
            else:
                pass
        return total

    def get_current_profit(self):
        total = self.get_closed_profit()
        total += self.get_opened_profit()
        return total

    def compute_usdt_ratio(self, symbol):
        # Orders are based on quote_asset for buying / selling
        # If it is different from USDT, using QUOTE/USDT pair is necessary to keep track of USD content in the wallet
        usdt_ratio = 1
        if symbol[-4:] != "USDT":
            xchg_info = self.exchange_info

            symbol_info = None
            for row in xchg_info['symbols']:
                if row['symbol'] == symbol:
                    symbol_info = row

            if symbol_info:
                quote_usdt = symbol_info['quoteAsset'] + "USDT"
                usdt_ratio = self.get_spot_price(quote_usdt)
            else:
                logger.error("Symbol : " + symbol + " not found in exchange_info(). Balance total may be incorrect !")
                return -1

        return usdt_ratio

    def process_order_removal(self, symbol, close_order, remove_list, price, coeff):
        logger.info("Order found for "+symbol+" - Closing it...")
        close_order.set_active(False)
        remove_list.remove(close_order)
        self.add_quantity(symbol, -close_order.get_quantity())
        usdt_ratio = self.compute_usdt_ratio(symbol)

        if usdt_ratio == -1:
            logger.error("Canceling process_order_removal() for "+symbol)
            return

        closing_commission = ((close_order.get_quantity() * self.commission_fee_taker) * price * usdt_ratio) / 100
        return_invest = (price * close_order.get_quantity()) - (close_order.get_price() * close_order.get_quantity())

        self.symbol_gain[symbol] += coeff * return_invest * usdt_ratio - closing_commission
        add_balance = usdt_ratio * close_order.get_price() * close_order.get_quantity() + return_invest - closing_commission
        logger.info("Adding to balance : " + str(add_balance))
        self.add_to_balance(add_balance)

        return

    def push_order(self, symbol, order_type, amount, take_profit=None, stop_loss=None, tpsl_percent=False):
        price = self.get_price(symbol)
        quantity = amount / price
        usdt_ratio = 1
        commission = ((quantity * self.commission_fee_taker) * price) / 100
        already_short = self.order_exist(symbol, 2)
        already_long = self.order_exist(symbol, 1)

        if already_long and order_type == 1:
            logger.info(self.get_name() + " - Long order rejected - Already long for " + symbol)
            return
        elif already_short and order_type == 2:
            logger.info(self.get_name() + " - Short order rejected - Already short for " + symbol)
            return

        if order_type == 1:
            active_list = self.active_long
            opposite_list = self.active_short
        elif order_type == 2:
            active_list = self.active_short
            opposite_list = self.active_long
        else:
            logger.info(self.get_name()+" - Incorrect order_type ("+order_type+")")
            return

        if already_short:
            close_order = already_short
            coeff = -1
        elif already_long:
            close_order = already_long
            coeff = 1
        else:
            close_order = None
            coeff = None

        if close_order:
            self.process_order_removal(symbol, close_order, opposite_list, price, coeff)
        else:
            usdt_ratio = self.compute_usdt_ratio(symbol)

            if usdt_ratio == -1:
                logger.warning("Symbol : " + symbol + " not found in exchange_info(). Aborting push_order() !")
                return

        if not self.paper_trade:
            # FixMe : Handle returned "fills" in case of real orders for more precise price & quantity
            real_order = BinanceAPI.buy_order_market(symbol, quantity)
            price = real_order
            quantity = real_order

        order = Orders.Orders(symbol, order_type, price, quantity, take_profit=take_profit, stop_loss=stop_loss, tpsl_percent=tpsl_percent)
        active_list.append(order)
        self.orders.append(order)
        self.add_to_balance(-commission * usdt_ratio)
        self.add_quantity(symbol, quantity)

    def exit_order(self, symbol):
        price = self.get_price(symbol)
        already_long = self.order_exist(symbol, 1)
        already_short = self.order_exist(symbol, 2)

        if already_short:
            remove_list = self.active_short
            close_order = already_short
            coeff = -1
        elif already_long:
            remove_list = self.active_long
            close_order = already_long
            coeff = 1
        else:
            return

        self.process_order_removal(symbol, close_order, remove_list, price, coeff)

        return

    def exit_all_orders(self):
        for symbol, qty in self.quantity.items():
            self.exit_order(symbol)

        return

    def check_take_profit_stop_loss(self):
        for order in self.active_long+self.active_short:
            symbol = order.get_symbol()
            price = self.get_price(symbol)

            if (order.get_order_type() == 1 and (order.get_stop_loss() >= price or order.get_take_profit() <= price)) \
                    or (order.get_order_type() == 2 and (order.get_stop_loss() <= price or order.get_take_profit() >= price)):
                self.exit_order(symbol)
        return

    def profit_to_str(self):
        buff_str = "{"
        latest_prices = self.get_prices()
        for key, value in self.quantity.items():
            exist_short = self.order_exist(key, 2)
            exist_long = self.order_exist(key, 1)
            if exist_long:
                buff_str += key+": "+str(self.symbol_gain[key] + (latest_prices[exist_long.get_symbol()] * exist_long.get_quantity()) - (exist_long.get_price() * exist_long.get_quantity()))+", "
            elif exist_short:
                buff_str += key+": "+str(self.symbol_gain[key] + (exist_short.get_price() * exist_short.get_quantity()) - (latest_prices[exist_short.get_symbol()] * exist_short.get_quantity()))+", "
            else:
                buff_str += key+": "+str(self.symbol_gain[key])+", "

        return buff_str+"}"

    def wallet_to_str(self):
        buff_str = "--- Wallet Status ---\n"
        for currency in self.wallet:
            buff_str += currency+": "+str(self.get_value(currency))
        return buff_str

    def quantities_to_str(self):
        buff_str = "{"
        for key, value in self.quantity.items():
            if self.order_exist(key, 1):
                order_type = "L"
            elif self.order_exist(key, 2):
                order_type = "S"
            else:
                order_type = "-"
            buff_str += key+": "+str(value)+"-"+order_type+"; "
        return buff_str+"}"

    def opened_symbol_profit(self):
        latest_prices = self.get_prices()
        buff_str = "{"
        for key, value in self.quantity.items():
            exist_short = self.order_exist(key, 2)
            exist_long = self.order_exist(key, 1)
            if exist_long:
                buff_str += key + ": " + str((latest_prices[exist_long.get_symbol()] * exist_long.get_quantity()) - (
                            exist_long.get_price() * exist_long.get_quantity())) + ", "
            elif exist_short:
                buff_str += key + ": " + str((exist_short.get_price() * exist_short.get_quantity()) - (
                            latest_prices[exist_short.get_symbol()] * exist_short.get_quantity())) + ", "
            else:
                pass
        return buff_str + "}"

    def overall_symbol_profit(self):
        latest_prices = self.get_prices()
        buff_str = "{"
        for key, value in self.quantity.items():
            exist_short = self.order_exist(key, 2)
            exist_long = self.order_exist(key, 1)
            if exist_long:
                buff_str += key + ": " + str(
                    self.symbol_gain[key] + (latest_prices[exist_long.get_symbol()] * exist_long.get_quantity()) - (
                                exist_long.get_price() * exist_long.get_quantity())) + ", "
            elif exist_short:
                buff_str += key + ": " + str(self.symbol_gain[key] + (exist_short.get_price() * exist_short.get_quantity()) - (
                            latest_prices[exist_short.get_symbol()] * exist_short.get_quantity())) + ", "
            else:
                buff_str += key + ": " + str(self.symbol_gain[key]) + ", "

        return buff_str + "}"

    def to_str(self):
        buff_str = "="*42+'\n'
        buff_str += datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')+'\n'
        buff_str += "== Wallet : "+self.get_name()+'\n'
        buff_str += "== Total Profit : $"+str(self.get_current_profit())+'\n'
        buff_str += "== Assets quantities"+'\n'
        buff_str += self.quantities_to_str()+'\n'
        buff_str += "== Closed order profits"+'\n'
        buff_str += str(self.symbol_gain)+'\n'
        buff_str += "== Opened order profits"+'\n'
        buff_str += self.opened_symbol_profit()+'\n'
        buff_str += "== Cumulated profits"+'\n'
        buff_str += self.overall_symbol_profit()+'\n'

        return buff_str


def main_spot():
    logging.basicConfig(filename="outputs/logs/debug.log", level=logging.DEBUG, filemode="w",
                        format="%(asctime)s [%(name)s] : %(message)s")

    name = "test_spot_wallet"
    wallet_dict = {"USD": 0.0}
    symbol_listing = ["XTZBNB", "MKRBTC", "LINKETH", "SHIBUSDT"]
    base_symbol = "USD"
    future = False
    wallet_demo = Wallet(name, wallet_dict, symbol_listing, base_symbol, future)

    wallet_demo.push_order(symbol_listing[0], 2, 0.5, take_profit=None, stop_loss=None)
    wallet_demo.push_order(symbol_listing[1], 2, 1.0, take_profit=None, stop_loss=None)
    wallet_demo.push_order(symbol_listing[2], 1, 1.5, take_profit=20, stop_loss=1, tpsl_percent=True)

    logger.debug(wallet_demo.get_name())
    logger.debug(wallet_demo.get_base_balance())
    logger.debug(wallet_demo.get_inactives())
    logger.debug(wallet_demo.get_actives())
    logger.debug(wallet_demo.get_value("USD"))
    logger.debug(wallet_demo.get_quantity(symbol_listing[0]))
    logger.debug(wallet_demo.get_current_profit())
    logger.debug(wallet_demo.wallet_to_str())
    logger.debug(wallet_demo.quantities_to_str())
    logger.debug(wallet_demo.profit_to_str())

    wallet_demo.check_take_profit_stop_loss()
    wallet_demo.exit_order(symbol_listing[0])
    wallet_demo.exit_order(symbol_listing[1])
    wallet_demo.exit_order(symbol_listing[2])

    logger.debug(wallet_demo.to_str())
    logger.debug("End of the <<Wallet>> tests.")


def main():
    logging.basicConfig(filename="outputs/logs/debug.log", level=logging.DEBUG, filemode="w", format="%(asctime)s [%(name)s] : %(message)s")

    name = "test_wallet"
    wallet_dict = {"USD": 0.0}
    symbol_listing = ["BTCUSDT", "ATOMUSDT", "BNBUSDT", "COMPUSDT", "STORJUSDT"]
    base_symbol = "USD"
    future = True
    wallet_demo = Wallet(name, wallet_dict, symbol_listing, base_symbol, future)

    wallet_demo.push_order(symbol_listing[0], 2, 100.0, take_profit=None, stop_loss=None)
    wallet_demo.push_order(symbol_listing[0], 2, 100.0, take_profit=None, stop_loss=None)
    wallet_demo.push_order(symbol_listing[0], 1, 200.0, take_profit=20, stop_loss=1, tpsl_percent=True)

    logger.debug(wallet_demo.get_name())
    logger.debug(wallet_demo.get_base_balance())
    logger.debug(wallet_demo.get_inactives())
    logger.debug(wallet_demo.get_actives())
    logger.debug(wallet_demo.get_value("USD"))
    logger.debug(wallet_demo.get_quantity(symbol_listing[0]))

    logger.debug(wallet_demo.get_current_profit())
    logger.debug(wallet_demo.wallet_to_str())
    logger.debug(wallet_demo.quantities_to_str())
    logger.debug(wallet_demo.profit_to_str())

    wallet_demo.check_take_profit_stop_loss()
    wallet_demo.exit_order("BTCUSDT")

    logger.debug(wallet_demo.to_str())
    logger.debug("End of the <<Wallet>> tests.")


if __name__ == '__main__':
    main_spot()
