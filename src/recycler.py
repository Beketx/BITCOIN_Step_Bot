import asyncio
import enum
import time
import schedule
from typing import List

from src.binance.rest import BinanceClient
from src.bitfinex.rest import BfxClientWrapper
from src.client import Client
from src.mock.mock_rest import MockClient
from src.whitebit.rest import WhiteBitClient


class Stock(enum.Enum):
    BINANCE = 'BINANCE'
    WHITEBIT = 'WHITEBIT'
    BITFINEX = 'BITFINEX'
    MOCK = 'MOCK'


class OrderType(enum.Enum):
    MARKET = "Market"
    LIMIT = "Limit"


BINANCE_API_KEY = "yeMW6p7ZxOjRTg1CORTWHQ4LneI8r2VU5CICPtLg48oquRfYLL1JW3GeR3t6wQ0S"
BINANCE_API_SECRET = "Qpxj0wtnSbUWrUQbAGzwgNunn5icPnHlB63u7P5yD3PTdPxGjUjdzBp438cwSkAH"
BITFINEX_API_KEY = "L3tAktqOf7YxQ1zVoxlqjUk0PztTREj5tfiqdzoIMoR"
BITFINEX_API_SECRET = "hyp4Txyt3IVsaGx5zGqegoeL1pZV6Uh65VCEMvOe1Lk"
WHITEBIT_API_KEY = "a6b88c85d2e229b6bd80b089e8f57245"
WHITEBIT_API_SECRET = "0ae248a4132d384f0c379d2ef503cc09"


STOCK = Stock.BINANCE
CURRENCY_PAIR_FIRST = "NEO"
CURRENCY_PAIR_SECOND = "USDT"
FIRST_PRICE = 36  # in Second part of pair, Ex: USD
LAST_PRICE = 42  # in Second part of pair, Ex: USD
TOTAL_AMOUNT = 1  # in First part of pair. Ex: NEO
STEP_SIZE = 2
IS_STOP_LOSS_NEEDED = False
STOP_LOSS_TYPE = OrderType.LIMIT  # Market / Limit
STOP_LOSS_PRICE = 5  # in Second part of pair, Ex: USD
TIME_DURATION = 5  # in seconds


""" Variables created dynamically """
DIFFERENCE = float(LAST_PRICE - FIRST_PRICE) / STEP_SIZE
AMOUNT = float(TOTAL_AMOUNT) / STEP_SIZE
END_SESSION = False


class LocalOrder:
    def __init__(self, buy, sell, amount):
        self.buy = buy
        self.sell = sell
        self.amount = amount

    def __str__(self):
        return f"buy: {self.buy}, sell: {self.sell}, amount:{self.amount}"


def create_table():
    table = []
    for i in range(1, STEP_SIZE + 1):
        table.append(LocalOrder(
            buy=FIRST_PRICE + DIFFERENCE * (i - 1),
            sell=FIRST_PRICE + DIFFERENCE * i,
            amount=AMOUNT
        ))
    return table


