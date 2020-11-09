import asyncio
from collections import namedtuple
import asyncpg
from asyncpg.pool import Pool
import logging
from decimal import Decimal
import yaml
from typing import List, Tuple, Dict, T, NamedTuple
from datetime import datetime, timedelta, timezone
from importlib import import_module
from dateutil import parser
import struct
from config import config


TIMEFRAMES = [
    60, 300, 900, 1800, 3600, 14400, 43200, 86400
]


class Trade(NamedTuple):
    pair_id: int
    timestamp: int
    amount: float
    price: float

    def serialize(self):
        return struct.pack('iQdd', self.pair_id, self.timestamp,
                           self.amount, self.price)

    @classmethod
    def deserialize(cls, b):
        return cls(*struct.unpack('iQdd', b))


class DBException(Exception): pass
class DBInvalidParams(DBException): pass


async def get_exchange_id(db_pool: Pool, name: str):
    async with db_pool.acquire() as conn:
        mod = import_module(f'.{name}', 'exchange')
        display_name = mod.Fetcher.NAME
        await conn.execute('''
            INSERT INTO exchanges (name, display_name)
            VALUES($1, $2)
            ON CONFLICT DO NOTHING
        ''', name, display_name)
        return await conn.fetchval('''
            SELECT id FROM exchanges WHERE name = $1
        ''', name)


async def get_pair_id(db_pool: Pool, ex_id: int, base: str, quote: str):
    async with db_pool.acquire() as conn:
        async def get():
            pair_id = await conn.fetchval('''
                SELECT id FROM pairs
                WHERE exchange = $1 AND
                      base = $2 AND
                      quote = $3
            ''', ex_id, base, quote)
            return pair_id
        pair_id = await get()
        if not pair_id:
            await conn.execute('''
                INSERT INTO pairs (exchange, base, quote)
                VALUES ($1, $2, $3)
            ''', ex_id, base, quote)
            pair_id = await get()
        return pair_id


time_2k = parser.parse('2000-01-01 00:00:00')\
    .replace(tzinfo=timezone.utc)\
    .astimezone(tz=None)\
    .timestamp() * 1000

async def insert_trade(db_pool: Pool, trade: Trade):
    logging.debug('trade: %s: pair: %s; amount: %s; price: %s',
                  # trade.timestamp.strftime('%d.%m.%Y %H:%M:%S'),
                  '',
                  trade.pair_id,
                  trade.amount,
                  trade.price)
    async with db_pool.acquire() as conn:
        await conn.set_type_codec(
            'timestamptz',
            encoder=lambda x: ((x - time_2k) * 1000,),
            decoder=str,
            schema='pg_catalog', format='tuple'
        )
        await conn.execute(
            '''
            INSERT INTO trades (pair, ts, amount, price)
            VALUES ($1, $2, $3, $4)
            ''',
            *trade
        )


def to_dict(record: asyncpg.Record) -> Dict[str, T]:
    result = {}
    for k, v in record.items():
        if isinstance(v, Decimal):
            result[k] = float(v)
        else:
            result[k] = v
    return result


async def get_pair_list(db_pool: Pool) -> List[Tuple[str, int, str, str]]:
    async with db_pool.acquire() as conn:
        result = await conn.fetch('''
            SELECT concat(pairs.base, '/', pairs.quote) as symbol,
                   pairs.id as pair_id,
                   exchanges.name as ex_name,
                   exchanges.display_name as disp_name
            FROM pairs
            JOIN exchanges ON pairs.exchange = exchanges.id
        ''')
        return result


async def get_summary(
    db_pool: Pool, pairs: List[int], start: datetime, end: datetime
) -> Dict[str, float]:
    async with db_pool.acquire() as conn:
        try:
            result = await conn.fetchrow(
                'SELECT * FROM get_summary($1::int[], $2, $3)',
                pairs, start, end
            )
            return to_dict(result)
        except asyncpg.exceptions.RaiseError as e:
            raise DBInvalidParams(str(e))


async def get_volume_chart(
    db_pool: Pool,
    pairs: List[int],
    start: datetime,
    interval: timedelta,
    count: int
) -> List[Tuple[int, float, float]]:
    if interval.total_seconds() not in TIMEFRAMES:
        raise DBInvalidParams('invalid interval')
    async with db_pool.acquire() as conn:
        await conn.set_type_codec(
            'numeric', encoder=str, decoder=float,
            schema='pg_catalog', format='text'
        )
        try:
            result = await conn.fetch(
                '''
                SELECT * FROM aggregate_volume(
                    $1::int[], $2, $3, $4
                )
                ''',
                pairs,
                start,
                interval,
                count
            )
            return [*map(tuple, result)]
        except asyncpg.exceptions.RaiseError as e:
            raise DBInvalidParams(str(e))


async def get_simple_price_chart(
    db_pool: Pool,
    pairs: List[int],
    start: datetime,
    interval: timedelta,
    count: int
) -> List[Tuple[int, float]]:
    if interval.total_seconds() not in TIMEFRAMES:
        raise DBInvalidParams('invalid interval')
    async with db_pool.acquire() as conn:
        await conn.set_type_codec(
            'numeric', encoder=str, decoder=float,
            schema='pg_catalog', format='text'
        )
        try:
            result = await conn.fetch(
                '''
                SELECT * FROM get_simple_price_chart(
                    $1::int[], $2, $3, $4
                )
                ''',
                pairs,
                start,
                interval,
                count
            )
            return [*map(tuple, result)]
        except asyncpg.exceptions.RaiseError as e:
            raise DBInvalidParams(str(e))


async def get_ohlc_chart(
    db_pool: Pool,
    pairs: List[int],
    start: datetime,
    interval: timedelta,
    count: int
) -> List[Tuple[int, float, float, float, float]]:
    if interval.total_seconds() not in TIMEFRAMES:
        raise DBInvalidParams('invalid interval')
    async with db_pool.acquire() as conn:
        await conn.set_type_codec(
            'numeric', encoder=str, decoder=float,
            schema='pg_catalog', format='text'
        )
        try:
            result = await conn.fetch(
                '''
                SELECT * FROM get_ohlc_chart(
                    $1::int[], $2, $3, $4
                )
                ''',
                pairs,
                start,
                interval,
                count
            )
            return [*map(tuple, result)]
        except asyncpg.exceptions.RaiseError as e:
            raise DBInvalidParams(str(e))


async def get_volume_profile_chart(
    db_pool: Pool,
    pairs: List[int],
    start: datetime,
    end: datetime,
    frames: int
) -> List[Tuple[float, float, float, float]]:
    async with db_pool.acquire() as conn:
        await conn.set_type_codec(
            'numeric', encoder=str, decoder=float,
            schema='pg_catalog', format='text'
        )
        try:
            result = await conn.fetch(
                '''
                SELECT * FROM get_volume_profile(
                    $1::int[], $2, $3, $4
                )
                ''',
                pairs,
                start,
                end,
                frames
            )
            return [*map(tuple, result)]
        except asyncpg.exceptions.RaiseError as e:
            raise DBInvalidParams(str(e))


async def connect() -> Pool:
    if not connect.db_pool:
        connect.db_pool = await asyncpg.create_pool(**config['dbconf'])
        logging.info(f"connected to db {config['dbconf']}")
    return connect.db_pool

connect.db_pool = None

