<template>
    <div>
        <chart-options>
            <horizontal-field labelText="Diff MA length">
                <input
                    class="input is-small"
                    v-model.number="data.maLength"
                    @change="rebuildChart">
            </horizontal-field>
        </chart-options>
        <chart-scroller v-model="scrollData" @change="updateData()"/>
        <chart :chart-data="chartData"/>
    </div>
</template>
<script>
import Vue from 'vue'
import { Bar } from 'vue-chartjs'
import { getVolumeChart } from '../api'
import makeChartComponent from './ChartBase'
import { ChartData, movingAverage } from '../chartUtils'
import ChartScroller from './ChartScroller.vue'
import HorizontalField from './HorizontalField.vue'
import ChartOptions from './ChartOptions.vue'

class VolumeChartData extends ChartData {
    maLength = 9

    async fetchData(first, count) {
        try {
            return await getVolumeChart(this.pairIds,
                first, this.timeframe, count)
        } catch (e) {
            Vue.flashMessage(e)
            return []
        }
    }
    makeChartData() {
        const labels = [],
            volUp = [],
            volDown = [],
            volDiff = []
        for (const [ts, up, down] of this.data) {
            labels.push(ts)
            volUp.push({x: ts, y: up})
            volDown.push({x: ts, y: -down})
            volDiff.push({x: ts, y: up - down})
        }
        return {
            /*labels,*/
            datasets: [{
                type: 'line',
                label: 'diff',
                borderColor: '#ffa',
                data: volDiff
            }, {
                type: 'line',
                label: 'diff MA',
                borderColor: '#faf',
                data: movingAverage(volDiff.map(x => x.y), this.maLength, labels)
            }, {
                type: 'bar',
                label: 'bought',
                backgroundColor: '#afa',
                data: volUp
            }, {
                type: 'bar',
                label: 'sold',
                backgroundColor: '#faa',
                data: volDown
            }]
        }
    }
}

const chartData = new VolumeChartData([], 0)

export default makeChartComponent(Bar, {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
        xAxes: [{
            type: 'time',
            distribution: 'series',
            stacked: true
        }]
    }
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

