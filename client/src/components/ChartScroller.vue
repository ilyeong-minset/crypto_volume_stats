<template>
    <div class="chart-scroller field is-grouped">
        <p class="control">
            <button
                class="button is-small"
                @click="scrollLeft">
                <i class="fas fa-step-backward"></i>
            </button>
        </p>
        <p class="control">
            <button
                class="button is-small"
                :disabled="offset === 0"
                @click="scrollRight">
                <i class="fas fa-step-forward"></i>
            </button>
        </p>
        <p class="control">
            <button
                class="button is-small"
                :disabled="offset === 0"
                @click="scrollReset">
                <i class="fas fa-fast-forward"></i>
            </button>
        </p>
        <p class="control">
            <button
                class="button is-small"
                :disabled="barCount >= barCountMax"
                @click="inc">
                <i class="fas fa-search-minus"></i>
            </button>
        </p>
        <p class="control">
            <button
                class="button is-small"
                :disabled="barCount <= barCountInc"
                @click="dec">
                <i class="fas fa-search-plus"></i>
            </button>
        </p>
        <p class="control">
            <button
                class="button is-small"
                :disabled="barCount <= barCountInc"
                @click="reload">
                <i class="fas fa-sync"></i>
            </button>
        </p>
    </div>
</template>
<script>
import { loadItem, saveItem } from '../storage'

const barCountMax = 100,
    barCountInc = 10
let barCount = loadItem('chartBarCount', 40)
let offset = 0
const updaters = []

const updateValue = () => {
    saveItem('chartBarCount', barCount)
    saveItem('chartOffset', offset)
    for (const x of updaters)
        x()
}

export default {
    props: ['value'],
    data: () => ({
        updater: null,
        barCount,
        barCountMax,
        barCountInc,
        offset
    }),
    methods: {
        inc() {
            barCount = Math.min(barCountMax, barCount + barCountInc)
            updateValue()
        },
        dec() {
            barCount = Math.max(0, barCount - barCountInc)
            updateValue()
        },
        scrollLeft() {
            offset += Math.round(barCount / 10)
            updateValue()
        },
        scrollRight() {
            offset -= Math.round(barCount / 10)
            updateValue()
        },
        scrollReset() {
            offset = 0
            updateValue()
        },
        reload() {
            this.$emit('reload')
        },
        updateValue() {
            if (this.barCount === barCount
                && this.offset === offset)
                return
            this.barCount = barCount
            this.offset = offset
            this.$emit('input', { barCount, offset })
            this.$emit('change')
        }
    },
    created() {
        this.updater = () => this.updateValue()
        updaters.push(this.updater)
        this.barCount = barCount
        this.offset = offset
        this.$emit('input', { barCount, offset })
    },
    destroyed() {
        updaters.splice(updaters.indexOf(this.updater), 1)
    }
}
</script>
<style>
.chart-scroller {
    margin: 5px;
}
</style>

