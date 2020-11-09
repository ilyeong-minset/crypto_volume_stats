<template>
    <div>
        <chart-options>
        <horizontal-field labelText="MA1 Length">
            <input
                class="input is-small"
                v-model.number="data.ma1Length"
                @change="rebuildChart">
        </horizontal-field>
        <horizontal-field labelText="MA2 Length">
            <input
                class="input is-small"
                v-model.number="data.ma2Length"
                @change="rebuildChart">
        </horizontal-field>
        </chart-options>
        <chart-scroller v-model="scrollData" @change="updateData()"/>
        <chart :chart-data="chartData"/>
    </div>
</template>
<script>
import Vue from 'vue'
import { Candlestick } from 'vue-chartjs-financial'
import { getOHLCVChart } from '../api'
import makeChartComponent from './ChartBase'
import { ChartData, movingAverage } from '../chartUtils'
import ChartScroller from './ChartScroller.vue'
import HorizontalField from './HorizontalField.vue'
import ChartOptions from './ChartOptions.vue'

class OHLCChartData extends ChartData {
    ma1Length = 5
    ma2Length = 9

    async fetchData(first, count) {
        try {
            const chart = await getOHLCVChart(this.pairIds,
                first, this.timeframe, count)
            return chart
        } catch (e) {
            Vue.flashMessage(e)
            return []
        }
    }
    makeChartData() {
        const ohlc = [],
            avg = [],
            xs = []
        for (const [ts, o, h, l, c] of this.data) {
            ohlc.push({t: ts, o: o, h: h, l: l, c: c})
            avg.push((h + l) / 2)
            xs.push(ts)
        }
        return {
            datasets: [{
                label: 'price',
                data: ohlc,
                order: 1
            }, {
                type: 'line',
                label: 'MA1',
                data: movingAverage(avg, this.ma1Length, xs, true),
                borderColor: '#aaf',
                fill: false,
                pointRadius: 0,
                order: 0
            }, {
                type: 'line',
                label: 'MA2',
                data: movingAverage(avg, this.ma2Length, xs, true),
                borderColor: '#faf',
                fill: false,
                pointRadius: 0,
                order: 0
            }]
        }
    }
}

const chartData = new OHLCChartData([], 0)

export default makeChartComponent(Candlestick, {
    responsive: true,
    maintainAspectRatio: false
}).extend({
    components: { ChartScroller, HorizontalField, ChartOptions },
    data: () => ({
        scrollData: { barCount: 10, offset: 0},
        data: chartData
    }),
    methods: {
        async updateData() {
            await this.data.update(this.selected.pairIds,
                this.selected.timeframe,
                this.scrollData.barCount,
                this.scrollData.offset)
            this.chartData = this.data.makeChartData()
        },
        rebuildChart() {
            this.chartData = this.data.makeChartData()
        }
    }
})
</script>
