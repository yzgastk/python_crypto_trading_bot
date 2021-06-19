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

import datetime
import seaborn as sn
import matplotlib.pyplot as plt
import matplotlib.dates as mpl_dates
from mpl_finance import candlestick_ohlc

import logging
logger = logging.getLogger(__name__)


def binance_to_timestamp(epoch_date):
    return datetime.datetime.fromtimestamp(float((str(epoch_date)[:-3])))


def get_heatmap(df):
    plt.clf()
    plt.figure(figsize=(20, 20))
    corr_matrix = df.corr()
    sn.heatmap(corr_matrix, annot=True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("./outputs/graphs/corMatrix-"+datetime.datetime.now().strftime('%s')+".svg")
    plt.close()


def plot_candlestick(symbol, klines, indicators_over={}, indicators={}, last_limit=100):
    # indicator_over : these indicators will be plot on the same graph as candlesticks
    # indicators : plot on separated graphs
    ohlc = klines.drop(['volume', 'close_time', 'quote_asset_volume', 'trade_number', 'tb_quote_av', 'tb_base_av'], axis=1)
    ohlc.reset_index(inplace=True)
    ohlc.rename(columns={"open_time": "Date"}, inplace=True)
    ohlc['Date'] = ohlc['Date'].apply(binance_to_timestamp).apply(mpl_dates.date2num)
    date_format = mpl_dates.DateFormatter('%d-%m-%Y')

    ind_number = len(indicators)+1
    fig, axs = plt.subplots(ind_number, 1, figsize=(12, 16))

    limiter = -last_limit
    if ind_number == 1:
        candlestick_ohlc(axs, ohlc.values[limiter:], width=0.6 / 24, colorup='green', colordown='red', alpha=0.8)
    else:
        candlestick_ohlc(axs[0], ohlc.values[limiter:], width=0.6 / 24, colorup='green', colordown='red', alpha=0.8)
        for name_o, ind_o in indicators_over.items():
            axs[0].plot(ohlc.Date[limiter:], ind_o[limiter:])

        axs[0].set_xlabel('Date')
        axs[0].set_ylabel('Price')
        axs[0].xaxis.set_major_formatter(date_format)

        i = 1
        for name, ind in indicators.items():
            axs[i].plot(ohlc.Date[limiter:], ind[limiter:], color='black')
            axs[i].set_xlabel('Date')
            axs[i].set_ylabel(name)
            axs[i].xaxis.set_major_formatter(date_format)
            i += 1

    fig.suptitle('Daily Chart for ' + symbol)

    fig.autofmt_xdate()

    try:
        fig.tight_layout()
        plt.savefig("./outputs/graphs/candlesticks-"+symbol+"-"+datetime.datetime.now().strftime('%s')+".svg", format="svg")
    except ValueError:
        print("Not enough data for : " + symbol)

    plt.clf()
    plt.cla()
    plt.close(fig)
    return


def main():
    import Klines
    import pandas
    import indicators

    logging.basicConfig(filename="./outputs/logs/debug.log", level=logging.DEBUG, filemode="w",
                        format="%(asctime)s [%(name)s] : %(message)s")

    kline_frame_btc = Klines.Klines("BTCUSDT", "1h", futures=True, keep_last=True)
    kline_frame_sol = Klines.Klines("SOLUSDT", "1h", futures=True, keep_last=True)
    kline_frame_xlm = Klines.Klines("XLMUSDT", "1h", futures=True, keep_last=True)
    kline_frame_bnb = Klines.Klines("BNBUSDT", "1h", futures=True, keep_last=True)
    kline_frame_doge = Klines.Klines("DOGEUSDT", "1h", futures=True, keep_last=True)
    kline_frame_comp = Klines.Klines("COMPUSDT", "1h", futures=True, keep_last=True)

    af_btc = kline_frame_btc.get_kline_frame().close.iloc[-10:]
    af_xlm = kline_frame_xlm.get_kline_frame().close.iloc[-10:]
    af_sol = kline_frame_sol.get_kline_frame().close.iloc[-10:]
    af_bnb = kline_frame_bnb.get_kline_frame().close.iloc[-10:]
    af_doge = kline_frame_doge.get_kline_frame().close.iloc[-10:]
    af_comp = kline_frame_comp.get_kline_frame().close.iloc[-10:]

    af_dict = {"BTCUSDT": af_btc, "SOLUSDT": af_sol, "XLMUSDT": af_xlm, "BNBUSDT": af_bnb, "DOGEUSDT": af_doge, "COMPUSDT": af_comp}
    aggregated_frame = pandas.concat(af_dict, axis=1)
    get_heatmap(aggregated_frame)

    ichi_cloud = indicators.ichimoku_cloud(kline_frame_doge.get_kline_frame())
    macd = indicators.get_macd(kline_frame_doge.get_kline_frame().close)
    rsi = indicators.get_rsi(kline_frame_doge.get_kline_frame().close)
    plot_candlestick("DOGEUSDT", kline_frame_doge.get_kline_frame(), indicators_over={'tenkan_sen': ichi_cloud['tenkan_sen'], 'kijun_sen': ichi_cloud['kijun_sen'], 'senkou_span_a': ichi_cloud['senkou_span_a'], 'senkou_span_b': ichi_cloud['senkou_span_b'], 'chikou_span': ichi_cloud['chikou_span']}, indicators={'macd': macd[0], 'rsi': rsi}, last_limit=100)

    print("End of the <<Statistics>> tests.\n")


if __name__ == '__main__':
    main()
