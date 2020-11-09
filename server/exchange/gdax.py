import json
import logging
from datetime import datetime, timezone
from fetcher import WebsocketFetcher
from db import Trade

def parse_time(time):
    ts = datetime.strptime(time.split('.')[0],
                           '%Y-%m-%dT%H:%M:%S')
    x = ts.replace(tzinfo=timezone.utc).astimezone(tz=None).timestamp()
    return int(x) * 1000


class Fetcher(WebsocketFetcher):
    NAME = 'Coinbase PRO'
    URI = 'wss://ws-feed.pro.coinbase.com'

    async def subscribe(self, ws):
        self.symbols = {}
        for base, quote, pair_id in self.pairs:
            symbol = f'{base}-{quote}'
            self.symbols[symbol] = pair_id
        await ws.send(json.dumps({
            'type': 'subscribe',
            'product_ids': list(self.symbols.keys()),
            'channels': ['matches']
        }))

    async def parse_message(self, message, callback):
        msg = json.loads(message)
        if isinstance(msg, dict):
            if msg['type'] == 'match':
                await callback(Trade(
                    self.symbols[msg['product_id']],
                    parse_time(msg['time']),
                    float(msg['size']) * (-1 if msg['side'] == 'sell' else 1),
                    float(msg['price'])
                ))
            elif msg['type'] == 'subscriptions':
                for chan in msg['channels']:
                    if chan['name'] == 'matches':
                        for p_id in chan['product_ids']:
                            logging.info('subscribed to %s',
                                         p_id)

