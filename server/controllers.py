import io

import databaseHelper
from voice.checker import get_checker
import config
from text.placeholder import process_translates as placeholderProcessTranslates
from text.wordSearch import expand_query_words
from logger import get_logger

log = get_logger("controllers")

_STARRAIL_VOICE_PATH_CHAPTER_MAP = {
    'chapter0': '空间站「黑塔」',
    'chapter1': '雅利洛-VI',
    'chapter2': '仙舟「罗浮」',
    'chapter3': '匹诺康尼',
    'chapter4': '翁瓦克',
    'vo_hertaspacestation': '空间站「黑塔」',
    'vo_belobog': '雅利洛-VI',
    'vo_xianzhou': '仙舟「罗浮」',
    'vo_penacony': '匹诺康尼',
    'vo_amphoreus': '翁瓦克',
}


class TalkNotFoundError(Exception):
    pass


def selectVoicePathFromTextHash(textHash, game="genshin", db=None):
    if db is None:
        db = databaseHelper.get_db(game)
    voicePath = db.selectVoicePathFromTextHashInDialogue(textHash)
    if voicePath is not None:
        return voicePath

    voicePath = db.selectVoicePathFromTextHashInFetter(textHash)
    if voicePath is not None:
        return voicePath

    return None


def selectVoiceOriginFromTextHash(textHash, langCode: int, game="genshin", db=None) -> tuple[str, bool]:
    if db is None:
        db = databaseHelper.get_db(game)
    origin = db.getSourceFromDialogue(textHash, langCode)
    if origin is not None:
        return origin, True

    origin = db.getSourceFromFetter(textHash, langCode)
    if origin is not None:
        return origin, False

    return "其他文本", False


def queryTextHashInfo(textHash, langs: 'list[int]', sourceLangCode: int, queryOrigin=True, game="genshin", db=None):
    if db is None:
        db = databaseHelper.get_db(game)
    obj = {'translates': {}, 'voicePaths': [], 'hash': str(textHash)}
    translates = db.selectTextMapFromTextHash(textHash, langs)
    obj['translates'] = placeholderProcessTranslates(translates, config.getIsMale(game), game)

    if queryOrigin:
        origin, isTalk = selectVoiceOriginFromTextHash(textHash, sourceLangCode, game, db)
        obj['isTalk'] = isTalk
        obj['origin'] = origin

    voicePath = selectVoicePathFromTextHash(textHash, game, db)
    if voicePath is not None:
        checker = get_checker(game)
        checker.ensure_loaded()
        if checker.should_append_voice(voicePath, langs):
            obj['voicePaths'].append(voicePath)

    return obj


def getTranslateObj(keyword: str, langCode: int, game="genshin", word_mode=False):
    db = databaseHelper.get_db(game)
    if word_mode and langCode == 4:
        expanded = expand_query_words(keyword)
        contents = db.selectTextMapFromKeywordWordMode(expanded, langCode)
    else:
        contents = db.selectTextMapFromKeyword(keyword, langCode)

    langs = config.getResultLanguages(game)
    sourceLangCode = config.getSourceLanguage(game)

    hashes = [c[0] for c in contents]

    batchTranslates = db.batchSelectTextMapFromTextHash(hashes, langs)
    batchOrigins = db.batchGetSourceFromDialogue(hashes, sourceLangCode)
    batchFetterOrigins = db.batchGetSourceFromFetter(
        [h for h in hashes if batchOrigins.get(h) is None], sourceLangCode
    )
    batchVoicePaths = db.batchSelectVoicePathFromTextHash(hashes)

    if game == "starrail":
        checker = get_checker(game)
        checker.ensure_loaded()
        talkerMap = db.batchGetTalkerNameFromTextHash(hashes, sourceLangCode)

    ans = []
    isMale = config.getIsMale(game)

    for content in contents:
        textHash = content[0]
        obj = {'translates': {}, 'voicePaths': [], 'hash': str(textHash)}

        translates = batchTranslates.get(textHash, [])
        obj['translates'] = placeholderProcessTranslates(translates, isMale, game)

        originInfo = batchOrigins.get(textHash)
        if originInfo is not None:
            obj['origin'] = originInfo[0]
            obj['isTalk'] = True
            if game == "genshin" and ', ' in originInfo[0]:
                obj['talker'] = originInfo[0].split(', ')[0]
            # 崩铁：如果来源是"对话文本"，尝试从语音路径推断更好的来源
            if game == "starrail" and originInfo[0] == "对话文本":
                vp = batchVoicePaths.get(textHash)
                if vp:
                    for prefix, areaName in _STARRAIL_VOICE_PATH_CHAPTER_MAP.items():
                        if vp.startswith(prefix):
                            obj['origin'] = areaName
                            break
        else:
            fetterOrigin = batchFetterOrigins.get(textHash)
            if fetterOrigin is not None:
                obj['origin'] = fetterOrigin
                obj['isTalk'] = False
            else:
                obj['origin'] = "其他文本"
                obj['isTalk'] = False

        if game == "starrail":
            talker = talkerMap.get(textHash)
            if talker:
                obj['talker'] = talker

        voicePath = batchVoicePaths.get(textHash)
        if voicePath is not None:
            checker = get_checker(game)
            if checker.should_append_voice(voicePath, langs):
                obj['voicePaths'].append(voicePath)

        ans.append(obj)

    ans.sort(key=lambda x: (x['origin'] == "其他文本", x['origin']))

    return ans


