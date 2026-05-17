import {reactive, watch} from 'vue'

const STORAGE_KEY_GAME = 'genshinTextSearch_currentGame'
const STORAGE_KEY_SEARCH_LANG = 'genshinTextSearch_searchLang'

function loadFromStorage(key, fallback) {
    try {
        const stored = localStorage.getItem(key)
        if (stored !== null) return JSON.parse(stored)
    } catch (e) {}
    return fallback
}

function saveToStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value))
    } catch (e) {}
}

const global = reactive({
    languages: {},
    voiceLanguages: {},
    config: {},
    availableGames: {},
    currentGame: loadFromStorage(STORAGE_KEY_GAME, ["genshin"])
})

watch(() => global.currentGame, (newVal) => {
    saveToStorage(STORAGE_KEY_GAME, newVal)
}, { deep: true })

export function getStoredSearchLang() {
    return loadFromStorage(STORAGE_KEY_SEARCH_LANG, null)
}

export function setStoredSearchLang(lang) {
    saveToStorage(STORAGE_KEY_SEARCH_LANG, lang)
}

export default global
