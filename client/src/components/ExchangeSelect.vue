<template>
    <div class="exchange-select">
        <div class="select is-small">
            <select
                v-model.number="selectedTimeframe"
                @change="updateValue()">
                <option
                    v-for="x in timeframes"
                    :key="x[0]"
                    :value="x[0]">{{x[1]}}</option>
            </select>
        </div>
        <div class="select is-small">
            <select
                v-model="selectedPair"
                @change="updateValue(true)">
                <option v-for="x in pairList" :key="x">{{x}}</option>
            </select>
        </div>
        <div class="exchange-menu-container">
            <span class="exchange-menu-title">Exchanges</span>
            <div class="exchange-menu">
                <label
                    class="checkbox"
                    v-for="x in pairIdList"
                    :key="x.id">
                    <input
                        type="checkbox"
                        v-model.number="selectedPairIds"
                        :value="x.id"
                        @change="updateValue()">
                    {{x.ex}}
                </label>
                <div class="field is-grouped is-grouped-centered">
                    <p class="control">
                        <button
                            class="button is-small"
                            @click="selectAll">All</button>
                    </p>
                    <p class="control">
                        <button
                            class="button is-small"
                            @click="updateValue(true)">None</button>
                    </p>
                </div>
            </div>
        </div>
    </div>
</template>
<script>
import Vue from 'vue'
import { getPairs, getTimeframes } from '../api'
import { loadItem, saveItem } from '../storage'

function tfToString(x) {
    const tfs = [
        [86400, 'D'],
        [3600, 'H'],
        [60, 'M']
    ]
    for (const [d, n] of tfs) {
        if (x % d === 0) {
            return (x / d).toFixed(0) + n
        }
    }
    return x.toString()
}

export default {
    props: ['value', 'storageName'],
    data: () => ({
        pairs: {},
        selectedPair: '',
        selectedPairIds: [],
        timeframes: [],
        selectedTimeframe: 0
    }),
    methods: {
        updateValue(clear = false, save = true) {
            if (clear) {
                this.selectedPairIds = []
            }
            this.selectedPairIds.sort()
            const selected = {
                pair: this.selectedPair,
                pairIds: this.selectedPairIds,
                timeframe: this.selectedTimeframe
            }
            if (save)
                saveItem(`exchangeSelect${this.storageName}`,
                    selected)
            this.$emit('input', selected)
        },
        selectAll() {
            this.selectedPairIds = this.pairIdList.map(x => x.id)
            this.updateValue()
        }
    },
    computed: {
        pairList() {
            return Object.keys(this.pairs)
        },
        pairIdList() {
            if (this.selectedPair === '')
                return []
            else
                return this.pairs[this.selectedPair]
        }
    },
    async created() {
        try {
            this.pairs = await getPairs()
            this.timeframes = (await getTimeframes())
                .map(x => [x, tfToString(x)])
        } catch (e) {
            Vue.flashMessage(e)
            this.pairs = {}
            this.timeframes = []
        }
        const selected =
            loadItem(`exchangeSelect${this.storageName}`)
        if (selected) {
            this.selectedPair = selected.pair
            this.selectedPairIds = selected.pairIds
            this.selectedTimeframe = selected.timeframe
            this.updateValue(false, false)
        } else {
            this.selectedPair = this.pairList[0]
            this.selectedTimeframe = this.timeframes[0][0]
            this.updateValue()
        }
    }
}
</script>
<style>
.exchange-select {
    position: sticky;
    top: 0px;
    padding: 10px;
    background-color: white;
    z-index: 999;
    border-bottom: 1px solid lightgray;
}
.exchange-select > div {
    display: inline-block;
    margin: 0px 5px;
}
.exchange-menu-title {
    border-bottom: 1px dashed;
}
.exchange-menu-container {
    position: relative;
    display: inline-block;
}
.exchange-menu {
    display: none;
    position: absolute;
    padding: 5px 10px;
    /*min-width: 30ch;*/
    background-color: white;
    border: 1px dashed lightgray;
    white-space: nowrap;
}
.exchange-menu > button {
    margin: 5px 5px;
}
.exchange-menu-container:hover .exchange-menu {
    display: block;
}
.exchange-menu label {
    display: block;
}
.exchange-menu button {
    display: inline;
}
</style>