def getTalkFromHash(textHash, game="genshin"):
    db = databaseHelper.get_db(game)
    talkInfo = db.getTalkInfo(textHash)
    if talkInfo is None:
        log.warning(f"talkInfo is None for textHash={textHash} game={game}")
        raise TalkNotFoundError("内容不属于任何对话！")

    langs = config.getResultLanguages(game)
    sourceLangCode = config.getSourceLanguage(game)

    talkId, talkerType, talkerId, coopQuestId = talkInfo
    log.debug(f"talkInfo: talkId={talkId} talkerType={talkerType} talkerId={talkerId} langs={langs}")

    if coopQuestId is None:
        questCompleteName = db.getTalkQuestName(talkId, sourceLangCode)
    else:
        questCompleteName = db.getCoopTalkQuestName(coopQuestId, sourceLangCode)

    rawDialogues = db.getTalkContent(talkId, coopQuestId, game)
    if rawDialogues is None:
        log.warning(f"rawDialogues is None for talkId={talkId} textHash={textHash} game={game}")
        raise TalkNotFoundError("未找到该对话内容！")
    log.debug(f"rawDialogues count={len(rawDialogues)} questName={questCompleteName}")
    dialogues = []

    if game == "starrail":
        dialogueIds = [rd[3] for rd in rawDialogues]
        talkerNamesFromVoice = db.batchGetTalkerNameFromVoice(dialogueIds)
    else:
        talkerNamesFromVoice = {}

    for rawDialogue in rawDialogues:
        textHash, talkerType, talkerId, dialogueId = rawDialogue
        obj = queryTextHashInfo(textHash, langs, sourceLangCode, False, game, db)
        if game == "starrail":
            obj['talker'] = talkerNamesFromVoice.get(dialogueId)
        else:
            obj['talker'] = db.getTalkerName(talkerType, talkerId, sourceLangCode)
        obj['dialogueId'] = dialogueId
        dialogues.append(obj)

    ans = {
        "talkQuestName": questCompleteName,
        "talkId": talkId,
        "dialogues": dialogues
    }

    return ans


def getVoiceBinStream(voicePath, langCode, game="genshin"):
    checker = get_checker(game)
    checker.ensure_loaded()
    wemBin = checker.get_audio_bin(voicePath, langCode)
    if wemBin is None:
        return None
    return io.BytesIO(wemBin)


def getLoadedVoicePacks(game="genshin"):
    checker = get_checker(game)
    checker.ensure_loaded()
    return checker.get_loaded_voice_packs()


def getImportedTextMapLangs(game="genshin"):
    db = databaseHelper.get_db(game)
    langs = db.getImportedTextMapLangs()
    ans = {}
    for langItem in langs:
        ans[langItem[0]] = langItem[1]

    return ans


def getConfig():
    return config.config


def setDefaultSearchLanguage(newLanguage: int, game: str = "genshin"):
    config.setDefaultSearchLanguage(newLanguage, game)


def setResultLanguages(newLanguages: list[int], game: str = "genshin"):
    config.setResultLanguages(newLanguages, game)


def saveConfig():
    config.saveConfig()


def setSourceLanguage(newSourceLanguage, game: str = "genshin"):
    config.setSourceLanguage(newSourceLanguage, game)


def setIsMale(isMale: bool, game: str = "genshin"):
    config.setIsMale(isMale, game)


def setAssetDir(newDir: str, game: str = "genshin"):
    config.setAssetDir(newDir, game)


def setNickname(nickname: str, game: str = "genshin"):
    config.setNickname(nickname, game)
