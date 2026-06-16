<template>
    <div class="viewWrapper">
        <h1 class="pageTitle">关键词检索</h1>
        <div class="helpText">
            <p>使用关键词对游戏的指定语言的文本进行检索。</p>
            <p>检索结果中,可能有对应配音的结果会被排序在前面。</p>
        </div>


        <el-input
            v-model="keyword"
            style="max-width: 600px;"
            placeholder="请输入关键词"
            class="input-with-select"
            @keyup.enter.native="onQueryButtonClicked"
            clearable
        >
            <template #prepend>
                <el-select v-model="selectedInputLanguage" placeholder="Select" class="languageSelector" >
                    <el-option v-for="(v,k) in supportedInputLanguage" :label="v" :value="k" :key="k"/>
                </el-select>
            </template>
            <template #append>
                <el-button :icon="Search" @click="onQueryButtonClicked"/>
            </template>
        </el-input>
        <el-switch
            v-model="wordSearchEnabled"
            active-text="单词搜索"
            inactive-text=""
            v-show="selectedInputLanguage === '4'"
            style="margin-left: 12px;"
            @change="onWordSearchChanged"
        />
        <span class="searchSummary">
            {{ searchSummary }}
        </span>

        <el-tabs v-model="activeResultTab" class="resultTabs">
            <el-tab-pane :label="`文本结果 (${queryResult.length})`" name="text">
                <p v-if="textSearchSummary" class="tabSummary">{{ textSearchSummary }}</p>
                <div>
                    <TranslateDisplay v-for="translate in queryResult" :key="`${translate.game}:${translate.hash}`" :translate-obj="translate" class="translate" @onVoicePlay="onVoicePlay" :keyword="keywordLast" />
                </div>
            </el-tab-pane>
            <el-tab-pane :label="`歌词结果 (${lyricsResult.length})`" name="lyrics">
                <p v-if="lyricsSearchSummary" class="tabSummary">{{ lyricsSearchSummary }}</p>
                <LyricsResultList :songs="lyricsResult" :keyword="keywordLast" :searched="lyricsSearched" />
            </el-tab-pane>
        </el-tabs>
    </div>

    <div class="viewWrapper voicePlayerContainer" v-show="showPlayer && queryResult.length > 0">
        <span class="hideIcon" @click="onHidePlayerButtonClicked">
            <el-icon>
                <Close />
            </el-icon>
        </span>

        <AudioPlayer

            ref="voicePlayer"
            :audio-list="audio"
            :show-prev-button="false"
            :show-next-button="false"
            :is-loop="false"
            :progress-interval="25"
            theme-color="var(--el-color-primary)">

        </AudioPlayer>
    </div>

    <div class="showPlayerButton" @click="onShowPlayerButtonClicked" v-show="!showPlayer && queryResult.length > 0">
        <i class="fi fi-sr-waveform-path"></i>
    </div>

</template>

<script setup>
import {onBeforeMount, ref, watch} from 'vue';
import {useRoute} from 'vue-router';
import {Close, Delete, Download, Plus, ZoomIn} from '@element-plus/icons-vue';
import { Search } from '@element-plus/icons-vue'
import global, {getStoredSearchLang, setStoredSearchLang} from "@/global/global"
import keywordApi from "@/api/keywordQuery"
import lyricsApi from "@/api/lyricsQuery"
import TranslateDisplay from "@/components/ResultEntry.vue";
import LyricsResultList from "@/components/LyricsResultList.vue";
import AudioPlayer from "@liripeng/vue-audio-player";

const queryLanguages = [1,4]
const route = useRoute()

const queryResult = ref([])
const lyricsResult = ref([])
const lyricsSearched = ref(false)
const activeResultTab = ref(route.query.tab === 'lyrics' ? 'lyrics' : 'text')
const textSearchSummary = ref("")
const lyricsSearchSummary = ref("")


const getSearchLanguage = () => {
    let stored = getStoredSearchLang()
    if (stored !== null) return stored
    let firstGame = global.currentGame[0] || "genshin"
    return (global.config[firstGame]?.defaultSearchLanguage ?? 4) + ''
}

const selectedInputLanguage = ref(getSearchLanguage())
const keyword = ref("")
const keywordLast = ref("")
const supportedInputLanguage = ref({})
const searchSummary = ref("")
const wordSearchEnabled = ref(localStorage.getItem('wordSearchEnabled') === 'true')

onBeforeMount(async ()=>{
    supportedInputLanguage.value = global.languages
    selectedInputLanguage.value = getSearchLanguage()
})