class PingPongBot:
    client: Client
    paritet: str

    def __init__(self):
        if STOCK == Stock.BITFINEX:
            self.client = BfxClientWrapper(BITFINEX_API_KEY, BITFINEX_API_SECRET)
            self.paritet = f"t{CURRENCY_PAIR_FIRST}{CURRENCY_PAIR_SECOND}"
        elif STOCK == Stock.BINANCE:
            self.client = BinanceClient(BINANCE_API_KEY, BINANCE_API_SECRET)
            self.paritet = f"{CURRENCY_PAIR_FIRST}{CURRENCY_PAIR_SECOND}"
        elif STOCK == Stock.WHITEBIT:
            self.client = WhiteBitClient(WHITEBIT_API_KEY, WHITEBIT_API_SECRET)
            self.paritet = f"{CURRENCY_PAIR_FIRST}_{CURRENCY_PAIR_SECOND}"
        elif STOCK == Stock.MOCK:
            self.client = MockClient()
            self.paritet = "x"
        else:
            raise NameError("Did not find stock type or None")

        self.table = create_table()
        self.bid_ping_table: List[LocalOrder] = [LocalOrder(row.buy, row.sell, amount=AMOUNT) for row in self.table]
        self.ask_pong_table: List[LocalOrder] = []

    def execute(self):
        ticker = asyncio.get_event_loop().run_until_complete(self.client.get_ticker(self.paritet))
        if ticker is None:
            print()
            print("Something went wrong while fetching TICKET")
            return
        stock_price = float(ticker.last)
        print()
        print(f"Current {self.paritet} PRICE: {stock_price}")

        rows_to_buy = [row for row in self.bid_ping_table if row.buy >= stock_price]
        rows_to_sell = [row for row in self.ask_pong_table if row.sell <= stock_price]

        # Buy request to client
        # brought_rows = asyncio.get_event_loop().run_until_complete(self.buy_rows(rows_to_buy))

        # Sell request to client
        # sold_rows = asyncio.get_event_loop().run_until_complete(self.sell_rows(rows_to_sell))

        brought_rows, sold_rows = asyncio.get_event_loop().run_until_complete(
            self.execute_orders(rows_to_buy, rows_to_sell)
        )
        print()
        print(f"Session bought {len(brought_rows)} rows")
        print(f"Session sold {len(sold_rows)} rows")
        global END_SESSION
        asyncio.get_event_loop().run_until_complete(self.check_stop_loss(stock_price))

    async def execute_orders(self, rows_to_buy, rows_to_sell):
        return await asyncio.gather(self.buy_rows(rows_to_buy), self.sell_rows(rows_to_sell))

    async def buy_rows(self, rows: List[LocalOrder]):
        """
        :param rows: List[LocalOrder]
        :return: List[LocalOrder]
        asynchronously buy rows
        if not successfully executed, it won't insert unsuccessful rows into returning value
        """
        all_brought_rows = await asyncio.gather(
            *[self.client.buy_order_limit(paritet=self.paritet, amount=row.amount, price=row.buy) for row in rows]
        )
        success_rows = []
        for row_index in range(len(all_brought_rows)):
            if all_brought_rows[row_index] is not None:
                success_rows.append(rows[row_index])

        for buy_row in success_rows:
            if buy_row not in self.bid_ping_table:
                continue
            self.bid_ping_table.remove(buy_row)
            self.ask_pong_table.append(buy_row)

        return success_rows

    async def sell_rows(self, rows: List[LocalOrder]):
        """
        :param rows: List[LocalOrder]
        :return: List[LocalOrder]
        asynchronously sell rows
        if not successfully executed, it won't insert unsuccessful row into returning value
        """
        all_sold_rows = await asyncio.gather(
            *[self.client.sell_order_limit(paritet=self.paritet, amount=row.amount, price=row.sell) for row in rows]
        )
        success_rows = []
        for row_index in range(len(all_sold_rows)):
            if all_sold_rows[row_index] is not None:
                success_rows.append(rows[row_index])

        for sell_row in success_rows:
            if sell_row not in self.ask_pong_table:
                continue
            self.ask_pong_table.remove(sell_row)
            self.bid_ping_table.append(sell_row)

        return success_rows

    async def check_stop_loss(self, current_price):
        if not IS_STOP_LOSS_NEEDED:
            return

        if STOP_LOSS_PRICE < current_price:  # 5 USD < 4 USD
            return

        total_sell = None
        if STOP_LOSS_TYPE == OrderType.MARKET:
            total_sell = await self.client.sell_order_limit(self.paritet, STOP_LOSS_PRICE / 2, TOTAL_AMOUNT)
        elif STOP_LOSS_TYPE == OrderType.LIMIT:
            total_sell = await self.client.sell_order_limit(self.paritet, STOP_LOSS_PRICE, TOTAL_AMOUNT)

        if total_sell is None:
            print()
            print("Something went wrong while STOP LOSS")

        global END_SESSION
        END_SESSION = True

    def print_order_table(self):
        print()
        print("====== BUY TABLE ======")
        for row in self.bid_ping_table:
            print(row)
        print("====== SELL TABLE ======")
        for row in self.ask_pong_table:
            print(row)


bot = PingPongBot()
bot.print_order_table()


def scheduled_task():
    bot.execute()
    bot.print_order_table()


def start():
    schedule.every(TIME_DURATION).seconds.do(scheduled_task)

    while not END_SESSION:
        schedule.run_pending()


# print(asyncio.get_event_loop().run_until_complete(bot.client.get_wallet("USDT")).available)
# print(asyncio.get_event_loop().run_until_complete(bot.client.buy_order_limit("NEO_USDT", 34.43, 0.3)))

start()


'''
Working with async:
 - create Task that will run at background concurrently with [create_task]
 - await Task with returning value
 
Or using asyncio.[gather(List[Concurrent function])]

Example 1:
    task = asyncio.create_task( some_async_function() )
    await task

Example 2:
    await asyncio.gather( [ some_async_function() ] )
'''