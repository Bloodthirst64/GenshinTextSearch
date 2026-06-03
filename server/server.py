import os.path
import time

from flask import Flask, jsonify, request, send_file, make_response
import controllers
import config
import databaseHelper
import lyricsData
from flask_cors import CORS
from flask import send_from_directory
from logger import get_logger

log = get_logger("server")

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
    wordMode = request.json.get('wordMode', False)

    if keyword.strip() == "":
        return buildResponse([])

    start = time.time()
    contents = controllers.getTranslateObj(keyword, langCode, game, word_mode=wordMode)
    end = time.time()

    talk_count = sum(1 for c in contents if c.get('isTalk'))
    voice_count = sum(1 for c in contents if c.get('voicePaths'))
    log.info(f"keyword={keyword} game={game} results={len(contents)} isTalk={talk_count} hasVoice={voice_count}")
    for c in contents[:3]:
        log.debug(f"  hash={c['hash']} isTalk={c.get('isTalk')} origin={c.get('origin')} translates_keys={list(c.get('translates', {}).keys())} voicePaths={c.get('voicePaths')}")

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
        log.warning(f"voice not found: voicePath={voicePath} langCode={langCode} game={game}")
        resp = make_response("Audio File Not Found")
        resp.headers['Access-Control-Expose-Headers'] = 'Error'
        resp.headers['Error'] = 'True'
        return resp

    log.info(f"voice ok: voicePath={voicePath} langCode={langCode} game={game} size={wemStream.getbuffer().nbytes}")
    return send_file(
        wemStream,
        download_name='voicePath',
        mimetype='image/png'
    )


@app.route("/api/getTalkFromHash", methods=['POST'])
def getTalkFromHash():
    textHash = int(request.json['textHash'])
    game = request.json.get('game', 'genshin')
    log.info(f"textHash={textHash} game={game}")
    try:
        start = time.time()
        contents = controllers.getTalkFromHash(textHash, game)
        end = time.time()
        log.info(f"success: talkQuestName={contents.get('talkQuestName')}, dialogues={len(contents.get('dialogues', []))}")
        for i, d in enumerate(contents.get('dialogues', [])[:3]):
            log.debug(f"  [{i}] talker={d.get('talker')} translates_keys={list(d.get('translates', {}).keys())} voicePaths={d.get('voicePaths')}")
    except controllers.TalkNotFoundError as e:
        log.warning(f"not found: textHash={textHash} game={game} error={e}")
        return buildResponse(code=114, msg=str(e))
    except Exception as e:
        log.error(f"exception: textHash={textHash} game={game} error={type(e).__name__}: {e}")
        return buildResponse(code=500, msg=str(e))

    return buildResponse({
        'contents': contents,
        'time': (end - start)*1000
    })


@app.route("/api/lyricsSearch", methods=['POST'])
def lyricsSearch():
    keyword = request.json.get('keyword', '').strip()
    game = request.json.get('game', None)
    if keyword == "":
        return buildResponse([])

    start = time.time()
    results = lyricsData.search_lyrics(keyword, game)
    end = time.time()

    log.info(f"lyricsSearch: keyword={keyword} game={game} results={len(results)}")
    return buildResponse({
        'contents': results,
        'time': (end - start)*1000
    })


@app.route("/api/getLyricsSongs")
def getLyricsSongs():
    game = request.args.get("game", None)
    songs = lyricsData.get_all_songs(game)
    return buildResponse(songs)


@app.route("/api/getLyricsDetail", methods=['POST'])
def getLyricsDetail():
    title = request.json.get('title', '')
    game = request.json.get('game', None)
    song = lyricsData.get_song_detail(title, game)
    if song is None:
        return buildResponse(code=404, msg="未找到该歌曲")
    return buildResponse(song)


@app.route("/api/reloadLyricsData", methods=['POST'])
def reloadLyricsData():
    songs = lyricsData.reload_lyrics_data()
    return buildResponse({"count": len(songs)})


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
    log.info("server starting on 0.0.0.0:5000")
    app.run(debug=False, host='0.0.0.0')
