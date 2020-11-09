from quart import Blueprint, request, jsonify, current_app as app
from decimal import Decimal
import db
from datetime import datetime, timedelta
from quart_cors import cors
from http import HTTPStatus


api = Blueprint('api', __name__)
api = cors(api)


def db_call_handler(f):
    async def wrapper():
        if 'pairs' not in request.args:
            return 'invalid arguments', HTTPStatus.BAD_REQUEST.value
        try:
            pairs = [*map(int, request.args['pairs'].split(','))]
            return await f(pairs)
        except ValueError:
            return 'invalid arguments', HTTPStatus.BAD_REQUEST.value
        except db.DBInvalidParams as e:
            return str(e), HTTPStatus.BAD_REQUEST.value
    wrapper.__name__ = f.__name__
    return wrapper


@api.route('/pairs')
async def pairs():
    pairs = {}
    for symbol, pair_id, _, disp_name in await db.get_pair_list(app.db_pool):
        if symbol not in pairs:
            pairs[symbol] = []
        pairs[symbol].append({'id': pair_id, 'ex': disp_name})
    return pairs


@api.route('/timeframes')
async def timeframes():
    return jsonify(db.TIMEFRAMES)


@api.route('/summary')
@db_call_handler
async def summary(pairs):
    interval = request.args.get('interval', default=60, type=int)
    end = datetime.now()
    start = end - timedelta(seconds=interval)
    return await db.get_summary(app.db_pool, pairs, start, end)


@api.route('/chart/price')
@db_call_handler
async def price(pairs):
    start = request.args.get(
        'start',
        default=int((datetime.now() - timedelta(hours=1)).timestamp() * 1000),
        type=int
    )
    interval = request.args.get('interval', default=60, type=int)
    cnt = request.args.get('count', default=60, type=int)
    return jsonify(
        await db.get_simple_price_chart(
            app.db_pool,
            pairs,
            datetime.fromtimestamp(start / 1000),
            timedelta(seconds=interval),
            cnt
        )
    )


@api.route('/chart/ohlc')
@db_call_handler
async def ohlcv(pairs):
    start = request.args.get(
        'start',
        default=int((datetime.now() - timedelta(hours=1)).timestamp() * 1000),
        type=int
    )
    interval = request.args.get('interval', default=60, type=int)
    cnt = request.args.get('count', default=60, type=int)
    return jsonify(
        await db.get_ohlc_chart(
            app.db_pool,
            pairs,
            datetime.fromtimestamp(start / 1000),
            timedelta(seconds=interval),
            cnt
        )
    )


@api.route('/chart/volume')
@db_call_handler
async def volume(pairs):
    start = request.args.get(
        'start',
        default=int((datetime.now() - timedelta(hours=1)).timestamp() * 1000),
        type=int
    )
    interval = request.args.get('interval', default=60, type=int)
    count = request.args.get('count', default=60, type=int)
    start = start - start % interval
    return jsonify(
        await db.get_volume_chart(
            app.db_pool,
            pairs,
            datetime.fromtimestamp(start / 1000),
            timedelta(seconds=interval),
            count
        )
    )


@api.route('/chart/volume-profile')
@db_call_handler
async def volume_profile(pairs):
    start = request.args.get(
        'start',
        default=int((datetime.now() - timedelta(hours=1)).timestamp() * 1000),
        type=int
    )
    end = request.args.get(
        'end',
        default=int(datetime.now().timestamp() * 1000),
        type=int
    )
    frames = request.args.get('frames', default=20, type=int)
    dt_start = datetime.fromtimestamp(start / 1000)
    dt_end = datetime.fromtimestamp(end / 1000)
    if (dt_end - dt_start).total_seconds() > 86400:
        return 'Time range is too large', HTTPStatus.BAD_REQUEST.value
    if frames > 30:
        return 'Frame count is too large', HTTPStatus.BAD_REQUEST.value
    return jsonify(
        await db.get_volume_profile_chart(
            app.db_pool,
            pairs,
            dt_start,
            dt_end,
            frames
        )
    )

