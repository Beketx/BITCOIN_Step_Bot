import asyncio

from src.client import Client, Wallet, Ticker


class MockClient(Client):


    async def get_ticker(self, paritet) -> Ticker:
        return Ticker("5", "6", "7.8")

    async def get_wallet(self, paritet) -> Wallet:
        return Wallet("10")

    async def buy_order_market(self, paritet, amount):
        await asyncio.sleep(5)
        if amount == 5:
            return None
        else:
            return True

    async def sell_order_market(self, paritet, amount):
        await asyncio.sleep(3)
        if amount == 10:
            return None
        else:
            return True

    async def buy_order_limit(self, paritet, price, amount):
        await asyncio.sleep(2)
        if price == 7.5:
            return None
        else:
            return True

    async def sell_order_limit(self, paritet, price, amount):
        await asyncio.sleep(2)
        if price == 7.5:
            return None
        else:
            return True
