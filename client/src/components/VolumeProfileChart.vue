<template>
    <div>
        <chart-options>
            <horizontal-field labelText="Start">
                <datetime
                    @click="updateMinMax"
                    type="datetime"
                    :auto="true"
                    :min-datetime="tsMin"
                    :max-datetime="dateEnd"
                    input-class="input is-small"
                    @close="updateTimeframe"
                    v-model="dateStart"/>
            </horizontal-field>
            <horizontal-field labelText="End">
                <datetime
                    @click="updateMinMax"
                    type="datetime"
                    :auto="true"
                    :min-datetime="dateStart"
                    :max-datetime="tsMax"
                    input-class="input is-small"
                    @close="updateTimeframe"
                    v-model="dateEnd"/>
            </horizontal-field>
            <horizontal-field>
                <button
                    class="button is-small"
                    @click="updateMinMax(true)">&gt;&gt;</button>
            </horizontal-field>
            <horizontal-field labelText="Frames">
                <input class="input is-small" v-model.number="frames">
            </horizontal-field>
        </chart-options>
        <horizontal-field>
            <button
                class="button is-small"
                @click="updateData">Load</button>
        </horizontal-field>
        <chart v-if="chartData !== null" :chart-data="chartData"/>
    </div>
</template>
<script>
import Vue from 'vue'
import { HorizontalBar } from 'vue-chartjs'
import { mixins } from 'vue-chartjs'
const { reactiveProp } = mixins
import { getVolumeProfileChart } from '../api'
import { Datetime } from 'vue-datetime'
import { DateTime } from 'luxon'
import 'vue-datetime/dist/vue-datetime.css'
import storage from '../storage'
import HorizontalField from './HorizontalField.vue'
import ChartOptions from './ChartOptions.vue'

let timeframe = storage.load('volumeProfileChart', 'timeframe', 3600)

const Chart = {
    extends: HorizontalBar,
    mixins: [reactiveProp],
    data: () => ({
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                xAxes: [{ stacked: true }],
                yAxes: [{ stacked: true }]
            }
        }
    }),
    mounted() {
        this.renderChart(this.chartData, this.options)
    }
}

export default {
    props: ['selected'],
    components: {
        Datetime, Chart, HorizontalField, ChartOptions
    },
    data: () => ({
        barCount: 30,
        frames: 20,
        data: [],
        dateStart: null,
        dateEnd: null,
        tsMin: null,
        tsMax: null,
        chartData: null
    }),
    methods: {
        updateMinMax(upd) {
            this.tsMax = new Date().toISOString()
            const tmax = DateTime.fromISO(this.tsMax).setZone('UTC')
            this.tsMin = tmax.minus({ days: 1 }).toISO()
            if (!this.dateEnd || upd)
                this.dateEnd = this.tsMax
            if (!this.dateStart || upd)
                this.dateStart = tmax.minus({ seconds: timeframe }).toISO()
        },
        async updateData() {
            try {
                this.data = await getVolumeProfileChart(
                    this.selected.pairIds,
                    new Date(this.dateStart).getTime(),
                    new Date(this.dateEnd).getTime(),
                    this.frames
                )
            } catch (e) {
                Vue.flashMessage(e)
                return
            }
            const labels = [],
                volUp = [],
                volDown = []
            for (const [s, e, up, down] of this.data) {
                labels.push(`${s.toFixed(0)} - ${e.toFixed(0)}`)
                volUp.push(up)
                volDown.push(down)
            }
            this.chartData = {
                labels,
                datasets: [{
                    label: 'bought',
                    backgroundColor: '#afa',
                    data: volUp
                }, {
                    label: 'sold',
                    backgroundColor: '#faa',
                    data: volDown
                }]
            }
        },
        updateTimeframe() {
            timeframe = Math.round(
                (new Date(this.dateEnd).getTime() - new Date(this.dateStart).getTime()) / 1000
            )
            storage.save('volumeProfileChart',
                'timeframe', timeframe)
        }
    },
    created() {
        this.updateMinMax()
    }
}
</script>
<style>
div.vdatetime {
    display: inline;
}
div.vdatetime > div {
    display: inline;
}
</style>

