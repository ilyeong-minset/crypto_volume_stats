import asyncio
import json
from datetime import datetime
import logging
from fetcher import WebsocketFetcher
from db import Trade

TIMEOUT = 10.0

class Fetcher(WebsocketFetcher):
    NAME = 'Kraken'
    URI = 'wss://ws.kraken.com'

    async def subscribe(self, ws):
        self.channels = {}
        self.symbols = {}
        self.last_heartbeat = None
        for base, quote, pair_id in self.pairs:
            if base == 'BTC':
                base = 'XBT'
            if quote == 'BTC':
                quote = 'XBT'
            symbol = base + '/' + quote
            self.symbols[symbol] = pair_id
        await ws.send(json.dumps({
            'event': 'subscribe',
            'pair': [*self.symbols.keys()],
            'subscription': {
                'name': 'trade'
            }
        }))

    async def parse_message(self, message, callback):
        msg = json.loads(message)
        if isinstance(msg, dict):
            if (
                msg['event'] == 'subscriptionStatus'
                and msg['status'] == 'subscribed'
                and msg['channelName'] == 'trade'
                and 'channelID' in msg
            ):
                self.channels[msg['channelID']] = \
                    self.symbols[msg['pair']]
                logging.info('subscribed to %s',
                             msg['pair'])
            elif msg['event'] == 'heartbeat':
                self.last_heartbeat = datetime.now()
                logging.debug('HEARTBEAT')
        elif isinstance(msg, list):
            chan_id, trades, *_ = msg
            for (price, amount, ts, side, *_) in trades:
                await callback(Trade(
                    self.channels[chan_id],
                    int(float(ts) * 1000),
                    float(amount) * (-1 if side == 's' else 1),
                    float(price)
                ))

    async def run(self, callback):
        class Reconnect(Exception):
            pass
        async def check_heartbeat():
            while True:
                if self.last_heartbeat:
                    dt = (
                        datetime.now() - self.last_heartbeat
                    ).total_seconds()
                    if dt > TIMEOUT:
                        logging.warning(
                            'heartbeat received %s seconds ago, ' +
                            'reconnecting',
                            dt)
                        raise Reconnect()
                await asyncio.sleep(1)
        while True:
            self.last_heartbeat = None
            try:
                runner = asyncio.create_task(super().run(callback))
                await asyncio.gather(check_heartbeat(), runner)
            except Reconnect:
                runner.cancel()

