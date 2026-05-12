import request from "@/utils/request";
import axios from "axios";

const queryBaidu = (keyword) => {
    return {
        "k": "KEYWORD",
        "v": "KEYWORD EXPLAIN"
    }
    // return request.post("/api/baiduQuery", {
    //     keyword: keyword
    // });
};

const queryByKeyword = (keyword, langCode, game) => {
    return request.post("/api/keywordQuery", {
        keyword: keyword,
        langCode: langCode,
        game: game || "genshin"
    });
};

/**
 *
 * @param voicePath
 * @param langCode
 * @return {Promise<ArrayBuffer|null>}
 */
const getVoiceOver = async (voicePath, langCode, game) => {

    let ans = await axios.post(request.defaults.baseURL ? request.defaults.baseURL: "" + "api/getVoiceOver", {
        voicePath: voicePath,
        langCode: parseInt(langCode),
        game: game || "genshin"
    }, {
        responseType: 'arraybuffer',
    });

    if(ans.headers.has("Error")) {
        console.log("戳了")
        return null
    }

    return ans.data
};




const getTalkFromHash = (textHash, game) => {
    return request.post("/api/getTalkFromHash", {
        "textHash": textHash,
        "game": game || "genshin"
    });
};

export default {
    queryBaidu,
    queryByKeyword,
    getVoiceOver,
    getTalkFromHash
};