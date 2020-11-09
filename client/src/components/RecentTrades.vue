<template>
    <div>
        <div class="recent-trades-container">
            <table class="table is-fullwidth">
                <thead>
                    <th>Time</th>
                    <th>Exchange</th>
                    <th>Amount</th>
                    <th>Price</th>
                </thead>
                <tbody>
                    <tr v-for="x in trades"
                        :key="x.id"
                        :class="x.className">
                        <td>{{x.timeString}}</td>
                        <td>{{pairs[x.pair].ex}}</td>
                        <td>{{x.amount}}</td>
                        <td>{{x.price}}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>
<script>
import Vue from 'vue'
import {
    subscribe, unsubscribe, getPairsDict, setTradeCallback
} from '../api'
import config from '../config'

export default {
    props: ['selected'],
    data: () => ({
        tradeCount: 0,
        trades: [],
        pairs: null
    }),
    watch: {
        selected(newSelected, oldSelected) {
            const toSub = [],
                toUnsub = []
            for (const id of newSelected.pairIds) {
                if (oldSelected.pairIds.indexOf(id) < 0)
                    toSub.push(id)
            }
            for (const id of oldSelected.pairIds) {
                if (newSelected.pairIds.indexOf(id) < 0)
                    toUnsub.push(id)
            }
            if (toSub.length > 0)
                subscribe(toSub)
            if (toUnsub.length > 0)
                unsubscribe(toUnsub)
        }
    },
    async created() {
        setTradeCallback(trade => {
            trade.id = this.tradeCount
            trade.timeString =
                new Date(trade.timestamp).toLocaleTimeString()
            trade.className = trade.amount > 0 ? 'trade-bought' : 'trade-sold'
            trade.amount = Math.abs(trade.amount)
            this.tradeCount++
            this.trades.unshift(trade)
            if (this.trades.length > config.maxTrades)
                this.trades.pop()
        })
        try {
            this.pairs = await getPairsDict()
        } catch (e) {
            Vue.flashMessage(e)
        }
        if (this.selected.pairIds.length > 0)
            subscribe(this.selected.pairIds)
    },
    destroyed() {
        unsubscribe()
        setTradeCallback(null)
    }
}
</script>
<style>
.trade-bought {
    background-color: #afa;
}
.trade-sold {
    background-color: #faa;
}
.recent-trades-container {
    height: 60vh;
    overflow-y: scroll;
    font-size: smaller;
}
</style>

