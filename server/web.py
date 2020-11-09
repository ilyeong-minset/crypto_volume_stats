import asyncio
from quart import (
    Quart, render_template, websocket, send_file
)
import json
import os
import zmq
import zmq.asyncio
import logging
from typing import NamedTuple
import struct
import db
from db import Trade
from api import api
from config import config, app_dir

static_folder = os.path.join(app_dir, '..', 'client', 'dist')
app = Quart(__name__,
            static_folder=static_folder,
            static_url_path='')
app.register_blueprint(api, url_prefix='/api')
ctx = zmq.asyncio.Context()


@app.before_serving
async def init():
    app.db_pool = await db.connect()


@app.route('/')
async def index():
    return await send_file(os.path.join(static_folder, 'index.html'))


class TradeQueue(NamedTuple):
    sock: zmq.asyncio.Socket
    pairs: set


async def ws_send(queue: TradeQueue):
    while True:
        trade = Trade.deserialize(await queue.sock.recv())
        await websocket.send(json.dumps({
            'event': 'trade',
            'data': dict(zip(('pair', 'timestamp', 'amount', 'price'),
                             trade))
        }))


async def ws_receive(queue: TradeQueue):
    while True:
        msg = json.loads(await websocket.receive())
        if 'action' in msg:
            if (
                msg['action'] == 'subscribe' and
                'pairs' in msg and
                all([isinstance(x, int) for x in msg['pairs']])
            ):
                for pair in msg['pairs']:
                    queue.pairs.add(pair)
                    queue.sock.subscribe(struct.pack('i', pair))
                logging.info('subscribed to: %s', msg['pairs'])
                await websocket.send(json.dumps({
                    'event': 'subscribed',
                    'pairs': msg['pairs']
                }))
            elif msg['action'] == 'unsubscribe':
                if (
                    'pairs' in msg and
                    all([isinstance(x, int) for x in msg['pairs']])
                ):
                    pairs = msg['pairs']
                else:
                    pairs = list(queue.pairs)
                for pair in pairs:
                    queue.pairs.remove(pair)
                    queue.sock.unsubscribe(struct.pack('i', pair))
                logging.info('unsubscribed from: %s', pairs)
                await websocket.send(json.dumps({
                    'event': 'unsubscribed',
                    'pairs': pairs
                }))


@app.websocket('/ws')
async def ws():
    logging.info('opening websocket connection')
    sock = ctx.socket(zmq.SUB) # pylint: disable=E1101
    sock.connect(f'tcp://127.0.0.1:{config["zmq_port"]}')
    try:
        queue = TradeQueue(sock, set())
        await asyncio.gather(ws_send(queue), ws_receive(queue))
    finally:
        logging.info('closing websocket connection')
        sock.close()

