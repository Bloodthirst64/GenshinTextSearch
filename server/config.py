import json
import os.path

GAME_CONFIG_DEFAULTS = {
    "genshin": {
        "assetDir": "",
        "isMale": False,
        "nickname": "旅行者",
        "sourceLanguage": 1,
        "defaultSearchLanguage": 4,
        "resultLanguages": [1, 4]
    },
    "starrail": {
        "assetDir": "",
        "isMale": False,
        "nickname": "开拓者",
        "sourceLanguage": 1,
        "defaultSearchLanguage": 4,
        "resultLanguages": [1, 4]
    }
}

config = {}

for _game, _defaults in GAME_CONFIG_DEFAULTS.items():
    config[_game] = dict(_defaults)


def loadConfig():
    if not os.path.isfile("config.json"):
        return
    fp = open("config.json", encoding='utf-8')
    fileJson = json.load(fp)
    fp.close()

    if "genshin" in fileJson and isinstance(fileJson["genshin"], dict):
        _load_game_config("genshin", fileJson["genshin"])
    if "starrail" in fileJson and isinstance(fileJson["starrail"], dict):
        _load_game_config("starrail", fileJson["starrail"])

    if "assetDir" in fileJson and isinstance(fileJson["assetDir"], str):
        config["genshin"]["assetDir"] = fileJson["assetDir"]

    if "starrailAssetDir" in fileJson and isinstance(fileJson["starrailAssetDir"], str):
        config["starrail"]["assetDir"] = fileJson["starrailAssetDir"]

    if "isMale" in fileJson and isinstance(fileJson["isMale"], bool):
        config["genshin"]["isMale"] = fileJson["isMale"]

    if "resultLanguages" in fileJson and isinstance(fileJson["resultLanguages"], list):
        for game in config:
            config[game]["resultLanguages"] = fileJson["resultLanguages"]

    if "defaultSearchLanguage" in fileJson and isinstance(fileJson["defaultSearchLanguage"], int):
        for game in config:
            config[game]["defaultSearchLanguage"] = fileJson["defaultSearchLanguage"]

    if "sourceLanguage" in fileJson and isinstance(fileJson["sourceLanguage"], int):
        for game in config:
            config[game]["sourceLanguage"] = fileJson["sourceLanguage"]


def _load_game_config(game, gameConfig):
    if "assetDir" in gameConfig and isinstance(gameConfig["assetDir"], str):
        config[game]["assetDir"] = gameConfig["assetDir"]
    if "isMale" in gameConfig and isinstance(gameConfig["isMale"], bool):
        config[game]["isMale"] = gameConfig["isMale"]
    if "nickname" in gameConfig and isinstance(gameConfig["nickname"], str):
        config[game]["nickname"] = gameConfig["nickname"]
    if "sourceLanguage" in gameConfig and isinstance(gameConfig["sourceLanguage"], int):
        config[game]["sourceLanguage"] = gameConfig["sourceLanguage"]
    if "defaultSearchLanguage" in gameConfig and isinstance(gameConfig["defaultSearchLanguage"], int):
        config[game]["defaultSearchLanguage"] = gameConfig["defaultSearchLanguage"]
    if "resultLanguages" in gameConfig and isinstance(gameConfig["resultLanguages"], list):
        config[game]["resultLanguages"] = gameConfig["resultLanguages"]


def saveConfig():
    fp = open("config.json", encoding='utf-8', mode="w")
    json.dump(config, fp, ensure_ascii=False, indent=2)
    fp.close()


def setDefaultSearchLanguage(newLanguage: int, game: str = "genshin"):
    config[game]['defaultSearchLanguage'] = newLanguage


def setResultLanguages(newLanguages: list[int], game: str = "genshin"):
    config[game]["resultLanguages"] = newLanguages


def setSourceLanguage(newSourceLanguage, game: str = "genshin"):
    config[game]['sourceLanguage'] = newSourceLanguage


def setIsMale(isMale, game: str = "genshin"):
    config[game]['isMale'] = isMale


def getDefaultSearchLanguage(game: str = "genshin"):
    return config[game]['defaultSearchLanguage']


def getResultLanguages(game: str = "genshin"):
    return config[game]["resultLanguages"]


def getSourceLanguage(game: str = "genshin"):
    return config[game]['sourceLanguage']


def getAssetDir(game: str = "genshin"):
    return config[game]['assetDir']


def setAssetDir(newDir: str, game: str = "genshin"):
    config[game]['assetDir'] = newDir


def getIsMale(game: str = "genshin"):
    return config[game]['isMale']


def getNickname(game: str = "genshin"):
    return config[game].get('nickname', '')


def setNickname(nickname: str, game: str = "genshin"):
    config[game]['nickname'] = nickname


loadConfig()
