import config from './config'

const getLs = () =>
    JSON.parse(window.localStorage.getItem(config.localStorage) || '{}')

export function saveItem(name, value) {
    const ls = getLs()
    ls[name] = value
    window.localStorage.setItem(config.localStorage,
        JSON.stringify(ls))
}

export function loadItem(name, def) {
    const ls = getLs()
    if (name in ls)
        return ls[name]
    else
        return def
}

