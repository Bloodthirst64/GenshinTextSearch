import request from "@/utils/request";

const getAvailableGames = () => {
    return request.get("/api/getAvailableGames");
}

const getImportedTextLanguages = (game) => {
    return request.get("/api/getImportedTextLanguages", { params: { game: game || "genshin" } });
};


const getImportedVoiceLanguages = (game) => {
    return request.get("/api/getImportedVoiceLanguages", { params: { game: game || "genshin" } });
}

const saveConfig = (perGameConfig) => {
    return request.post("/api/saveSettings", {
        'config': perGameConfig
    })
}

const getConfig = () => {
    return request.get("/api/getSettings")
}

export default {
    getAvailableGames,
    getImportedTextLanguages,
    getImportedVoiceLanguages,
    getConfig,
    saveConfig
}
