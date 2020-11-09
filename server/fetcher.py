import logging
import asyncio
from importlib import import_module
import websockets
from typing import Sequence, Tuple, Union, Callable, Awaitable
import zmq
import zmq.asyncio
import db
from db import Trade
from config import config
import uvloop

ctx = zmq.asyncio.Context()

TradeFetchCallback = Callable[[Trade], Awaitable[None]]

class TradeFetcher:
    def __init__(self, ex_id: int, pairs: Sequence[Tuple[str, str, int]]):
        self.ex_id = ex_id
        self.pairs = pairs


class WebsocketFetcher(TradeFetcher):
    NAME = ''
    URI = ''

    async def run(self, callback: TradeFetchCallback):
        while True:
            try:
                uri = self.uri()
                async with websockets.connect(uri) as ws:
                    logging.info('%s: connected to %s', self.NAME, uri)
                    await self.subscribe(ws)
                    async for msg in ws:
                        await self.parse_message(msg, callback)
                logging.warning('%s: connection closed',
                                self.NAME)
            except websockets.exceptions.ConnectionClosedError:
                logging.warning('%s: connection error, reconnecting',
                                self.NAME)
            except websockets.exceptions.WebSocketException as e:
                logging.warning('%s: websocket exception: %s',
                                self.NAME,
                                str(e))
                if str(e).find('HTTP 429') >= 0:
                    await asyncio.sleep(600)

    def uri(self) -> str:
        return self.URI

    async def subscribe(self, ws: websockets.WebSocketClientProtocol):
        pass

    async def parse_message(
        self, msg: Union[str, bytes], callback: TradeFetchCallback
    ):
        pass


async def run_fetchers():
    pub = ctx.socket(zmq.PUB) # pylint: disable=E1101
    pub.bind(f'tcp://*:{config["zmq_port"]}')
    db_pool = await db.connect()
    async def callback(trade: Trade):
        await db.insert_trade(db_pool, trade)
        await pub.send(trade.serialize())
    task_list = []
    for ex in config['exchanges']:
        ex_name = ex['name']
        mod = import_module(f'.{ex_name}', 'exchange')
        ex_id = await db.get_exchange_id(db_pool, ex_name)
        pair_list = []
        for base, quote in [x.split('/') for x in ex['pairs']]:
            pair_id = await db.get_pair_id(db_pool, ex_id, base, quote)
            pair_list.append((base, quote, pair_id))
        fetcher = mod.Fetcher(ex_name, pair_list)
        task_list.append(fetcher.run(callback))
    await asyncio.gather(*task_list)

if __name__ == '__main__':
    uvloop.install()
    asyncio.run(run_fetchers())

