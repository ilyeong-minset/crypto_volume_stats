<template>
    <div>
        <exchange-select
            storageName=""
            v-model="selected"/>
        <wrapper title="Summary" :selected="selected">
            <summary-table :selected="selected"/>
        </wrapper>
        <wrapper title="Price chart" :selected="selected">
            <OHLCVChart :selected="selected"/>
        </wrapper>
        <wrapper title="Volume" :selected="selected">
            <volume-chart :selected="selected"/>
        </wrapper>
        <wrapper title="Volume profile" :selected="selected">
            <volume-profile-chart :selected="selected"/>
        </wrapper>
        <wrapper title="Recent trades" :selected="selected">
            <recent-trades :selected="selected"/>
        </wrapper>
        <flash-message/>
    </div>
</template>
<script>
import ExchangeSelect from './components/ExchangeSelect.vue'
import SummaryTable from './components/SummaryTable.vue'
import RecentTrades from './components/RecentTrades.vue'
import OHLCVChart from './components/OHLCChart.vue'
import VolumeChart from './components/VolumeChart.vue'
import VolumeProfileChart from './components/VolumeProfileChart.vue'
import Wrapper from './components/Wrapper.vue'
import Vue from 'vue'
import FlashMessage from './components/FlashMessage.vue'
import 'bulma/css/bulma.min.css'
import '@fortawesome/fontawesome-free/css/all.css'

Vue.use(FlashMessage.flashMessage)

export default {
    components: {
        Wrapper,
        ExchangeSelect,
        SummaryTable,
        RecentTrades,
        OHLCVChart,
        VolumeChart,
        VolumeProfileChart
    },
    data: () => ({
        selected: {
            timeframe: 0,
            pairIds: [],
            pair: ''
        }
    })
}
</script>

