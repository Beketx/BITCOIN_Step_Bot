import asyncio
from bfxapi import Order
from bfxapi.rest.bfx_rest import BfxRest
from src.client import Client, Ticker, Wallet


class BfxClientWrapper(Client):

    def __init__(self, API_KEY, API_SECRET):
        self.client = BfxRest(
            API_KEY=API_KEY,
            API_SECRET=API_SECRET,
            logLevel='DEBUG'
        )

    async def platform_status(self):
        try:
            response = await self.client.fetch("platform/status")
            return response
        except Exception as e:
            print(e)
            return None

    def get_platform_status(self):
        t = asyncio.ensure_future(self.platform_status())
        status = asyncio.get_event_loop().run_until_complete(t)
        return status[0]

    async def get_ticker(self, symbol):
        """ Get tickers for the given symbol. Tickers shows you the current best bid and ask,
        as well as the last trade price.

        symbol = format: t{}{} -> %First currency, %Second currency

        BfxRest.get_public_ticker(symbol)
        """
        try:
            ticker = await self.client.get_public_ticker(symbol)
            return Ticker(
                bid=str(ticker[0]),
                ask=str(ticker[2]),
                last=str(ticker[6])
            )
        except Exception as e:
            print(e)
            return None

    def get_ticker_synchronized(self, symbol):
        try:
            t = asyncio.ensure_future(self.get_ticker(symbol))
            ticker = asyncio.get_event_loop().run_until_complete(t)
            return ticker
        except Exception as e:
            print(e)
            return None

    async def get_wallet(self, market):
        try:
            wallets = await self.client.get_wallets()
            spec_wallet = next((wallet.balance for wallet in wallets if wallet.currency == market), 0)
            return Wallet(available=str(spec_wallet))
        except Exception as e:
            print(e)
            return None

    def get_wallet_synchronized(self, market):
        try:
            t = asyncio.ensure_future(self.get_wallet(market))
            wallets = asyncio.get_event_loop().run_until_complete(t)
            return wallets
        except Exception as e:
            print(e)
            return None

    async def post_submit_order(self, symbol, amount, price):
        """ Submit Order

        amount = negative for sell, positive for buy

        BfxRest.submit_order(symbol,
                             price,
                             amount,
                             market_type='LIMIT',
                             hidden=False,
                             price_trailing=None,
                             price_aux_limit=None,
                             oco_stop_price=None,
                             close=False,
                             reduce_only=False,
                             post_only=False,
                             oco=False,
                             aff_code=None,
                             time_in_force=None,
                             leverage=None,
                             gid=None)
        """
        order = await self.client.submit_order(
            symbol=symbol,
            market_type=Order.Type.LIMIT,
            amount=amount,
            price=price
        )
        return order

    async def sell_order_market(self, symbol, amount):
        try:
            return await self.post_submit_order(symbol, -amount, 0)
        except Exception as e:
            print(e)
            return None

    async def buy_order_market(self, symbol, amount):
        try:
            return await self.post_submit_order(symbol, amount, 0)
        except Exception as e:
            print(e)
            return None

    async def sell_order_limit(self, paritet, price, amount):
        """
        :param paritet: Ex: NEOUSDT
        :param price: in second pair. Ex: NEOUSDT => second pair: USDT
        :param amount: in first pair. Ex: NEOUSDT => first pair: NEO
        :return:
        """
        try:
            return await self.post_submit_order(paritet, -amount, price)
        except Exception as e:
            print(e)
            return None

    async def buy_order_limit(self, paritet, price, amount):
        """
        :param paritet: Ex: NEOUSDT
        :param price: in second pair. Ex: NEOUSDT => second pair: USDT
        :param amount: in first pair. Ex: NEOUSDT => first pair: NEO
        :return:
        """
        try:
            return await self.post_submit_order(paritet, amount, price)
        except Exception as e:
            print(e)
            return None

    def submit_order(self, symbol, amount, price):
        try:
            t = asyncio.ensure_future(self.post_submit_order(
                symbol=symbol,
                amount=amount,
                price=price
            ))
            order = asyncio.get_event_loop().run_until_complete(t)
            return order
        except Exception as e:
            print(e)
            return None

    def order_buy_market(self, symbol, amount):
        return self.submit_order(symbol, amount, 0)

    def order_sell_market(self, symbol, amount):
        return self.submit_order(symbol, -amount, 0)
