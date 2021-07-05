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

import sys
import csv
import time
import datetime

from argparse import ArgumentParser

import Klines
import Wallets
import WalletManager
import statistics
import strategies as strat

import logging

logger = logging.getLogger(__name__)


def main():
    print("python_trading_bot  Copyright (C) 2021  Olivier DECOURBE \n\
    This program comes with ABSOLUTELY NO WARRANTY. \n\
    This is free software, and you are welcome to redistribute it \n\
    under certain conditions; type `python3 main.py --warranty' or `python3 main.py -w` for details.")

    timeframe_to_sec = {"1m": 60, "3m": 180, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "2h": 7200, "4h": 14400,
                        "6h": 21600, "8h": 28800, "12h": 43200, "1d": 86400, "3d": 259200, "1w": 604800, "1M": 2419200}

    now = datetime.datetime.now()
    logging.basicConfig(filename="./outputs/logs/trading_bot_" + now.strftime("%Y%m%d_%H%M%S") + ".log",
                        level=logging.DEBUG,
                        filemode="w",
                        format="%(asctime)s [%(name)s] : %(message)s")

    parser = ArgumentParser()
    parser.add_argument("-t", "--timeframe", dest="timeframe", default="15m", help="The chosen timeframe as given on "
                                                                                   "binance (1m, 3m, 1h,...).")
    parser.add_argument("-u", "--runUntil", type=datetime.datetime.fromisoformat, dest="stop_date",
                        default=datetime.datetime.now() + datetime.timedelta(days=1),
                        help="Date at which the script stops. Formatted as YYYY-MM-DD.HH:mm:ss")
    parser.add_argument("-s", "--symbols", dest="symbol_file", default="./symbol_list.csv",
                        help="Path to the .csv that contains symbols")
    parser.add_argument("-w", "--warranty", dest="license_info", nargs='?', const=True, default=False,
                        help="Display licencing extended information.")
    args = parser.parse_args()

    if args.license_info:
        with open("./gpl-3-license.md", ) as gplv3license:
            print(gplv3license.read())
        sys.exit("End Of license terms.")

    kline_dict = {}

    with open(args.symbol_file) as symbol_file:
        reader = csv.reader(symbol_file)
        symbols_raw = list(reader)[0]
        symbols = [i.upper() for i in symbols_raw]

    # Interval at which stop_loss will be checked
    stop_loss_interval = timeframe_to_sec["1m"]

    # Defining a wallet manager that will track the different wallets
    wallet_manager = WalletManager.WalletManager()

    # Retrieving history of klines for each symbol to track
    for symbol in symbols:
        logger.debug("Fetching " + symbol)
        kline_dict[symbol] = Klines.Klines(symbol, args.timeframe, futures=False, keep_last=True, heikinashi=True)
        kline_dict[symbol].update_klines()

    # Creating a wallet that will handle orders and keep track of profit and loss
    paper_wallet = Wallets.Wallet("paper_wallet" + args.timeframe, {"USD": 0.0}, symbols, "USD", futures=True)
    wallet_manager.add_wallet(paper_wallet)

    logger.debug("Starting trading bot core loop")

    # Main loop that will check strategies and update klines
    while datetime.datetime.now() < args.stop_date:
        # Updating klines for each symbols
        for symbol in symbols:
            logger.debug("Processing " + symbol)
            kline_dict[symbol].update_klines()

            # Applying strategeis
            strat.discord_strat_01(symbol, paper_wallet, kline_frame.close[-1], 30000.0, 35000.0, 100.0)

        time_delta = timeframe_to_sec[args.timeframe] - (
                    int(datetime.datetime.now().strftime('%s')) % timeframe_to_sec[args.timeframe])

        print(paper_wallet.to_str())
        # Take profit / Stop loss loop running until the next update
        while time_delta > stop_loss_interval:
            paper_wallet.check_take_profit_stop_loss()
            time_delta -= stop_loss_interval
            time.sleep(stop_loss_interval)

        # Assuming computation overhead will enforce the new kline has been opened
        time.sleep(time_delta)

    logger.info("Waiting for the next candle to open.")


if __name__ == '__main__':
    main()
