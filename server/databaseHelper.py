import sqlite3
from contextlib import closing
import os


class GameDB:
    TRAVELLER_AVATAR_IDS = {
        "genshin": 10000005,
        "starrail": 8001
    }

    def __init__(self, db_path, game="genshin"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._wanderNames = {}
        self._travellerNames = {}
        self._game = game

    def selectTextMapFromKeyword(self, keyWord: str, langCode: int):
        with closing(self.conn.cursor()) as cursor:
            sql1 = "select hash, content from textMap where lang=? and content like ? limit 200"
            cursor.execute(sql1, (langCode, '%{}%'.format(keyWord)))
            matches = cursor.fetchall()
            return matches

    def selectTextMapFromTextHash(self, textHash, langs: list[int] = None):
        with closing(self.conn.cursor()) as cursor:
            if langs is not None and len(langs) > 0:
                langStr = ','.join([str(i) for i in langs])
                sql1 = "select content, lang from textMap where hash=? and lang in ({})".format(langStr)
            else:
                sql1 = "select content, lang from textMap where hash=?"
            cursor.execute(sql1, (textHash,))
            matches = cursor.fetchall()
            return matches

    def selectVoicePathFromTextHashInFetter(self, textHash):
        with closing(self.conn.cursor()) as cursor:
            sql1 = ("select voicePath,voice.avatarId from fetters, voice "
                    "where voiceFileTextTextMapHash=? and fetters.voiceFile=voice.dialogueId "
                    "and (fetters.avatarId=voice.avatarId or voice.avatarId=0)")
            cursor.execute(sql1, (textHash,))
            matches = cursor.fetchall()
            if len(matches) >= 1:
                return matches[0][0]
            elif len(matches) == 0:
                return None

    def selectVoicePathFromTextHashInDialogue(self, textHash):
        with closing(self.conn.cursor()) as cursor:
            sql1 = "select voicePath from dialogue join voice on voice.dialogueId= dialogue.dialogueId where textHash=?"
            cursor.execute(sql1, (textHash,))
            matches = cursor.fetchall()
            if len(matches) > 0:
                return matches[0][0]
            return None

    def getImportedTextMapLangs(self):
        with closing(self.conn.cursor()) as cursor:
            sql1 = "select id,displayName from langCode where imported=1"
            cursor.execute(sql1, )
            matches = cursor.fetchall()
            return matches

    def getSourceFromFetter(self, textHash, langCode: int = 1):
        with closing(self.conn.cursor()) as cursor:
            sql1 = 'select avatarId, content from fetters, textMap where voiceFileTextTextMapHash=? and voiceTitleTextMapHash = hash and lang=?'
            cursor.execute(sql1, (textHash, langCode))
            ans = cursor.fetchall()
            if len(ans) == 0:
                return None
            avatarId, voiceTitle = ans[0]

            sql2 = 'select content from avatar, textMap where avatarId=? and avatar.nameTextMapHash=textMap.hash and lang=?'

            cursor.execute(sql2, (avatarId, langCode))
            ans2 = cursor.fetchall()
            if len(ans2) == 0:
                return None
            avatarName = ans2[0][0]

            return "{} · {}".format(avatarName, voiceTitle)

    def getCharterName(self, avatarId: int, langCode: int = 1):
        with closing(self.conn.cursor()) as cursor:
            sql2 = 'select content from avatar, textMap where avatarId=? and avatar.nameTextMapHash=textMap.hash and lang=?'

            cursor.execute(sql2, (avatarId, langCode,))
            ans2 = cursor.fetchall()
            if len(ans2) == 0:
                return None

            return ans2[0][0]

    def getWanderName(self, langCode: int = 1):
        if langCode not in self._wanderNames:
            self._wanderNames[langCode] = self.getCharterName(10000075, langCode)
        return self._wanderNames[langCode]

    def getTravellerName(self, langCode: int = 1):
        if langCode not in self._travellerNames:
            avatarId = self.TRAVELLER_AVATAR_IDS.get(self._game, 10000005)
            self._travellerNames[langCode] = self.getCharterName(avatarId, langCode)
        return self._travellerNames[langCode]

    def getTalkInfo(self, textHash) -> 'tuple[int, str, int, int | None] | None':
        with closing(self.conn.cursor()) as cursor:
            sql1 = 'select talkerType, talkerId, talkId, coopQuestId from dialogue where textHash=?'
            cursor.execute(sql1, (textHash,))
            ans = cursor.fetchall()
            if len(ans) == 0:
                return None
            talkerType, talkerId, talkId, coopQuestId = ans[0]
            return talkId, talkerType, talkerId, coopQuestId

    def getTalkerName(self, talkerType: str, talkerId: int, langCode: int = 1) -> 'str | None':
        with closing(self.conn.cursor()) as cursor:
            talkerName = None
            if talkerType == "TALK_ROLE_NPC":
                sqlGetNpcName = 'select content from npc, textMap indexed by textMap_hash_index where npcId = ? and textHash = hash and lang = ?'
                cursor.execute(sqlGetNpcName, (talkerId, langCode))
                ansNpcName = cursor.fetchall()
                if len(ansNpcName) > 0:
                    talkerName = ansNpcName[0][0]
            elif talkerType == "TALK_ROLE_PLAYER":
                talkerName = "主角"
            elif talkerType == "TALK_ROLE_MATE_AVATAR":
                talkerName = "反主"

            if talkerName == '#{REALNAME[ID(1)|HOSTONLY(true)]}':
                talkerName = self.getWanderName(langCode)
            return talkerName

    def getTalkQuestId(self, talkId: int) -> int | None:
        with closing(self.conn.cursor()) as cursor:
            sql2 = ('select quest.questId from questTalk, quest '
                    'where talkId=? and quest.questId=questTalk.questId')
            cursor.execute(sql2, (talkId,))
            ans2 = cursor.fetchall()
            if len(ans2) == 0:
                return None
            return ans2[0][0]

    def getQuestName(self, questId, langCode):
        with closing(self.conn.cursor()) as cursor:
            sql2 = ('select content from quest, textMap '
                    'where quest.questId=? and titleTextMapHash=hash and lang=?')
            cursor.execute(sql2, (questId, langCode))
            ans2 = cursor.fetchall()
            if len(ans2) == 0:
                return "对话文本"

            questTitle = ans2[0][0]

            sql3 = 'select chapterTitleTextMapHash,chapterNumTextMapHash from chapter, quest where questId=? and quest.chapterId=chapter.chapterId'
            cursor.execute(sql3, (questId,))
            ans3 = cursor.fetchall()
            if len(ans3) == 0:
                return questTitle
            chapterTitleTextMapHash, chapterNumTextMapHash = ans3[0]

            sql4 = 'select content from textMap where hash=? and lang=?'
            cursor.execute(sql4, (chapterTitleTextMapHash, langCode))
            ans4 = cursor.fetchall()
            if len(ans4) == 0:
                return questTitle

            chapterTitleText = ans4[0][0]

            cursor.execute(sql4, (chapterNumTextMapHash, langCode))
            ans5 = cursor.fetchall()

            if len(ans5) > 0:
                chapterNumText = ans5[0][0]
                questCompleteName = '{} · {} · {}'.format(chapterNumText, chapterTitleText, questTitle)
            else:
                questCompleteName = '{} · {}'.format(chapterTitleText, questTitle)

            return questCompleteName

    def getTalkQuestName(self, talkId: int, langCode: int = 1) -> str:
        questId = self.getTalkQuestId(talkId)
        if questId is None:
            return "对话文本"

        questCompleteName = self.getQuestName(questId, langCode)
        return questCompleteName

    def getCoopTalkQuestName(self, coopQuestId, langCode):
        questCompleteName = self.getQuestName(coopQuestId // 100, langCode)
        return questCompleteName

    def getSourceFromDialogue(self, textHash, langCode: int = 1):
        talkInfo = self.getTalkInfo(textHash)
        if talkInfo is None:
            return None

        talkId, talkerType, talkerId, coopQuestId = talkInfo

        talkerName = self.getTalkerName(talkerType, talkerId, langCode)

        if coopQuestId is None:
            questCompleteName = self.getTalkQuestName(talkId, langCode)
        else:
            questCompleteName = self.getCoopTalkQuestName(coopQuestId, langCode)

        if talkerName is None:
            return questCompleteName
        else:
            return f"{talkerName}, {questCompleteName}"

    def getManualTextMap(self, placeHolderName, lang):
        with closing(self.conn.cursor()) as cursor:
            sql1 = 'select content from manualTextMap, textMap where textMapId=? and textHash = hash and lang=?'
            cursor.execute(sql1, (placeHolderName, lang))
            ans = cursor.fetchall()
            if len(ans) > 0:
                return ans[0][0]
            else:
                return None

    def getTalkContent(self, talkId: int, coopQuestId: 'int | None') -> 'list[tuple[int, str, int, int]] | None':
        with closing(self.conn.cursor()) as cursor:
            if coopQuestId is None:
                sql1 = 'select textHash, talkerType, talkerId, dialogueId from dialogue where talkId = ? and coopQuestId is null'
                cursor.execute(sql1, (talkId,))
                ans = cursor.fetchall()
            else:
                sql1 = 'select textHash, talkerType, talkerId, dialogueId from dialogue where talkId = ? and coopQuestId = ?'
                cursor.execute(sql1, (talkId, coopQuestId))
                ans = cursor.fetchall()
            if len(ans) > 0:
                return ans
            else:
                return None

    def batchSelectTextMapFromTextHash(self, textHashes: list, langs: list[int] = None):
        if not textHashes:
            return {}
        with closing(self.conn.cursor()) as cursor:
            placeholders = ','.join(['?'] * len(textHashes))
            if langs is not None and len(langs) > 0:
                langStr = ','.join([str(i) for i in langs])
                sql = f"select hash, content, lang from textMap where hash in ({placeholders}) and lang in ({langStr})"
            else:
                sql = f"select hash, content, lang from textMap where hash in ({placeholders})"
            cursor.execute(sql, textHashes)
            result = {}
            for row in cursor.fetchall():
                h = row[0]
                if h not in result:
                    result[h] = []
                result[h].append((row[1], row[2]))
            return result

    def batchGetSourceFromDialogue(self, textHashes: list, langCode: int = 1):
        if not textHashes:
            return {}
        with closing(self.conn.cursor()) as cursor:
            placeholders = ','.join(['?'] * len(textHashes))
            sql = f"""select d.textHash, d.talkerType, d.talkerId, d.talkId, d.coopQuestId
                      from dialogue d where d.textHash in ({placeholders})"""
            cursor.execute(sql, textHashes)
            dialogueRows = cursor.fetchall()

            talkIds = set()
            npcIds = set()
            for row in dialogueRows:
                talkIds.add(row[3])
                if row[1] == "TALK_ROLE_NPC":
                    npcIds.add(row[2])

            talkToQuest = {}
            if talkIds:
                talkPlaceholders = ','.join(['?'] * len(talkIds))
                sql2 = f"select talkId, questId from questTalk where talkId in ({talkPlaceholders})"
                cursor.execute(sql2, list(talkIds))
                for r in cursor.fetchall():
                    talkToQuest[r[0]] = r[1]

            npcNames = {}
            if npcIds:
                npcPlaceholders = ','.join(['?'] * len(npcIds))
                sql3 = f"""select npcId, content from npc, textMap
                           where npcId in ({npcPlaceholders}) and textHash = hash and lang = ?"""
                cursor.execute(sql3, list(npcIds) + [langCode])
                for r in cursor.fetchall():
                    npcNames[r[0]] = r[1]

            questIds = set(talkToQuest.values())
            questNames = {}
            questChapters = {}
            if questIds:
                questPlaceholders = ','.join(['?'] * len(questIds))
                sql4 = f"""select questId, content from quest, textMap
                           where questId in ({questPlaceholders}) and titleTextMapHash = hash and lang = ?"""
                cursor.execute(sql4, list(questIds) + [langCode])
                for r in cursor.fetchall():
                    questNames[r[0]] = r[1]

                sql5 = f"""select questId, chapterTitleTextMapHash, chapterNumTextMapHash
                           from chapter, quest where questId in ({questPlaceholders}) and quest.chapterId = chapter.chapterId"""
                cursor.execute(sql5, list(questIds))
                for r in cursor.fetchall():
                    questChapters[r[0]] = (r[1], r[2])

            chapterHashes = set()
            for qid, (titleHash, numHash) in questChapters.items():
                chapterHashes.add(titleHash)
                if numHash:
                    chapterHashes.add(numHash)

            chapterTexts = {}
            if chapterHashes:
                chPlaceholders = ','.join(['?'] * len(chapterHashes))
                sql6 = f"select hash, content from textMap where hash in ({chPlaceholders}) and lang = ?"
                cursor.execute(sql6, list(chapterHashes) + [langCode])
                for r in cursor.fetchall():
                    chapterTexts[r[0]] = r[1]

            result = {}
            for row in dialogueRows:
                textHash = row[0]
                talkerType = row[1]
                talkerId = row[2]
                talkId = row[3]
                coopQuestId = row[4]

                talkerName = None
                if talkerType == "TALK_ROLE_NPC":
                    talkerName = npcNames.get(talkerId)
                elif talkerType == "TALK_ROLE_PLAYER":
                    talkerName = "主角"
                elif talkerType == "TALK_ROLE_MATE_AVATAR":
                    talkerName = "反主"

                if coopQuestId is not None:
                    questId = coopQuestId // 100
                else:
                    questId = talkToQuest.get(talkId)

                if questId is None:
                    questCompleteName = "对话文本"
                else:
                    questTitle = questNames.get(questId, "对话文本")
                    chInfo = questChapters.get(questId)
                    if chInfo:
                        titleHash, numHash = chInfo
                        chapterTitleText = chapterTexts.get(titleHash)
                        if chapterTitleText:
                            numText = chapterTexts.get(numHash) if numHash else None
                            if numText:
                                questCompleteName = f"{numText} · {chapterTitleText} · {questTitle}"
                            else:
                                questCompleteName = f"{chapterTitleText} · {questTitle}"
                        else:
                            questCompleteName = questTitle
                    else:
                        questCompleteName = questTitle

                if talkerName is not None:
                    result[textHash] = (f"{talkerName}, {questCompleteName}",)
                else:
                    result[textHash] = (questCompleteName,)

            return result

    def batchGetSourceFromFetter(self, textHashes: list, langCode: int = 1):
        if not textHashes:
            return {}
        with closing(self.conn.cursor()) as cursor:
            placeholders = ','.join(['?'] * len(textHashes))
            sql = f"""select f.voiceFileTextTextMapHash, f.avatarId, t.content
                      from fetters f, textMap t
                      where f.voiceFileTextTextMapHash in ({placeholders})
                      and f.voiceTitleTextMapHash = t.hash and t.lang = ?"""
            cursor.execute(sql, textHashes + [langCode])
            fetterRows = cursor.fetchall()

            avatarIds = set(r[1] for r in fetterRows)
            avatarNames = {}
            if avatarIds:
                avPlaceholders = ','.join(['?'] * len(avatarIds))
                sql2 = f"""select avatarId, content from avatar, textMap
                           where avatarId in ({avPlaceholders})
                           and avatar.nameTextMapHash = textMap.hash and lang = ?"""
                cursor.execute(sql2, list(avatarIds) + [langCode])
                for r in cursor.fetchall():
                    avatarNames[r[0]] = r[1]

            result = {}
            for row in fetterRows:
                textHash = row[0]
                avatarId = row[1]
                voiceTitle = row[2]
                avatarName = avatarNames.get(avatarId, "")
                result[textHash] = f"{avatarName} · {voiceTitle}"

            return result

    def batchSelectVoicePathFromTextHash(self, textHashes: list):
        if not textHashes:
            return {}
        with closing(self.conn.cursor()) as cursor:
            placeholders = ','.join(['?'] * len(textHashes))
            sql = f"""select d.textHash, v.voicePath
                      from dialogue d join voice v on v.dialogueId = d.dialogueId
                      where d.textHash in ({placeholders})"""
            cursor.execute(sql, textHashes)
            result = {}
            for row in cursor.fetchall():
                if row[0] not in result:
                    result[row[0]] = row[1]
            return result


_game_dbs = {}


def get_db(game: str) -> GameDB:
    if game not in _game_dbs:
        if game == "genshin":
            db_path = os.path.join(os.path.dirname(__file__), "data.db")
        elif game == "starrail":
            db_path = os.path.join(os.path.dirname(__file__), "starrail-data.db")
        else:
            raise ValueError(f"Unknown game: {game}")
        _game_dbs[game] = GameDB(db_path, game)
    return _game_dbs[game]


def get_available_games():
    games = []
    if os.path.exists(os.path.join(os.path.dirname(__file__), "data.db")):
        games.append("genshin")
    if os.path.exists(os.path.join(os.path.dirname(__file__), "starrail-data.db")):
        games.append("starrail")
    return games
