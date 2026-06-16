<template>
    <div v-if="songs.length > 0" class="resultsContainer">
        <div v-for="song in songs" :key="`${song.game}:${song.title}:${song.album || ''}`" class="songCard" @click="onSongCardClick(song)">
            <div class="songHeader">
                <el-tag v-if="song.game" :type="song.game === 'starrail' ? 'warning' : ''" size="small" class="gameTag">
                    {{ gameName(song.game) }}
                </el-tag>
                <span class="songTitle">{{ song.title }}</span>
                <span v-if="song.singer" class="songSinger">{{ song.singer }}</span>
                <span v-if="song.album" class="songAlbum">{{ song.album }}</span>
            </div>
            <div v-if="song.matchedLines && song.matchedLines.length > 0" class="matchedLines">
                <p v-for="line in song.matchedLines" :key="line" class="matchedLine">
                    <StylizedText :text="line" :keyword="keyword" />
                </p>
            </div>
        </div>
    </div>

    <el-empty v-if="searched && songs.length === 0" :description="emptyDescription" />

    <el-dialog v-model="showDetail" :title="detailSong?.title || ''" width="700px" top="5vh">
        <div v-if="detailSong" class="detailContent">
            <div class="detailMeta">
                <el-tag v-if="detailSong.game" :type="detailSong.game === 'starrail' ? 'warning' : ''" size="small">
                    {{ gameName(detailSong.game) }}
                </el-tag>
                <span v-if="detailSong.album" class="metaItem">专辑：{{ detailSong.album }}</span>
                <span v-if="detailSong.singer" class="metaItem">歌手：{{ detailSong.singer }}</span>
                <span v-if="detailSong.composer" class="metaItem">作曲：{{ detailSong.composer }}</span>
                <span v-if="detailSong.lyricist" class="metaItem">作词：{{ detailSong.lyricist }}</span>
            </div>
            <div class="lyricsContent">
                <p v-for="line in detailSongLyrics" :key="line" class="lyricsLine" :class="{ highlightLine: keyword && line.toLowerCase().includes(keyword.toLowerCase()) }">
                    <StylizedText :text="line" :keyword="keyword" />
                </p>
            </div>
        </div>
    </el-dialog>
</template>

<script setup>
import {computed, ref} from 'vue';
import global from "@/global/global";
import StylizedText from "@/components/StylizedText.vue";

const props = defineProps({
    songs: {
        type: Array,
        default: () => []
    },
    keyword: {
        type: String,
        default: ""
    },
    searched: {
        type: Boolean,
        default: false
    },
    emptyDescription: {
        type: String,
        default: "没有找到匹配的歌词"
    }
})

const showDetail = ref(false)
const detailSong = ref(null)

const fallbackGameOptions = {
    "genshin": "原神",
    "starrail": "崩坏：星穹铁道"
}

const detailSongLyrics = computed(() => {
    if (!detailSong.value || !detailSong.value.lyrics) return []
    return detailSong.value.lyrics.split("\n")
})

const gameName = (game) => global.availableGames[game] || fallbackGameOptions[game] || game

const onSongCardClick = (song) => {
    detailSong.value = song
    showDetail.value = true
}
</script>

<style scoped>
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
