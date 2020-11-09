import json
from datetime import datetime
import logging
from db import Trade
from fetcher import WebsocketFetcher

class Fetcher(WebsocketFetcher):
    NAME = 'Bitstamp'
    URI = 'wss://ws.bitstamp.net'

    async def subscribe(self, ws):
        self.channels = {}
        for base, quote, pair_id in self.pairs:
            channel_name = 'live_trades_' + base.lower() + quote.lower()
            self.channels[channel_name] = pair_id
            await ws.send(json.dumps({
                'event': 'bts:subscribe',
                'data': {
                    'channel': channel_name
                }
            }))

    async def parse_message(self, message, callback):
        msg = json.loads(message)
        if msg['event'] == 'trade':
            trade = msg['data']
            await callback(Trade(
                self.channels[msg['channel']],
                int(trade['timestamp']) * 1000,
                trade['amount'] * (-1 if trade['type'] == 1 else 1),
                trade['price']
            ))
        elif msg['event'] == 'bts:subscription_succeeded':
            logging.info('subscribed to %s',
                         msg['channel'])

