from abc import abstractmethod


class Ticker:
    def __init__(self, bid: str, ask: str, last: str):
        self.bid = bid
        self.ask = ask
        self.last = last


class Wallet:
    def __init__(self, available: str):
        self.available = available


class OpenOrder:
    def __init__(self, price, order_id, amount, side):
        self.price = price
        self.order_id = order_id
        self.amount = amount
        self.side = side


class Client:
    @abstractmethod
    async def get_ticker(self, paritet) -> Ticker: pass

    @abstractmethod
    async def get_wallet(self, paritet) -> Wallet: pass

    @abstractmethod
    async def buy_order_market(self, paritet, amount): pass

    @abstractmethod
    async def sell_order_market(self, paritet, amount): pass

    @abstractmethod
    async def buy_order_limit(self, paritet, price, amount): pass

    @abstractmethod
    async def sell_order_limit(self, paritet, price, amount): pass

    @abstractmethod
    async def get_open_orders(self, symbol): pass
