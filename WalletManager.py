#!/usr/bin/python3.8
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

import logging
logger = logging.getLogger(__name__)


class WalletManager:

    def __init__(self):
        self.wallets = []

    def add_wallet(self, wallet):
        self.wallets.append(wallet)

    def remove_wallet(self, wallet_ref=None, name=None):
        if name:
            for wallet in self.wallets:
                if wallet.get_name() == name:
                    self.wallets.remove(wallet)
        elif wallet_ref:
            self.wallets.remove(wallet_ref)
        else:
            logger.debug("No wallet to remove, specify wallet object or wallet name.")

    def to_str(self):
        buff_str = ""
        for wallet in self.wallets:
            buff_str += wallet.to_str()+'\n'
        return buff_str


def main():
    import Wallets
    import time
    logging.basicConfig(filename="./outputs/logs/debug.log", level=logging.DEBUG, filemode="w",
                        format="%(asctime)s [%(name)s] : %(message)s")

    name1 = "test_wallet"
    wallet_dict1 = {"USD": 0.0}
    symbol_listing1 = ["LINABTC", "TRXBTC", "BNBBTC", "COMPUSDT", "STORJUSDT"]
    base_symbol1 = "USD"
    future1 = False
    wallet1 = Wallets.Wallet(name1, wallet_dict1, symbol_listing1, base_symbol1, future1)
    for symbol in symbol_listing1:
        wallet1.push_order(symbol, 1, 200.0)
    time.sleep(60)
    wallet1.exit_all_orders()
    wallet1.push_order(symbol_listing1[0], 1, 200.0)
    wallet1.push_order(symbol_listing1[1], 2, 200.0)
    wallet1.push_order(symbol_listing1[3], 2, 200.0)

    name2 = "test_wallet2"
    wallet_dict2 = {"USD": 0.0}
    symbol_listing2 = ["XLMUSDT", "ENJUSDT", "MKRUSDT", "ETHUSDT", "BTCUSDT"]
    base_symbol2 = "USD"
    future2 = True
    wallet2 = Wallets.Wallet(name2, wallet_dict2, symbol_listing2, base_symbol2, future2)
    for symbol in symbol_listing2:
        wallet2.push_order(symbol, 1, 200.0)
    time.sleep(60)
    wallet2.exit_all_orders()
    wallet2.push_order(symbol_listing2[4], 1, 200.0)
    wallet2.push_order(symbol_listing2[2], 2, 200.0)
    wallet2.push_order(symbol_listing2[1], 2, 200.0)

    wallet_manager = WalletManager()
    wallet_manager.add_wallet(wallet1)
    wallet_manager.add_wallet(wallet2)

    logger.debug(wallet_manager.to_str())

    return


if __name__ == '__main__':
    main()
