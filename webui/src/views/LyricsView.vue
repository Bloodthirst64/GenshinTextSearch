<template>
    <div class="viewWrapper">
        <h1 class="pageTitle">歌词检索</h1>
        <div class="helpText">
            <p>搜索米哈游旗下游戏（原神、崩坏：星穹铁道等）中带歌词的歌曲。</p>
            <p>支持按歌名、歌词内容、歌手、专辑等关键词搜索。</p>
        </div>

        <el-input
            v-model="keyword"
            style="max-width: 600px;"
            placeholder="输入关键词搜索歌词"
            class="input-with-select"
            @keyup.enter.native="onSearchButtonClicked"
            clearable
        >
            <template #prepend>
                <el-select v-model="selectedGame" placeholder="游戏" class="gameSelector">
                    <el-option label="全部" :value="null" />
                    <el-option v-for="(name, key) in gameOptions" :label="name" :value="key" :key="key" />
                </el-select>
            </template>
            <template #append>
                <el-button :icon="Search" @click="onSearchButtonClicked"/>
            </template>
        </el-input>
        <span class="searchSummary">
            {{ searchSummary }}
        </span>

        <div v-if="queryResult.length > 0" class="resultsContainer">
            <div v-for="song in queryResult" :key="song.title + song.game" class="songCard" @click="onSongCardClick(song)">
                <div class="songHeader">
                    <el-tag v-if="song.game" :type="song.game === 'starrail' ? 'warning' : ''" size="small" class="gameTag">
                        {{ gameOptions[song.game] || song.game }}
                    </el-tag>
                    <span class="songTitle">{{ song.title }}</span>
                    <span v-if="song.singer" class="songSinger">{{ song.singer }}</span>
                    <span v-if="song.album" class="songAlbum">{{ song.album }}</span>
                </div>
                <div v-if="song.matchedLines && song.matchedLines.length > 0" class="matchedLines">
                    <p v-for="line in song.matchedLines" class="matchedLine">
                        <StylizedText :text="line" :keyword="keywordLast" />
                    </p>
                </div>
            </div>
        </div>

        <el-empty v-if="searched && queryResult.length === 0" description="没有找到匹配的歌词" />
    </div>

    <el-dialog v-model="showDetail" :title="detailSong?.title || ''" width="700px" top="5vh">
        <div v-if="detailSong" class="detailContent">
            <div class="detailMeta">
                <el-tag v-if="detailSong.game" :type="detailSong.game === 'starrail' ? 'warning' : ''" size="small">
                    {{ gameOptions[detailSong.game] || detailSong.game }}
                </el-tag>
                <span v-if="detailSong.album" class="metaItem">专辑：{{ detailSong.album }}</span>
                <span v-if="detailSong.singer" class="metaItem">歌手：{{ detailSong.singer }}</span>
                <span v-if="detailSong.composer" class="metaItem">作曲：{{ detailSong.composer }}</span>
                <span v-if="detailSong.lyricist" class="metaItem">作词：{{ detailSong.lyricist }}</span>
            </div>
            <div class="lyricsContent">
                <p v-for="line in detailSongLyrics" class="lyricsLine" :class="{ highlightLine: keywordLast && line.toLowerCase().includes(keywordLast.toLowerCase()) }">
                    <StylizedText :text="line" :keyword="keywordLast" />
                </p>
            </div>
        </div>
    </el-dialog>
</template>

<script setup>
import {ref, computed} from 'vue';
import {Search} from '@element-plus/icons-vue';
import global from "@/global/global";
import api from "@/api/lyricsQuery";
import StylizedText from "@/components/StylizedText.vue";

const keyword = ref("")
const keywordLast = ref("")
const selectedGame = ref(null)
const queryResult = ref([])
const searchSummary = ref("")
const searched = ref(false)
const showDetail = ref(false)
const detailSong = ref(null)

const gameOptions = {
    "genshin": "原神",
    "starrail": "崩坏：星穹铁道"
}

const detailSongLyrics = computed(() => {
    if (!detailSong.value || !detailSong.value.lyrics) return []
    return detailSong.value.lyrics.split("\n")
})

const onSearchButtonClicked = async () => {
    if (!keyword.value.trim()) {
        searchSummary.value = "请输入搜索关键词。"
        queryResult.value = []
        return
    }

    let allContents = []
    let totalTime = 0

    try {
        let game = selectedGame.value
        if (!game && global.currentGame.length === 1) {
            game = global.currentGame[0]
        }

        let ans = (await api.searchLyrics(keyword.value, game)).json
        totalTime += ans.time
        allContents = ans.contents
    } catch (err) {
        if (!err.network) err.defaultHandler()
        return
    }

    let searchSummaryTmp = `查询用时: ${totalTime.toFixed(2)}ms，`
    if (allContents.length > 0) {
        searchSummaryTmp += `共 ${allContents.length} 首歌曲`
    } else {
        searchSummaryTmp += `没有找到结果。`
        searchSummary.value = searchSummaryTmp
        queryResult.value = []
        searched.value = true
        return
    }

    searchSummaryTmp += '。'
    searchSummary.value = searchSummaryTmp
    queryResult.value = allContents
    keywordLast.value = keyword.value
    searched.value = true
}

const onSongCardClick = (song) => {
    detailSong.value = song
    showDetail.value = true
}
</script>

<style scoped>
.viewWrapper {
    position: relative;
    width: 85%;
    margin: 0 auto;
    background-color: #fff;
    box-shadow: 0 3px 3px rgba(36, 37, 38, .05);
    border-radius: 3px;
    padding: 20px;
}

.pageTitle {
    border-bottom: 1px #ccc solid;
    padding-bottom: 10px;
}

.helpText {
    margin: 20px 0 20px 0;
    color: #999;
}

.gameSelector {
    width: 160px;
}

.gameSelector:deep(input) {
    text-align: center;
}

.searchSummary {
    margin-left: 10px;
    color: var(--el-input-text-color, var(--el-text-color-regular));
    font-size: 14px;
}

.resultsContainer {
    margin-top: 20px;
}

.songCard {
    padding: 16px 20px;
    border-bottom: 1px solid #eee;
    cursor: pointer;
    transition: background-color 0.2s;
}

.songCard:hover {
    background-color: var(--el-color-primary-light-9);
}

.songCard:last-child {
    border-bottom: none;
}

.songHeader {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}

.songTitle {
    font-size: 16px;
    font-weight: 500;
    color: var(--el-text-color-primary);
}

.songSinger {
    font-size: 13px;
    color: var(--el-color-primary);
}

.songAlbum {
    font-size: 13px;
    color: #999;
}

.gameTag {
    vertical-align: middle;
}

.matchedLines {
    margin-top: 8px;
    padding-left: 12px;
    border-left: 3px solid var(--el-color-primary-light-5);
}

.matchedLine {
    font-size: 14px;
    color: #666;
    line-height: 1.6;
    margin: 2px 0;
}

.detailContent {
    max-height: 70vh;
    overflow-y: auto;
}

.detailMeta {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid #eee;
}

.metaItem {
    font-size: 13px;
    color: #666;
}

.lyricsContent {
    white-space: pre-wrap;
}

.lyricsLine {
    font-size: 15px;
    line-height: 1.8;
    margin: 0;
    padding: 2px 4px;
    border-radius: 3px;
}

.highlightLine {
    background-color: var(--el-color-primary-light-9);
}
</style>
