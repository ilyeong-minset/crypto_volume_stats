<template>
    <div class="wrapper">
        <div class="wrapper-title">
            <a href="#" @click="toggle();$event.preventDefault()">{{title}}</a>
        </div>
        <div v-if="visible" class="wrapper-body">
            <slot v-if="selected.pairIds.length"/>
            <div v-if="selected.pairIds.length === 0">
                Selecte some exchanges to view data
            </div>
        </div>
    </div>
</template>
<script>
import { loadItem, saveItem } from '../storage'

export default {
    props: ['title', 'selected'],
    data: () => ({
        visible: false,
        storageName: ''
    }),
    methods: {
        toggle() {
            this.visible = !this.visible
            saveItem(this.storageName, this.visible)
        }
    },
    created() {
        this.storageName = this.title.replace(' ', '_').toLowerCase()
        this.visible = loadItem(this.storageName, true)
    }
}
</script>
<style>
.wrapper {
    border: 1px solid lightgray;
    border-radius: 5px;
    padding: 8px;
    margin: 8px;
}
.wrapper-title {
    font-size: large;
}
.wrapper-body {
    margin-top: 15px;
}
</style>

