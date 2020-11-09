import axios from 'axios'
import config from './config'

const api = axios.create({
    validateStatus: code => code >= 200 && code < 500,
    baseURL: config.apiEndpoint
})

async function get(path, params) {
    let result
    try {
        result = await api.get(path, {
            params
        })
    } catch (e) {
        throw `Network error while requesting ${path}`
    }
    if (result.status === 200)
        return result.data
    else
        throw `${path} returned error (${result.status}): ${result.data}`
}

let pairs = null,
    pairDict = null

export async function getPairs() {
    if (pairs === null) {
        pairs = await get('/pairs')
    }
    return pairs
}

export async function getPairsDict() {
    if (pairDict === null) {
        const pairs = await getPairs()
        pairDict = {}
        for (const sym in pairs)
            for (const id of pairs[sym])
                pairDict[id.id] = {
                    ex: id.ex,
                    sym
                }
    }
    return pairDict
}

let timeframes = null

export async function getTimeframes() {
    if (timeframes === null) {
        timeframes = await get('/timeframes')
    }
    return timeframes
}

export async function getSummary(pairs, interval) {
    return await get('/summary', {
        interval: interval,
        pairs: pairs.join(',')
    })
}

export async function getPriceChart(pairs, start, interval, count) {
    return await get('/chart/price', {
        pairs: pairs.join(','),
        start,
        count,
        interval
    })
}

export async function getOHLCVChart(pairs, start, interval, count) {
    return await get('/chart/ohlc', {
        pairs: pairs.join(','),
        start,
        count,
        interval
    })
}

export async function getVolumeChart(pairs, start, interval, count) {
    return await get('/chart/volume', {
        pairs: pairs.join(','),
        start,
        count,
        interval
    })
}

export async function getVolumeProfileChart(pairs, start, end, frames) {
    return await get('/chart/volume-profile', {
        pairs: pairs.join(','),
        start,
        end,
        frames
    })
}

let tradeCallback = null

const ws = new WebSocket(config.wsEndpoint)
ws.onmessage = (ev) => {
    const data = JSON.parse(ev.data)
    if (data.event === 'trade') {
        if (tradeCallback)
            tradeCallback(data.data)
    }
}

export function setTradeCallback(callback) {
    tradeCallback = callback
}

export function subscribe(pairs) {
    ws.send(JSON.stringify({
        action: 'subscribe',
        pairs: pairs
    }))
}

export function unsubscribe(pairs) {
    const data = {
        action: 'unsubscribe'
    }
    if (pairs !== null) {
        data.pairs = pairs
    }
    ws.send(JSON.stringify(data))
}

