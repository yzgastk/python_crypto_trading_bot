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

import pandas as pd
import talib

import indicators as ind
import Orders

import logging
logger = logging.getLogger(__name__)


def golden_cross(symbol, klines, wallet, ma_type="wma", fast_ma=50, slow_ma=200, amount=1000.0):
    if ma_type == "wma":
        ma_50 = ind.get_wma(klines.close, timeperiod=fast_ma)
        ma_200 = ind.get_wma(klines.close, timeperiod=slow_ma)
    else:
        ma_50 = ind.get_sma(klines.close, timeperiod=fast_ma)
        ma_200 = ind.get_sma(klines.close, timeperiod=slow_ma)

    if ind.cross_up(ma_50.iloc[-2], ma_50.iloc[-1], ma_200.iloc[-2], ma_200.iloc[-1]):
        logger.debug("Cross-up happened !")
        wallet.push_order(symbol, Orders.Orders.LONG, amount)
    elif ind.cross_down(ma_50.iloc[-2], ma_50.iloc[-1], ma_200.iloc[-2], ma_200.iloc[-1]):
        logger.debug("Cross-down happened !")
        wallet.push_order(symbol, Orders.Orders.SHORT, amount)

    return


def sar_strategy(symbol, klines, wallet, amount=1000.0):
    sar = ind.get_sar(klines.high, klines.low, acceleration=0.02, maximum=0.2)

    if sar.iloc[-1] >= klines.high.iloc[-1] and sar.iloc[-2] <= klines.low.iloc[-2]:
        wallet.push_order(symbol, Orders.Orders.SHORT, amount)
    elif sar.iloc[-1] <= klines.low.iloc[-1] and sar.iloc[-2] >= klines.high.iloc[-2]:
        wallet.push_order(symbol, Orders.Orders.LONG, amount)

    return


def moving_atr_stop_loss(kline_frame, order, current_price, atr_length=14, atr_multiplier=1.2):
    atr = (talib.ATR(kline_frame.high, kline_frame.low, kline_frame.close, timeperiod=atr_length).iloc[-1] * atr_multiplier)

    if order.get_order_type() == Orders.Orders.LONG:
        new_stop_loss = current_price - atr
        if not order.stop_loss or new_stop_loss > order.stop_loss:
            order.stop_loss = new_stop_loss
    elif order.get_order_type() == Orders.Orders.SHORT:
        new_stop_loss = current_price + atr
        if not order.stop_loss or new_stop_loss < order.stop_loss:
            order.stop_loss = new_stop_loss

    return


	def discord_strat_01(symbol, wallet, current_price, buy_limit, sell_limit, amount=100):
		if current_price <= buy_limit:
			wallet.push_order(symbol, Orders.Orders.LONG, amount)
		elif current_price >= sell_limit:
			waller.exit_order(symbol)

		return


def main():
    import Klines as Kl
    import Wallets

    logging.basicConfig(filename="./outputs/logs/debug.log", level=logging.DEBUG, filemode="w",
                        format="%(asctime)s [%(name)s] : %(message)s")

    symbol = "LINKUSDT"
    interval = "1h"
    start_time = int(Kl.Klines.timestamp_to_binance("2021-05-07 01:00:00,00"))
    end_time = int(Kl.Klines.timestamp_to_binance("2021-05-08 09:00:00,00"))
    historic_data = Kl.Klines(symbol, interval, limit=300,  end_time=end_time, futures=True, keep_last=True).get_kline_frame()
    data = Kl.Klines(symbol, interval, start_time=start_time,  end_time=end_time, futures=True, keep_last=True).get_kline_frame()

    replay_buffer = pd.DataFrame()
    replay_buffer = replay_buffer.append(data.iloc[0])
    replay_buffer = replay_buffer.append(data.iloc[1])

    wallet = Wallets.Wallet("strategy_testing", {"USD": 0.0}, [symbol], "USD", True)

    for i in range(data.shape[0] - 2):
        sar_strategy(symbol, replay_buffer, wallet, 2000.0)
        golden_cross(symbol, historic_data.loc[:replay_buffer.index.max()], wallet, ma_type="wma")

        order = wallet.get_order_by_symbol(symbol)
        current_price = replay_buffer.open.iloc[-1]

        if order:
            moving_atr_stop_loss(historic_data.loc[:replay_buffer.index.max()], order, current_price, atr_length=14, atr_multiplier=1.2)

        replay_buffer = replay_buffer.append(data.iloc[i+2])

    logger.debug("End of the <Statistics> tests.\n")


if __name__ == '__main__':
    main()
