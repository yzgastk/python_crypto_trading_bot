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
import requests
import datetime
import pandas as pd

import logging
logger = logging.getLogger(__name__)


class Klines:
	query_weight_limit = 1100
	kline_column_names = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_asset_volume", "trade_number", "tb_base_av", "tb_quote_av"]
	max_klines = 1000

	def __init__(self, symbol, interval, start_time=None, end_time=None, limit=500, futures=True, keep_last=False, heikinashi=False):
		self.symbol = symbol
		self.interval = interval
		self.futures = futures
		self.keep_last = keep_last
		self.heikinashi = heikinashi

		self.kline_frame = self.dl_klines(start_time=start_time, end_time=end_time, limit=limit)

		if not self.keep_last:
			self.kline_frame.drop(self.kline_frame.tail(1).index, inplace=True)

		if self.heikinashi:
			self.heikin_ashi_frame = self.compute_heikin_ashi(self.kline_frame)

		logger.debug("Klines object created for symbol "+self.symbol)

	def dl_klines(self, start_time=None, end_time=None, limit=500):
		if self.futures:
			url = "https://fapi.binance.com/fapi/v1/klines?symbol="+self.symbol+"&interval="+self.interval
		else:
			url = "https://api.binance.com/api/v3/klines?symbol="+self.symbol+"&interval="+self.interval

		if start_time:
			url += "&startTime="+str(start_time)
		if end_time:
			url += "&endTime="+str(end_time)

		if start_time and end_time:
			r_json = requests.get(url)
		else:
			r_json = requests.get(url+"&limit="+str(limit))

		if int(r_json.headers['X-MBX-USED-WEIGHT-1M']) > Klines.query_weight_limit:
			sys.exit("API usage reaching limits, shutting down the bot...")

		if r_json.status_code == 429 or r_json.status_code == 418:
			sys.exit("Weight limit of the API excedeed with code"+str(r_json.status_code))

		if r_json.status_code != 200:
			sys.exit("Exiting because of unhandled status code from http header:"+str(r_json.status_code))

		clean_df = pd.read_json(r_json.content)
		# Remove the last column as it is marked as "ignore" in API doc
		clean_df.drop(clean_df.columns[-1], axis=1, inplace=True)
		clean_df.columns = Klines.kline_column_names
		clean_df.set_index(Klines.kline_column_names[0], inplace=True)

		return clean_df

	def update_klines(self):
		if self.keep_last:
			new_klines = self.dl_klines(start_time=self.kline_frame.tail(1).index[0], limit=Klines.max_klines)
			self.kline_frame.drop(self.kline_frame.tail(1).index, inplace=True)
			self.kline_frame = pd.concat([self.kline_frame, new_klines])
		else:
			new_klines = self.dl_klines(start_time=self.kline_frame.tail(1).index[0] + 1, limit=Klines.max_klines)
			self.kline_frame = pd.concat([self.kline_frame, new_klines])
			self.kline_frame.drop(self.kline_frame.tail(1).index, inplace=True)

		if self.heikinashi:
			self.heikin_ashi_frame = self.compute_heikin_ashi(self.kline_frame)

		return

	def get_kline_frame(self):
		return self.kline_frame

	def get_heikin_ashi(self):
		return self.heikin_ashi_frame

	@staticmethod
	def compute_heikin_ashi(df):
		ha = pd.DataFrame()
		ha['ha_close'] = (df.open + df.high + df.low + df.close) / 4
		ha_open = [(df.open.iloc[0] + df.close.iloc[0]) / 2]
		[ha_open.append((ha_open[i] + ha.ha_close.values[i]) / 2) for i in range(0, len(df) - 1)]
		ha['ha_open'] = ha_open
		ha['ha_high'] = pd.merge(ha[['ha_open', 'ha_close']], df.high, how='inner', left_index=True, right_index=True).max()
		ha['ha_low'] = pd.merge(ha[['ha_open', 'ha_close']], df.low, how='inner', left_index=True, right_index=True).min()

		return ha

	@staticmethod
	def timestamp_to_binance(timestamp):
		dt_obj = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S,%f')
		return dt_obj.timestamp() * 1000


def main():
	logging.basicConfig(filename="./outputs/logs/debug.log", level=logging.DEBUG, filemode="w",
						format="%(asctime)s [%(name)s] : %(message)s")

	symbol1 = "BTCUSDT"
	interval1 = "1h"
	start_time1 = Klines.timestamp_to_binance("2021-01-01 00:00:00,00")
	end_time1 = Klines.timestamp_to_binance(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f'))
	symbol_data1 = Klines(symbol1, interval1, start_time=start_time1, end_time=end_time1, limit=300, futures=False,
								keep_last=True, heikinashi=True)

	symbol2 = "ETHUSDT"
	interval2 = "1d"
	symbol_data2 = Klines(symbol2, interval2, start_time=None, end_time=None, limit=500, futures=True,
								keep_last=False, heikinashi=False)

	logger.debug(symbol_data1.get_kline_frame().head())
	logger.debug(symbol_data2.get_kline_frame().head())
	print("End of the <<Klines>> test phase.")


if __name__ == '__main__':
	main()
