import asyncio
import base64
import hashlib
import hmac
import json
import time

import aiohttp
from src.client import Client, Ticker, Wallet, OpenOrder


class FetchException(Exception):
    pass


class BinanceClient(Client):

    def __init__(self, API_KEY, API_SECRET, host="https://api.binance.com"):
        self.API_KEY = API_KEY
        self.API_SECRET = API_SECRET
        self.host = host

    async def post(self, endpoint, params=""):
        """
        :param endpoint:
        :param params:
        :return:
        """
        signature = self.signature_payload(params)
        if params.strip() == "":
            params = "?{}signature={}".format(params, signature)
        else:
            params = "?{}&signature={}".format(params, signature)
        url = '{}/{}{}'.format(self.host, endpoint, params)
        headers = self.generate_headers()
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as resp:
                text = await resp.text()
                if resp.status < 200 or resp.status > 299:
                    raise FetchException('POST {} failed with status {} - {}'
                                         .format(url, resp.status, text))
                parsed = json.loads(text, parse_float=float)
                return parsed

    async def fetch(self, endpoint, params="", is_public=False):
        """
        :param endpoint:
        :param params:
        :param is_public:
        :return:
        """
        signature = self.signature_payload(params)
        if is_public:
            params = f"?{params}"
        elif params.strip() == "":
            params = "?{}signature={}".format(params, signature)
        else:
            params = "?{}&signature={}".format(params, signature)

        url = '{}/{}{}'.format(self.host, endpoint, params)
        headers = self.generate_headers()
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                text = await resp.text()
                if resp.status != 200:
                    raise FetchException('GET {} failed with status {} - {}'
                                         .format(url, resp.status, text))
                parsed = json.loads(text, parse_float=float)
                return parsed

    def signature_payload(self, data):
        signature = hmac.new(self.API_SECRET.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest()
        return signature

    def generate_headers(self):
        return {
            'X-MBX-APIKEY': '{}'.format(self.API_KEY)
        }

    async def order_book(self, market):
        """Get the Order Book for the market
        https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#order-book
        :param symbol: required
        :type symbol: str
        :param limit:  Default 100; max 1000
        :type limit: int
        :returns: API response
        .. code-block:: python
            {
                "lastUpdateId": 1027024,
                "bids": [
                    [
                        "4.00000000",     # PRICE
                        "431.00000000",   # QTY
                        []                # Can be ignored
                    ]
                ],
                "asks": [
                    [
                        "4.00000200",
                        "12.00000000",
                        []
                    ]
                ]
            }
        :raises: BinanceRequestException, BinanceAPIException
        """
        order_books = None
        try:
            request = "/api/v3/depth"
            paydata = "symbol={}".format(market)
            order_books = await self.fetch(endpoint=request, params=paydata)
            return order_books
        except FetchException as e:
            print(e)
            return None
        except Exception as e:
            print(e)
            return None

    def order_book_synchronized(self, market):
        try:
            t = asyncio.ensure_future(self.get_ticker(market))
            order_book = asyncio.get_event_loop().run_until_complete(t)
            return order_book
        except Exception as e:
            print(e)
            return None

    async def get_wallet(self, symbol):
        try:
            request = 'api/v3/account'
            nonce = str(int(time.time() * 1000))
            paydata = "timestamp={}".format(nonce)
            wallet = await self.fetch(endpoint=request, params=paydata)
            balance = 0.0
            for wallet in wallet["balances"]:
                if wallet["asset"] == symbol:
                    balance = wallet["free"]
            return Wallet(available=str(balance))
        except FetchException as e:
            print(e)
            return None
        except Exception as e:
            print(e)
            return None

    def get_wallets_synchronized(self, market):
        try:
            t = asyncio.ensure_future(self.get_wallet(market))
            wallets = asyncio.get_event_loop().run_until_complete(t)
            return wallets
        except Exception as e:
            print(e)
            return None

    async def get_open_orders(self, symbol):
        try:
            request = "api/v3/openOrders"
            nonce = str(int(time.time() * 1000))
            paydata = [
                f"symbol={symbol}",
                f"timestamp={nonce}"
            ]
            orders = await self.fetch(endpoint=request, params=self.list_to_string(paydata))
            open_orders = []
            for order in orders:
                open_orders.append(
                    OpenOrder(
                        price=order["price"],
                        amount=order["origQty"],
                        side=order["side"],
                        order_id=order["orderId"]
                    )
                )
            return open_orders
        except FetchException as e:
            print(e)
            return None
        except Exception as e:
            print(e)
            return None

    async def get_ticker(self, paritet):
        try:
            request = 'api/v3/ticker/price'
            paydata = "symbol={}".format(paritet)
            ticker = await self.fetch(endpoint=request, params=paydata, is_public=True)
            return Ticker(last=ticker["price"], ask="", bid="")
        except FetchException as e:
            print(e)
            return None
        except Exception as e:
            print(e)
            return None

    def get_tickers_synchronized(self, symbol):
        try:
            t = asyncio.ensure_future(self.get_ticker(symbol))
            ticker = asyncio.get_event_loop().run_until_complete(t)
            return ticker
        except Exception as e:
            print(e)
            return None

    async def buy_order_market(self, market, amount):
        try:
            request = 'api/v3/order'
            nonce = str(int(time.time() * 1000))
            paydata = [
                "symbol={}".format(market),
                "side=BUY",
                "quantity={}".format(amount),
                "type={}".format("MARKET"),
                "timestamp={}".format(nonce)
            ]
            buy = await self.post(endpoint=request, params=self.list_to_string(paydata))
            return buy
        except FetchException as e:
            print(e)
            return None
        except Exception as e:
            print(e)
            return None

    async def sell_order_market(self, market, amount):
        try:
            request = 'api/v3/order'
            nonce = str(int(time.time() * 1000))
            paydata = [
                "symbol={}".format(market),
                "side=SELL",
                "quantity={}".format(amount),
                "type={}".format("MARKET"),
                "timestamp={}".format(nonce)
            ]
            return await self.post(endpoint=request, params=self.list_to_string(paydata))
        except FetchException as e:
            print(e)
            return None
        except Exception as e:
            print(e)
            return None

    async def buy_order_limit(self, paritet, price, amount):
        try:
            request = 'api/v3/order'
            nonce = str(int(time.time() * 1000))
            paydata = [
                "symbol={}".format(paritet),
                "side=BUY",
                "type={}".format("LIMIT"),
                "timeInForce=GTC",
                "quantity={}".format(amount),
                "price={}".format(round(price, 3)),
                "recvWindow=5000",
                "timestamp={}".format(nonce)
            ]
            buy = await self.post(endpoint=request, params=self.list_to_string(paydata))
            return buy
        except FetchException as e:
            print(e)
            return None
        except Exception as e:
            print(e)
            return None

    async def sell_order_limit(self, paritet, price, amount):
        try:
            request = 'api/v3/order'
            nonce = int(time.time() * 1000)
            paydata = [
                "symbol={}".format(paritet),
                "side=SELL",
                "quantity={}".format(amount),
                "timeInForce=GTC",
                "type={}".format("LIMIT"),
                "recvWindow=5000",
                "timestamp={}".format(nonce),
                "price={}".format(round(price, 3))
            ]
            return await self.post(endpoint=request, params=self.list_to_string(paydata))
        except FetchException as e:
            print(e)
            return None
        except Exception as e:
            print(e)
            return None

    def buy_order_market_synchronized(self, market, amount):
        try:
            t = asyncio.ensure_future(self.buy_order_market(market, amount))
            order = asyncio.get_event_loop().run_until_complete(t)
            return order
        except Exception as e:
            print(e)
            return None

    def sell_order_market_synchronized(self, market, amount):
        try:
            t = asyncio.ensure_future(self.sell_order_market(market, amount))
            order = asyncio.get_event_loop().run_until_complete(t)
            return order
        except Exception as e:
            print(e)
            return None

    @staticmethod
    def list_to_string(paydata):
        return "&".join(paydata)

    @staticmethod
    def dict_to_string(paydata):
        return "&".join([f"{key}={value}" for key, value in paydata.items()])

