<template>
    <div class="field is-horizontal">
        <div class="field-label is-small">
            <label class="label">
                {{labelText}}
            </label>
        </div>
        <div class="field-body">
            <div class="field">
                <p class="control">
                <slot></slot>
                </p>
            </div>
        </div>
    </div>
</template>
<script>
export default {
    props: ['labelText']
}
</script>
