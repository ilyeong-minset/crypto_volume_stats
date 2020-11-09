<template>
    <div class="chart-options">
        <span
            class="chart-options-title"
            @click="toggle">Options</span>
        <div v-if="enabled">
            <slot></slot>
        </div>
    </div>
</template>
<script>
export default {
    data: () => ({
        enabled: false
    }),
    methods: {
        toggle() {
            this.enabled = !this.enabled
        }
    }
}
</script>
<style>
.chart-options-title {
    border-bottom: 1px dashed;
    font-size: smaller;
}
.chart-options-title:hover {
    cursor: pointer;
}
.chart-options {
    padding: 5px;
}
</style>
