import json
from datetime import datetime
from db import Trade
from fetcher import WebsocketFetcher

BASE_URI = 'wss://stream.binance.com:9443/stream?streams='

class Fetcher(WebsocketFetcher):
    NAME = 'Binance'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.symbols = {
            (base + quote).upper(): pair_id
            for base, quote, pair_id in self.pairs
        }

    def uri(self):
        return BASE_URI + '/'.join([
            (base + quote).lower() + '@aggTrade'
            for base, quote, _ in self.pairs
        ])

    async def parse_message(self, message, callback):
        msg = json.loads(message)
        data = msg['data']
        if (
            data['e'] == 'aggTrade'
            and data['s'] in self.symbols
        ):
            await callback(Trade(
                self.symbols[data['s']],
                int(data['T']),
                float(data['q']) * (-1 if data['m'] else 1),
                float(data['p'])
            ))

