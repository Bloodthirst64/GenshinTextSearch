import os.path
import time

from flask import Flask, jsonify, request, send_file, make_response
import controllers
import config
import databaseHelper
from flask_cors import CORS
from flask import send_from_directory

app = Flask(__name__)
CORS(app)


def buildResponse(data=None, code=200, msg="ok"):
    return jsonify({
        "data": data,
        "code": code,
        "msg": msg
    })


@app.route("/api/getAvailableGames")
def getAvailableGames():
    games = databaseHelper.get_available_games()
    game_info = {}
    for g in games:
        if g == "genshin":
            game_info[g] = "原神"
        elif g == "starrail":
            game_info[g] = "崩坏：星穹铁道"
    return buildResponse(game_info)


@app.route("/api/getImportedTextLanguages")
def getImportedTextLanguages():
    game = request.args.get("game", "genshin")
    return buildResponse(controllers.getImportedTextMapLangs(game))


@app.route("/api/getImportedVoiceLanguages")
def getImportedVoiceLanguages():
    game = request.args.get("game", "genshin")
    return buildResponse(controllers.getLoadedVoicePacks(game))


@app.route("/api/keywordQuery", methods=['POST'])
def keywordQuery():
    langCode = request.json['langCode']
    keyword: str = request.json['keyword']
    game = request.json.get('game', 'genshin')

    if keyword.strip() == "":
        return buildResponse([])

    start = time.time()
    contents = controllers.getTranslateObj(keyword, langCode, game)
    end = time.time()

    return buildResponse({
        'contents': contents,
        'time': (end - start)*1000
    })


@app.route("/api/getVoiceOver", methods=['POST'])
def getVoiceOver():
    langCode = request.json['langCode']
    voicePath = request.json['voicePath']
    game = request.json.get('game', 'genshin')

    wemStream = controllers.getVoiceBinStream(voicePath, langCode, game)
    if wemStream is None:
        resp = make_response("Audio File Not Found")
        resp.headers['Access-Control-Expose-Headers'] = 'Error'
        resp.headers['Error'] = 'True'
        return resp

    return send_file(
        wemStream,
        download_name='voicePath',
        mimetype='image/png'
    )


@app.route("/api/getTalkFromHash", methods=['POST'])
def getTalkFromHash():
    textHash = request.json['textHash']
    game = request.json.get('game', 'genshin')
    try:
        start = time.time()
        contents = controllers.getTalkFromHash(textHash, game)
        end = time.time()
    except controllers.TalkNotFoundError as e:
        return buildResponse(code=114, msg=str(e))

    return buildResponse({
        'contents': contents,
        'time': (end - start)*1000
    })


@app.route("/api/saveSettings", methods=['POST'])
def saveSettings():
    newConfig = request.json.get('config', {})

    for game in ["genshin", "starrail"]:
        gameConfig = newConfig.get(game, {})
        if not isinstance(gameConfig, dict):
            continue
        if 'defaultSearchLanguage' in gameConfig:
            controllers.setDefaultSearchLanguage(gameConfig['defaultSearchLanguage'], game)
        if 'resultLanguages' in gameConfig:
            controllers.setResultLanguages(gameConfig['resultLanguages'], game)
        if 'sourceLanguage' in gameConfig:
            controllers.setSourceLanguage(gameConfig['sourceLanguage'], game)
        if 'isMale' in gameConfig:
            controllers.setIsMale(gameConfig['isMale'], game)
        if 'nickname' in gameConfig:
            controllers.setNickname(gameConfig['nickname'], game)
        if 'assetDir' in gameConfig:
            controllers.setAssetDir(gameConfig['assetDir'], game)

    controllers.saveConfig()

    return buildResponse(controllers.getConfig())


@app.route("/api/getSettings")
def getConfig():
    return buildResponse(controllers.getConfig())


staticDir = r"../webui/dist/"


@app.route('/')
def serveRoot():
    return send_from_directory(staticDir, 'index.html')


@app.route("/<path:path>")
def serveStatic(path):
    filePath = staticDir + path
    if os.path.exists(filePath):
        return send_from_directory(staticDir, path)
    else:
        return send_from_directory(staticDir, 'index.html')


if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0')
