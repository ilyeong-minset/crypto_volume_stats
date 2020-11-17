<template>
    <div>
        <div class="content is-large">
            <div v-if="loading">Loading...</div>
            <div v-if="!loading">
                {{selected.pair}}
                <button
                    class="button"
                    @click="updateData">
                    <i class="fas fa-sync"></i>
                </button>
            </div>
        </div>
        <chart-options>
            <horizontal-field labelText="Update interval (seconds)">
                <input
                    type="number"
                    class="input is-small"
                    v-model.number="updateInterval" @change="setUpdateInterval()">
            </horizontal-field>
        </chart-options>
        <table v-if="summary" class="table is-striped is-fullwidth is-hoverable">
            <tbody>
                <tr v-for="x in fieldNames"
                    :key="x[0]">
                    <td>{{x[1]}}</td>
                    <td>{{formatValue(summary[x[0]])}}</td>
                </tr>
            </tbody>
        </table>
        <p
            class="content is-small"
            v-if="updated && summary">Updated: {{updated}}</p>
    </div>
</template>
<script>
import Vue from 'vue'
import { getSummary } from '../api'
import storage from '../storage'
import HorizontalField from './HorizontalField.vue'
import ChartOptions from './ChartOptions.vue'

export default {
    components: { HorizontalField, ChartOptions },
    props: ['selected'],
    data: () => ({
        loading: false,
        summary: null,
        fieldNames: [
            ['firstp', 'First'],
            ['lastp', 'Last'],
            ['lowp', 'Low'],
            ['highp', 'High'],
            ['avgp', 'Average'],
            ['wavgp', 'Weighted AVG'],
            ['ntrades', '# trades'],
            ['vol', 'Total volume'],
            ['volup', 'Bought'],
            ['voldown', 'Sold']
        ],
        updated: null,
        updateIntervalID: 0,
        updateInterval: storage.load('summaryTable', 'interval', 60)
    }),
    methods: {
        async updateData() {
            if (this.selected.pairIds.length > 0 && this.selected.timeframe > 0) {
                this.loading = true
                try {
                    this.summary = await getSummary(
                        this.selected.pairIds,
                        this.selected.timeframe
                    )
                } catch (e) {
                    Vue.flashMessage(e)
                    this.summary = null
                }
                this.loading = false
                this.updated = new Date().toLocaleTimeString()
            } else {
                this.summary = null
            }
        },
        setUpdateInterval() {
            storage.save('summaryTable', 'interval', this.updateInterval)
            if (this.updateIntervalID > 0)
                clearInterval(this.updateIntervalID)
            this.updateIntervalID = setInterval(() => this.updateData(),
                1000 * this.updateInterval)
        },
        formatValue: x => (x === Math.round(x)
            ? x
            : (x > 1 ? x.toFixed(2) : x.toFixed(8)))
    },
    watch: {
        async selected() {
            await this.updateData()
        }
    },
    async created() {
        await this.updateData()
        this.setUpdateInterval()
    },
    destroyed() {
        if (this.updateIntervalID > 0)
            clearInterval(this.updateIntervalID)
    }
}
</script>
