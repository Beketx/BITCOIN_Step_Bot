import asyncio
import base64
import hashlib
import hmac
import json
import time
import aiohttp
from src.client import Client, Wallet, Ticker


class FetchException(Exception):
    pass


class WhiteBitClient(Client):
    def __init__(self, API_KEY, API_SECRET, host="https://whitebit.com"):
        self.API_KEY = API_KEY
        self.API_SECRET = API_SECRET
        self.host = host  # last slash. Do not use https://whitebit.com/

    async def post(self, endpoint, data, params=""):
        """
        Send a pre-signed POST request to the whitebit api

        @return response
        """
        url = '{}/{}'.format(self.host, endpoint)
        headers, paydata = self.generate_headers(data)
        async with aiohttp.ClientSession() as session:
            async with session.post(url + params, headers=headers, data=paydata) as resp:
                text = await resp.text()
                if resp.status < 200 or resp.status > 299:
                    raise FetchException('POST {} failed with status {} - {}'
                                         .format(url, resp.status, text))
                parsed = json.loads(text, parse_float=float)
                return parsed

    async def fetch(self, endpoint, params=""):
        """
        Send a GET request to the whitebit api

        @return reponse
        """
        url = '{}/{}{}'.format(self.host, endpoint, params)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                text = await resp.text()
                if resp.status != 200:
                    raise FetchException('GET {} failed with status {} - {}'
                                         .format(url, resp.status, text))
                parsed = json.loads(text, parse_float=float)
                return parsed

    def signature_payload(self, data):
        data_json = json.dumps(data, separators=(',', ':'))  # use separators param for deleting spaces
        payload = base64.b64encode(data_json.encode('ascii'))
        signature = hmac.new(self.API_SECRET.encode('ascii'), payload, hashlib.sha512).hexdigest()
        return payload, signature, data_json

    def generate_headers(self, paydata):
        payload, signature, data_json = self.signature_payload(paydata)

        return {
            'Content-Type': 'application/json',
            'X-TXC-APIKEY': '{}'.format(self.API_KEY),
            'X-TXC-PAYLOAD': '{}'.format(payload.decode("ascii")),
            'X-TXC-SIGNATURE': '{}'.format(signature),
        }, data_json

    async def get_ticker(self, market):
        ticker = None
        try:
            ticker = await self.fetch("api/v1/public/ticker", "?market={}".format(market))
            return Ticker(bid=ticker["result"]['bid'], ask=ticker["result"]['ask'], last=ticker['result']['last'])
        except FetchException as e:
            print(e)
            return None
        except:
            print(ticker)
            return None

    def get_ticker_synchronized(self, market):
        try:
            t = asyncio.ensure_future(self.get_ticker(market))
            ticker = asyncio.get_event_loop().run_until_complete(t)
            return ticker
        except Exception as e:
            print(e)
            return None

    async def get_wallet(self, market):
        wallet = None
        try:
            request = 'api/v4/trade-account/balance'
            nonce = str(int(time.time()))
            paydata = {
                "ticker": market,
                "request": "/" + request,
                "nonce": nonce
            }
            wallet = await self.post(request, paydata)
            return Wallet(available=wallet["available"])
        except FetchException as e:
            print(e)
            return None
        except:
            print(wallet)
            return None

    def get_wallets_synchronized(self, market):
        try:
            t = asyncio.ensure_future(self.get_wallet(market))
            wallets = asyncio.get_event_loop().run_until_complete(t)
            return wallets
        except Exception as e:
            print(e)
            return None

    async def buy_order_market(self, market, amount):
        try:
            request = 'api/v4/order/market'
            nonce = str(int(time.time()))
            paydata = {
                "market": "{}".format(market),
                "side": "buy",
                "amount": "{}".format(amount),
                "request": "/" + request,
                "nonce": nonce
            }
            return await self.post(request, paydata)
        except Exception as e:
            print(e)
            return None

    async def sell_order_market(self, market, amount):
        try:
            request = 'api/v4/order/market'
            nonce = str(int(time.time()))
            paydata = {
                "market": "{}".format(market),
                "side": "sell",
                "amount": "{}".format(amount),
                "request": "/" + request,
                "nonce": nonce
            }
            return await self.post(request, paydata)
        except Exception as e:
            print(e)
            return None

    async def buy_order_limit(self, paritet, price, amount):
        """
        :param paritet:
        :param price:
        :param amount:
        :return:
        """
        try:
            request = 'api/v4/order/new'
            nonce = str(int(time.time()))
            paydata = {
                "market": "{}".format(paritet),
                "side": "buy",
                "amount": "{}".format(amount),
                "price": price,
                "request": "/" + request,
                "nonce": nonce
            }
            return await self.post(request, paydata)
        except Exception as e:
            print(e)
            return None

    async def sell_order_limit(self, paritet, price, amount):
        """
        :param paritet:
        :param price:
        :param amount:
        :return:
        """
        try:
            request = 'api/v4/order/new'
            nonce = str(int(time.time()))
            paydata = {
                "market": "{}".format(paritet),
                "side": "sell",
                "amount": "{}".format(amount),
                "price": price,
                "request": "/" + request,
                "nonce": nonce
            }
            return await self.post(request, paydata)
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
