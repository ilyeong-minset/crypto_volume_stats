import json
from datetime import datetime
import logging
from db import Trade
from fetcher import WebsocketFetcher

class Fetcher(WebsocketFetcher):
    NAME = 'Bitfinex'
    URI = 'wss://api-pub.bitfinex.com/ws/2'

    async def subscribe(self, ws):
        self.symbols = {}
        self.channels = {}
        for base, quote, pair_id in self.pairs:
            symbol = f't{base}{quote}'
            self.symbols[symbol] = pair_id
            await ws.send(json.dumps({
                'event': 'subscribe',
                'channel': 'trades',
                'symbol': symbol
            }))

    async def parse_message(self, message, callback):
        msg = json.loads(message)
        if isinstance(msg, dict):
            if (
                msg['event'] == 'subscribed'
                and msg['channel'] == 'trades'
                and msg['symbol'] in self.symbols
            ):
                self.channels[msg['chanId']] = self.symbols[msg['symbol']]
                logging.info('subscribed to %s',
                             msg['symbol'])
        elif isinstance(msg, list) and len(msg) == 3:
            chan_id, _, [_, ts, amt, price] = msg
            await callback(Trade(self.channels[chan_id], int(ts), amt, price))

