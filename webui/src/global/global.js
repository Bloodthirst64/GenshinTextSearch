import {reactive} from 'vue'

const global = reactive({
    languages: {},
    voiceLanguages: {},
    config: {},
    availableGames: {},
    currentGame: ["genshin"]
})

export default global
