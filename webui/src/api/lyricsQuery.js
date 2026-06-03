import request from "@/utils/request";

const searchLyrics = (keyword, game) => {
    return request.post("/api/lyricsSearch", {
        keyword: keyword,
        game: game || null
    });
};

const getLyricsSongs = (game) => {
    return request.get("/api/getLyricsSongs", { params: { game: game || null } });
};

const getLyricsDetail = (title, game) => {
    return request.post("/api/getLyricsDetail", {
        title: title,
        game: game || null
    });
};

const reloadLyricsData = () => {
    return request.post("/api/reloadLyricsData");
};

export default {
    searchLyrics,
    getLyricsSongs,
    getLyricsDetail,
    reloadLyricsData
};
