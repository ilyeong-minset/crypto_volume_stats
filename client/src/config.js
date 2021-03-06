const host = process.env.VUE_APP_API_HOST 
    ? process.env.VUE_APP_API_HOST
    : window.location.host

export default {
    apiEndpoint: `http://${host}/api`,
    wsEndpoint: `ws://${host}/ws`,
    maxTrades: 100,
    localStorage: '75b9eeab-ad76-48d1-a006-47bf25775fec'
}