watch(() => global.currentGame, async (newGames) => {
    querySeq++
    selectedInputLanguage.value = getSearchLanguage()
    queryResult.value = []
    lyricsResult.value = []
    lyricsSearched.value = false
    searchSummary.value = ""
    textSearchSummary.value = ""
    lyricsSearchSummary.value = ""
}, {deep: true})

watch(() => global.languages, async (newLangs) => {
    supportedInputLanguage.value = newLangs
    selectedInputLanguage.value = getSearchLanguage()
}, {deep: true})

watch(selectedInputLanguage, (newLang) => {
    setStoredSearchLang(newLang)
})

watch(() => route.query.tab, (tab) => {
    if(tab === 'lyrics' || tab === 'text') activeResultTab.value = tab
})

const onWordSearchChanged = (val) => {
    localStorage.setItem('wordSearchEnabled', val)
}

const escapeRegExp = (text) => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

const hasExactWordMatch = (item, searchText) => {
    if(!searchText.trim()) return false
    let pattern = new RegExp(`\\b${escapeRegExp(searchText.trim())}\\b`, 'i')
    return Object.values(item.translates).some(text => typeof text === 'string' && pattern.test(text))
}

const searchLyricsForGames = async (searchText, games) => {
    let results = await Promise.allSettled(games.map(game =>
        lyricsApi.searchLyrics(searchText, game).then(response => ({game, ans: response.json}))
    ))
    let allContents = []
    let totalTime = 0
    let failedCount = 0
    for (let result of results) {
        if(result.status !== 'fulfilled'){
            failedCount++
            continue
        }
        let {game, ans} = result.value
        totalTime += ans.time
        for(let song of ans.contents){
            song.game = song.game || game
            allContents.push(song)
        }
    }

    let songMap = new Map()
    for(let song of allContents){
        let key = `${song.game}:${song.title}:${song.album || ''}`
        if(!songMap.has(key)) songMap.set(key, song)
    }

    return {
        contents: Array.from(songMap.values()),
        time: totalTime,
        failedCount
    }
}

/**
 *
 * @type {Ref<AudioPlayer>}
 */
const voicePlayer = ref()
const showPlayer = ref(false)
let firstShowPlayer = true
let querySeq = 0

const onQueryButtonClicked = async () =>{
    let searchText = keyword.value.trim()
    if (!searchText) {
        searchSummary.value = "请输入搜索关键词。"
        textSearchSummary.value = ""
        lyricsSearchSummary.value = ""
        queryResult.value = []
        lyricsResult.value = []
        lyricsSearched.value = false
        return
    }

    if (global.currentGame.length === 0) {
        searchSummary.value = "请至少选择一个游戏。"
        textSearchSummary.value = ""
        lyricsSearchSummary.value = ""
        queryResult.value = []
        lyricsResult.value = []
        lyricsSearched.value = false
        return
    }

    try {
        voicePlayer.value.pause()
    } catch(e) {}

    let currentSeq = ++querySeq
    let games = [...global.currentGame]
    let gameNames = global.availableGames

    let textSearchPromise = Promise.allSettled(games.map(game =>
        keywordApi.queryByKeyword(searchText, selectedInputLanguage.value, game, wordSearchEnabled.value)
            .then(response => ({game, ans: response.json}))
    ))
    let lyricsSearchPromise = searchLyricsForGames(searchText, games)

    let [textSearchResult, lyricsSearchResult] = await Promise.allSettled([textSearchPromise, lyricsSearchPromise])
    if(currentSeq !== querySeq) return

    let allContents = []
    let totalTime = 0
    if(textSearchResult.status === 'fulfilled'){
        for (let result of textSearchResult.value) {
            if(result.status !== 'fulfilled') continue
            let {game, ans} = result.value
            totalTime += ans.time
            for (let item of ans.contents) {
                item.game = game
                item.gameName = gameNames[game] || game
                allContents.push(item)
            }
        }
    }

    let mergedCount = 0
    let resultMap = new Map()
    for(let item of allContents){
        let key = item.hash + "|" + item.game
        if(!resultMap.has(key)){
            resultMap.set(key, item)
            continue
        }
        mergedCount++
        let oldItem = resultMap.get(key)
        oldItem.voicePaths = [...new Set([...(oldItem.voicePaths || []), ...(item.voicePaths || [])])]
    }

    let allEntries = []
    resultMap.forEach((item, key, _)=>{
        item._exactWordMatch = wordSearchEnabled.value && selectedInputLanguage.value === '4' && hasExactWordMatch(item, searchText) ? 1 : 0
        item._hasVoice = item.voicePaths.length > 0 ? 1 : 0
        allEntries.push(item)
    })

    allEntries.sort((a, b) => {
        if (a._exactWordMatch !== b._exactWordMatch) return b._exactWordMatch - a._exactWordMatch
        if (a._hasVoice !== b._hasVoice) return b._hasVoice - a._hasVoice
        return 0
    })

    queryResult.value = allEntries

    let textSummary = `文本查询用时: ${totalTime.toFixed(2)}ms，`
    if(queryResult.value.length > 0){
        textSummary += allContents.length >= 200 ? `共 ≥200 条结果` : `共 ${queryResult.value.length} 条结果`
        if(mergedCount > 0) textSummary += `，已合并 ${mergedCount} 条重复结果。`
        else textSummary += '。'
    }else{
        textSummary += `没有找到结果。`
    }
    textSearchSummary.value = textSummary

    if(lyricsSearchResult.status === 'fulfilled'){
        lyricsResult.value = lyricsSearchResult.value.contents
        lyricsSearched.value = true
        let lyricsSummary = `歌词查询用时: ${lyricsSearchResult.value.time.toFixed(2)}ms，`
        lyricsSummary += lyricsResult.value.length > 0 ? `共 ${lyricsResult.value.length} 首歌曲。` : `没有找到结果。`
        if(lyricsSearchResult.value.failedCount > 0) lyricsSummary += ` 部分游戏歌词查询失败。`
        lyricsSearchSummary.value = lyricsSummary
    }else{
        lyricsResult.value = []
        lyricsSearched.value = true
        lyricsSearchSummary.value = "歌词查询失败。"
    }

    keywordLast.value = searchText
    searchSummary.value = `文本 ${queryResult.value.length} 条，歌词 ${lyricsResult.value.length} 首。`
    if(queryResult.value.length === 0 && lyricsResult.value.length > 0){
        activeResultTab.value = 'lyrics'
    }
}

