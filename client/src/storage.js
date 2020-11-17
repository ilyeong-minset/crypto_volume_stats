import config from './config'

const getLs = () =>
    JSON.parse(window.localStorage.getItem(config.localStorage) || '{}')

const saveLs = x =>
    window.localStorage.setItem(config.localStorage, JSON.stringify(x))

export default {
    load(nameSpace, name, def) {
        const ls = getLs()
        if (nameSpace in ls && name in ls[nameSpace])
            return ls[nameSpace][name]
        else
            return def
    },
    save(nameSpace, name, value) {
        const ls = getLs()
        if (!(nameSpace in ls))
            ls[nameSpace] = {}
        ls[nameSpace][name] = value
        saveLs(ls)
    },
    loadItems(nameSpace, items) {
        const ls = getLs()
        if (!(nameSpace in ls))
            return items
        else {
            const res = {},
                ns = ls[nameSpace]
            for (const k in items)
                res[k] = k in ns ? ns[k] : items[k]
            return res
        }
    },
    saveItems(nameSpace, items) {
        const ls = getLs()
        if (!(nameSpace in ls))
            ls[nameSpace] = {}
        for (const k in items)
            ls[nameSpace][k] = items[k]
        saveLs(ls)
    }
}

