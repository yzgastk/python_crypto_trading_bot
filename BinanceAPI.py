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

import time
import hmac
import hashlib
import requests
import pandas as pd

import logging
logger = logging.getLogger(__name__)

# /!\ Warning /!\
# - This module should be considered has an alpha and you should not expect it to work properly.
# - Functionalities are limited to very basic order push
# - For example, in case a request fail, there is no backup or safety net, the script will stop by throwing an exception
#   or continue to run ignoring the failed order.

class BinanceAPI:
    base_endpoint = "https://api.binance.com/api/v3/"
    signed_endpoint = "https://api.binance.com/sapi/v1/futures/transfer/"
    future_endpoint = "https://fapi.binance.com/fapi/v1/"

    def __init__(self, default_endpoint="futures", hedge_mode="True"):
        self.public_key = "put_your_binanceapi_public_key_here"
        self.private_key = "put_your_binanceapi_private_key_here"

        self.recv_window = 3000
        self.default_endpoint = default_endpoint
        self.hedge_mode = hedge_mode
        self.set_default_endpoint(new_endpoint=self.default_endpoint)

    def to_str(self):
        str_buff = "Public Key : "+self.public_key+'\n'
        str_buff += "Private Key : "+self.private_key+'\n'
        str_buff += "Receive Window : "+str(self.recv_window)+'\n'
        str_buff += "Default Endpoint : "+self.default_endpoint+'\n'
        str_buff += "Hedge Mode : "+self.hedge_mode+'\n'

        return str_buff

    def set_hedge_mode(self, new_mode):
        self.hedge_mode = new_mode

    def set_default_endpoint(self, new_endpoint="futures"):
        self.default_endpoint = new_endpoint
        if self.default_endpoint == "futures":
            self.endpoint = BinanceAPI.future_endpoint
        else:
            self.endpoint = BinanceAPI.base_endpoint

    @staticmethod
    def error_handler(r_json):
        if r_json.status_code != 200:
            return True
        return False

    def buy_order_limit(self):
        return

    def buy_order_market(self, symbol, quote_order_qty):
        base_request = self.endpoint + "order"
        timestamp = int(round(time.time() * 1000))
        if self.default_endpoint != "futures":
            query_string = "symbol=" + symbol + "&side=BUY&type=MARKET&quoteOrderQty=" + str(
            quote_order_qty) + "&newOrderRespType=FULL&recvWindow=" + str(self.recv_window) + "&timestamp=" + str(
            timestamp)
        else:
            if self.hedge_mode:
                query_string = "symbol=" + symbol + "&side=BUY&type=MARKET&quantity=" + str(
                    quote_order_qty) + "&newOrderRespType=FULL&recvWindow=" + str(
                    self.recv_window) + "&positionSide=LONG" + "&timestamp=" + str(timestamp)
            else:
                query_string = "symbol=" + symbol + "&side=BUY&type=MARKET&quantity=" + str(
                    quote_order_qty) + "&newOrderRespType=FULL&recvWindow=" + str(
                    self.recv_window) + "&timestamp=" + str(timestamp)

        hmac_base_request = hmac.new(bytes(self.private_key, 'utf-8'), query_string.encode('utf-8'), hashlib.sha256)
        r = requests.post(url=base_request + "?" + query_string + "&signature=" + hmac_base_request.hexdigest(),
                          headers={'X-MBX-APIKEY': self.public_key, })
        r_json = r.json()
        if not self.error_handler(r):
            return pd.json_normalize(r_json)
        else:
            logger.error(r)
            return r

    def sell_order_limit(self):
        return

    def sell_order_market(self, symbol, quote_order_qty):
        base_request = self.endpoint + "order"
        timestamp = int(round(time.time() * 1000))

        if self.default_endpoint != "futures":
            query_string = "symbol=" + symbol + "&side=SELL&type=MARKET&quantity=" + str(
                quote_order_qty) + "&newOrderRespType=FULL&recvWindow=" + str(self.recv_window) + "&timestamp=" + str(
                timestamp)
        else:
            if self.hedge_mode:
                query_string = "symbol=" + symbol + "&side=SELL&type=MARKET&quantity=" + str(
                    quote_order_qty) + "&newOrderRespType=FULL&recvWindow=" + str(
                    self.recv_window) + "&positionSide=SHORT" + "&timestamp=" + str(timestamp)
            else:
                query_string = ""

        hmac_base_request = hmac.new(bytes(self.private_key, 'utf-8'), query_string.encode('utf-8'), hashlib.sha256)
        r = requests.post(url=base_request + "?" + query_string + "&signature=" + hmac_base_request.hexdigest(),
                          headers={'X-MBX-APIKEY': self.public_key, })
        r_json = r.json()

        if not self.error_handler(r):
            return pd.json_normalize(r_json)
        else:
            return r


def main():
    binance_handler = BinanceAPI(default_endpoint="futures")
    print(binance_handler.to_str())
    # binance_handler.buy_order_market("ALGOUSDT", 20)
    # binance_handler.sell_order_market("DOTUSDT", 0.5)
    # binance_handler.set_default_endpoint(new_endpoint="basic")
    # binance_handler.buy_order_market("ATABTC", 0.00015)
    # binance_handler.sell_order_market("ATABTC", 4)
    print("End of the <BinanceAPI> test phase.")
    return


if __name__ == '__main__':
    main()