// 播放器相关开始
const audio = ref([])



const onHidePlayerButtonClicked = () => {
    showPlayer.value = false
}

const onShowPlayerButtonClicked = () => {
    showPlayer.value = true
}

const onVoicePlay = (voiceUrl) => {
    if(firstShowPlayer){
        showPlayer.value = true;
        firstShowPlayer = false
    }

    if(audio.value.length > 0 && voiceUrl === audio.value[0]){
        if(voicePlayer.value.isPlaying){
            voicePlayer.value.pause()
        }else{
            voicePlayer.value.play()
        }

    }else{
        audio.value = [voiceUrl]
        // 要等一会才能播放
        setTimeout(()=>{
            voicePlayer.value.play()
        }, 0)

    }

}


</script>

<style scoped>
.viewWrapper{
    position: relative;
    width: 85%;
    margin: 0 auto;
    background-color: #fff;
    box-shadow: 0 3px 3px rgba(36,37,38,.05);
    border-radius: 3px;
    padding: 20px;
}

.languageSelector{
    width: 120px;
}

.languageSelector:deep(input){
    text-align: center;
}
.translate:not(:last-child){
    border-bottom: 1px solid #ccc;
}

.voicePlayerContainer {
    margin-top: 10px;
    bottom: 0;
    position: sticky !important;
    box-shadow: 0 0 5px 5px rgba(36,37,38,.05);
}

.showPlayerButton{
    position: absolute;
    right: 7.5%;
    bottom: 80px;
    height: 70px;
    width: 70px;
    border-radius: 50%;
    background-color: var(--el-color-primary);
    color: #fff;
    font-size: 25px;
    box-shadow: 0 6px 15px rgba(36,37,38,.2);
    text-align: center;
    line-height: 75px;
    cursor: pointer;
}

.showPlayerButton:hover{
    background-color: var(--el-color-primary-light-3);
}

.hideIcon {
    cursor: pointer;
    position: absolute;
    top: 10px;
    right: 10px;
}

.hideIcon:hover {
    color: #888;
}

.pageTitle {
    border-bottom: 1px #ccc solid;
    padding-bottom: 10px;
}

.helpText {
    margin: 20px 0 20px 0;
    color: #999;
}

.searchSummary{
    margin-left: 10px;
    color: var(--el-input-text-color, var(--el-text-color-regular));
    font-size: 14px;
}

.resultTabs {
    margin-top: 20px;
}

.tabSummary {
    color: var(--el-text-color-regular);
    font-size: 14px;
    margin: 0 0 10px 0;
}

</style>
