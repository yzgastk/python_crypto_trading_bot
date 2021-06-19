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

import talib
import pandas as pd
import logging
logger = logging.getLogger(__name__)


def cross_up(penu_line1, line1, penu_line2, line2):
    if (penu_line1 < penu_line2) and (line1 > line2):
        return True
    else:
        return False


def cross_down(penu_line1, line1, penu_line2, line2):
    if (penu_line1 > penu_line2) and (line1 < line2):
        return True
    else:
        return False


def get_macd(x, fastperiod=12, slowperiod=26, signalperiod=9):
    return talib.MACD(x, fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)


def get_rsi(x, timeperiod=60):
    return talib.RSI(x, timeperiod=timeperiod)


def get_sar(high, low, acceleration=0, maximum=0):
    return talib.SAR(high, low, acceleration=acceleration, maximum=maximum)


def get_sma(close, timeperiod=30):
    return talib.SMA(close, timeperiod=timeperiod)


def get_wma(close, timeperiod=30):
    return talib.WMA(close, timeperiod=timeperiod)


# Ichimoku Kinko Hyo
def get_tenkan_sen(kline_frame):
    period9_high = kline_frame.high.rolling(window=9).max()
    period9_low = kline_frame.low.rolling(window=9).min()
    return (period9_high + period9_low) / 2


def get_kijun_sen(kline_frame):
    period26_high = kline_frame.high.rolling(window=26).max()
    period26_low = kline_frame.low.rolling(window=26).min()
    return (period26_high + period26_low) / 2


def get_senkou_span_a(tenkan_sen, kijun_sen):
    return ((tenkan_sen + kijun_sen) / 2).shift(26)


def get_senkou_span_b(kline_frame):
    period52_high = kline_frame.high.rolling(window=52).max()
    period52_low = kline_frame.low.rolling(window=52).min()
    return ((period52_high + period52_low) / 2).shift(26)


def get_chikou_span(kline_frame):
    return kline_frame.close.shift(-26)


def ichimoku_cloud(kline_frame):
    ichi_frame = pd.DataFrame()
    ichi_frame['tenkan_sen'] = get_tenkan_sen(kline_frame)
    ichi_frame['kijun_sen'] = get_kijun_sen(kline_frame)
    ichi_frame['senkou_span_a'] = get_senkou_span_a(ichi_frame['tenkan_sen'], ichi_frame['kijun_sen'])
    ichi_frame['senkou_span_b'] = get_senkou_span_b(kline_frame)
    ichi_frame['chikou_span'] = get_chikou_span(kline_frame)

    return ichi_frame


def main():
    import Klines

    logging.basicConfig(filename="./outputs/logs/debug.log", level=logging.DEBUG, filemode="w",
                        format="%(asctime)s [%(name)s] : %(message)s")

    kline_frame = Klines.Klines("BTCUSDT", "1h", futures=True, keep_last=True)
    ichi_cloud = ichimoku_cloud(kline_frame.get_kline_frame())
    logger.debug(ichi_cloud.head())

    print("End of the <<indicator>> tests.\n")


if __name__ == '__main__':
    main()
