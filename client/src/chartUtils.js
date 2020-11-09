import _ from 'lodash'

export const timestampToLabel = x =>
    new Date(x).toLocaleTimeString()

export const alignTimestamp = (interval, time = Date.now()) =>
    time - time % (interval * 1000)

export function timeBounds(timeframe, barCount, offset = 0) {
    const last = alignTimestamp(timeframe) - (timeframe * offset * 1000),
        first = last - timeframe * (barCount - 1) * 1000
    return [first, last]
}

export class ChartData {
    rawData = []
    data = []
    pairIds = []
    timeframe = 0

    constructor(pairIds, timeframe) {
        this.pairIds = pairIds
        this.timeframe = timeframe
    }
    sliceData(first, last) {
        return this.rawData.slice(this.rawData.findIndex(x => x[0] === first),
            this.rawData.findIndex(x => x[0] === last) + 1)
    }
    get firstBar() {
        return this.rawData[0]
    }
    get lastBar() {
        return this.rawData[this.rawData.length - 1]
    }
    async update(pairIds, timeframe, barCount, offset) {
        if (!_.isEqual(pairIds, this.pairIds) || this.timeframe !== timeframe) {
            this.pairIds = pairIds
            this.timeframe = timeframe
            this.rawData = []
        }
        const [first, last] = timeBounds(this.timeframe, barCount, offset)
        if (this.rawData.length === 0) {
            this.rawData = await this.fetchData(first, barCount)
        } else if (first < this.firstBar[0]) {
            const d = await this.fetchData(first,
                (this.firstBar[0] - first) / (this.timeframe * 1000))
            for (let i = d.length - 1; i >= 0; i--)
                this.rawData.unshift(d[i])
        } else {
            const start = this.lastBar[0],
                count = ((last - start) / (this.timeframe * 1000)) + 1
            if (count > 1) {
                this.rawData.pop()
                this.rawData.push(...await this.fetchData(start, count))
            }
        }
        this.data = this.sliceData(first, last)
    }
}

export function movingAverage(input, length, xs = null, skipZeroes = false) {
    const ma = []
    const l = length - 1
    const data = skipZeroes ? input.filter(x => x > 0) : input
    let sum = _.sum(_.take(data, l))
    for (let i = 0, j = 0; i < data.length; i++, j++) {
        if (skipZeroes)
            while (j < input.length && input[j] === 0) {
                ma.push(xs ? {x: xs[j], y: NaN} : NaN)
                j++
            }
        let y
        if (i < l) {
            y = NaN
        } else {
            sum += data[i]
            y = sum / length
            sum -= data[i - l]
        }
        ma.push(xs ? {x: xs[j], y} : y)
    }
    return ma
}

