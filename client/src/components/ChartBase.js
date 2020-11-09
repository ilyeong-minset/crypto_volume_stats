import Vue from 'vue'
import { mixins } from 'vue-chartjs'
const { reactiveProp } = mixins

export default (base, options) => {
    const Chart = {
        extends: base,
        mixins: [reactiveProp],
        data: () => ({ options }),
        mounted() {
            this.renderChart(this.chartData, this.options)
        }
    }
    return Vue.extend({
        components: { Chart },
        props: ['selected'],
        data: () => ({
            chartData: {},
            updateIntervalID: 0
        }),
        template: '<chart :chart-data="chartData"/>',
        methods: {
            setUpdater() {
                this.clearUpdater()
                if (this.selected.timeframe > 0) {
                    this.updateIntervalID = setInterval(() => this._updateData(),
                        this.selected.timeframe * 500)
                }
            },
            clearUpdater() {
                if (this.updateIntervalID > 0) {
                    clearInterval(this.updateIntervalID)
                    this.updateIntervalID = 0
                }
            },
            async _updateData() {
                if (this.selected.pairIds.length > 0) {
                    await this.updateData()
                } else {
                    this.chartData = { datasets: [] }
                }
            }
        },
        watch: {
            async selected() {
                this.setUpdater()
                await this._updateData()
            }
        },
        async mounted() {
            this.setUpdater()
            await this._updateData()
        },
        destroyed() {
            this.clearUpdater()
        }
    })
}

