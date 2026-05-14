import io

import databaseHelper
import languagePackReader
import starrailLanguagePackReader
import config
import placeholderHandler
from logger import get_logger

log = get_logger("controllers")


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
    for translate in translates:
        content = translate[0]
        if content.startswith("#"):
            obj['translates'][translate[1]] = (placeholderHandler.replace(content, config.getIsMale(game), translate[1], game))[1:]
        elif game == "starrail" and ("{M#" in content or "{F#" in content or "{NICKNAME}" in content):
            obj['translates'][translate[1]] = placeholderHandler.replace(content, config.getIsMale(game), translate[1], game)
        else:
            obj['translates'][translate[1]] = content

    if queryOrigin:
        origin, isTalk = selectVoiceOriginFromTextHash(textHash, sourceLangCode, game, db)
        obj['isTalk'] = isTalk
        obj['origin'] = origin

    voicePath = selectVoicePathFromTextHash(textHash, game, db)
    if voicePath is not None:
        if game == "genshin":
            voiceExist = False
            for lang in langs:
                if lang in languagePackReader.langPackages and languagePackReader.checkAudioBin(voicePath, lang):
                    voiceExist = True
                    break
            if voiceExist:
                obj['voicePaths'].append(voicePath)
        elif game == "starrail":
            starrailLanguagePackReader.loadLangPackages()
            if starrailLanguagePackReader.langPackages:
                voiceExist = False
                for lang in langs:
                    if lang in starrailLanguagePackReader.langPackages and starrailLanguagePackReader.checkAudioBin(voicePath, lang):
                        voiceExist = True
                        break
                if voiceExist:
                    obj['voicePaths'].append(voicePath)
            elif starrailLanguagePackReader._availableLangs:
                obj['voicePaths'].append(voicePath)

    return obj


def getTranslateObj(keyword: str, langCode: int, game="genshin"):
    db = databaseHelper.get_db(game)
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
        starrailLanguagePackReader.loadLangPackages()

    ans = []
    isMale = config.getIsMale(game)

    for content in contents:
        textHash = content[0]
        obj = {'translates': {}, 'voicePaths': [], 'hash': str(textHash)}

        translates = batchTranslates.get(textHash, [])
        for translate in translates:
            text = translate[0]
            lang = translate[1]
            if text.startswith("#"):
                obj['translates'][lang] = (placeholderHandler.replace(text, isMale, lang, game))[1:]
            elif game == "starrail" and ("{M#" in text or "{F#" in text or "{NICKNAME}" in text):
                obj['translates'][lang] = placeholderHandler.replace(text, isMale, lang, game)
            else:
                obj['translates'][lang] = text

        originInfo = batchOrigins.get(textHash)
        if originInfo is not None:
            obj['origin'] = originInfo[0]
            obj['isTalk'] = True
        else:
            fetterOrigin = batchFetterOrigins.get(textHash)
            if fetterOrigin is not None:
                obj['origin'] = fetterOrigin
                obj['isTalk'] = False
            else:
                obj['origin'] = "其他文本"
                obj['isTalk'] = False

        voicePath = batchVoicePaths.get(textHash)
        if voicePath is not None:
            if game == "genshin":
                voiceExist = False
                for lang in langs:
                    if lang in languagePackReader.langPackages and languagePackReader.checkAudioBin(voicePath, lang):
                        voiceExist = True
                        break
                if voiceExist:
                    obj['voicePaths'].append(voicePath)
            elif game == "starrail":
                if starrailLanguagePackReader.langPackages:
                    voiceExist = False
                    for lang in langs:
                        if lang in starrailLanguagePackReader.langPackages and starrailLanguagePackReader.checkAudioBin(voicePath, lang):
                            voiceExist = True
                            break
                    if voiceExist:
                        obj['voicePaths'].append(voicePath)
                elif starrailLanguagePackReader._availableLangs:
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
    log.debug(f"rawDialogues count={len(rawDialogues)} questName={questCompleteName}")
    dialogues = []

    for rawDialogue in rawDialogues:
        textHash, talkerType, talkerId, dialogueId = rawDialogue
        obj = queryTextHashInfo(textHash, langs, sourceLangCode, False, game, db)
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
    if game == "starrail":
        starrailLanguagePackReader.loadLangPackages()
        wemBin = starrailLanguagePackReader.getAudioBin(voicePath, langCode)
    else:
        wemBin = languagePackReader.getAudioBin(voicePath, langCode)
    if wemBin is None:
        return None
    return io.BytesIO(wemBin)


def getLoadedVoicePacks(game="genshin"):
    ans = {}
    if game == "starrail":
        starrailLanguagePackReader.loadLangPackages()
        if starrailLanguagePackReader.langPackages:
            for packId in starrailLanguagePackReader.langPackages:
                ans[packId] = starrailLanguagePackReader.langCodes[packId]
        else:
            for code in starrailLanguagePackReader._availableLangs:
                ans[code] = starrailLanguagePackReader.langCodes[code]
    else:
        for packId in languagePackReader.langPackages:
            ans[packId] = languagePackReader.langCodes[packId]

    return ans


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
