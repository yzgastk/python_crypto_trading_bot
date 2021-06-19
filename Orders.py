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

import numpy as np
from datetime import datetime

import logging
logger = logging.getLogger(__name__)


class Orders:
	LONG = 1
	SHORT = 2

	def __init__(self, symbol, order_type, price, quantity, take_profit=None, stop_loss=None, tpsl_percent=False):
		self.symbol = symbol
		self.order_type = order_type
		self.price = price
		self.quantity = quantity
		self.timestamp = datetime.now()
		self.active = True

		if tpsl_percent:
			self.take_profit = Orders.get_percent_tpsl(self.order_type, 1, self.price, take_profit)
			self.stop_loss = Orders.get_percent_tpsl(self.order_type, 2, self.price, stop_loss)
		else:
			self.take_profit = take_profit
			self.stop_loss = stop_loss

		if self.order_type == Orders.LONG:
			odr = "long"
			if not self.take_profit:
				self.take_profit = np.inf
			if not self.stop_loss:
				self.stop_loss = -np.inf
		else:
			odr = "short"
			if not self.take_profit:
				self.take_profit = -np.inf
			if not self.stop_loss:
				self.stop_loss = np.inf

		logger.info("New "+odr+" order created for "+self.symbol+" : "+str(self.quantity)+" @ "+str(self.price))
		logger.debug(self.to_str())

	@staticmethod
	def get_percent_tpsl(order_type, side, base_price, coefficient):
		if (order_type == Orders.LONG and side == 1) or (order_type == Orders.SHORT and side == 2):
			return base_price + base_price * coefficient / 100
		elif (order_type == Orders.LONG and side == 2) or (order_type == Orders.SHORT and side == 1):
			return base_price - base_price * coefficient / 100

	def set_active(self, active):
		self.active = active

	def set_take_profit(self, take_profit):
		self.take_profit = take_profit

	def set_stop_loss(self, stop_loss):
		self.stop_loss = stop_loss

	def get_symbol(self):
		return self.symbol

	def get_order_type(self):
		return self.order_type

	def get_price(self):
		return self.price

	def get_quantity(self):
		return self.quantity

	def get_timestamp(self):
		return self.timestamp

	def get_active(self):
		return self.active

	def get_take_profit(self):
		return self.take_profit

	def get_stop_loss(self):
		return self.stop_loss

	def to_str(self):
		return self.get_symbol()+":"+str(self.get_order_type())+":"+str(self.get_price())+":"+str(self.get_quantity())+":"+str(self.get_timestamp())+":"+str(self.get_active())+":"+str(self.get_take_profit())+":"+str(self.get_stop_loss())


def main():
	logging.basicConfig(filename="./outputs/logs/debug.log", level=logging.DEBUG, filemode="w",
						format="%(asctime)s [%(name)s] : %(message)s")

	order1 = Orders('BTCUSDT', Orders.SHORT, 40000, 0.01)
	order2 = Orders('ENJUSDT', Orders.LONG, 10, 20, take_profit=20, stop_loss=2, tpsl_percent=True)
	order3 = Orders('ETHUSDT', Orders.LONG, 1500, 0.5, take_profit=1650, stop_loss=1450)

	logger.debug(order1.to_str())
	o1_price = order1.get_price()
	order1.set_take_profit(Orders.get_percent_tpsl(Orders.SHORT, 1, o1_price, 50))
	order1.set_stop_loss(Orders.get_percent_tpsl(Orders.SHORT, 2, o1_price, 5))
	logger.debug(order1.to_str())

	logger.debug(order2.to_str())
	order2.set_active(False)
	logger.debug(order2.to_str())

	logger.debug(order3.to_str())
	logger.debug("End of the <<Orders>> test phase.")
	return


if __name__ == '__main__':
	main()
