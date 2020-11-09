<template>
    <div v-if="messages.length > 0" class="flash-message-container">
        <div v-for="(x, i) in messages" :key="i" class="flash-message">
            {{x.text}}
            <a href="#" style="float:right;" @click="close(x);$event.preventDefault()">Dismiss</a>
        </div>
    </div>
</template>
<script>
const messages = []

const removeMessage = x => {
    clearTimeout(x.timeout)
    const idx = messages.indexOf(x)
    if (idx >= 0)
        messages.splice(idx, 1)
}

const FlashMessage = {
    data: () => ({ messages }),
    methods: {
        close(x) {
            removeMessage(x)
        }
    }
}

FlashMessage.flashMessage = {
    install(Vue) {
        Vue.component('flash-message', FlashMessage)
        Vue.flashMessage = (x, timeout) => {
            const msg = {text: x}
            msg.timeout = setTimeout(() => removeMessage(msg),
                timeout || 5000)
            messages.push(msg)
        }
    }
}

export default FlashMessage
</script>
<style>
.flash-message-container {
    position: fixed;
    bottom: 0px;
}
.flash-message {
    margin: 5px;
    padding: 5px;
    background-color: white;
    border: 1px solid lightgray;
    width: 90vw;
    left: 25%;
}
</style>

