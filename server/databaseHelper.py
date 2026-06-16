import sqlite3
from contextlib import closing
import os
import re
from logger import get_logger

log = get_logger("database")

_VOICE_PATH_CHAR_MAP = {
    'player': '开拓者',
    'playerboy': '穹',
    'mar7th': '三月七',
    'march7th': '三月七',
    'sanyueqi': '三月七',
    'danheng': '丹恒',
    'danhengil': '丹恒•饮月',
    'danhengcb': '丹恒',
    'danhengjiyi': '丹恒',
    'jydanfeng': '丹枫',
    'himeko': '姬子',
    'himekojiyi': '姬子',
    'welt': '瓦尔特',
    'silverwolf': '银狼',
    'silverwolflv999': '银狼',
    'kafka': '卡芙卡',
    'arlan': '阿兰',
    'asta': '艾丝妲',
    'herta': '黑塔',
    'theherta': '大黑塔',
    'hertadoll': '黑塔',
    'bronya': '布洛妮娅',
    'seele': '希儿',
    'serval': '希露瓦',
    'gepard': '杰帕德',
    'natasha': '娜塔莎',
    'pela': '佩拉',
    'clara': '克拉拉',
    'sampo': '桑博',
    'hook': '虎克',
    'lynx': '玲可',
    'luka': '卢卡',
    'topaz': '托帕',
    'jingyuan': '景元',
    'bailu': '白露',
    'yanqing': '彦卿',
    'fuxuan': '符玄',
    'tingyun': '停云',
    'qingque': '青雀',
    'luofucloud': '停云',
    'luocha': '罗刹',
    'misha': '米沙',
    'xueyi': '雪衣',
    'xueyijiqiao': '雪衣',
    'ruanyi': '阮•梅',
    'ruanmei': '阮•梅',
    'ruanyue': '阮•梅',
    'drtruth': '真理医生',
    'ratio': '真理医生',
    'sparkle': '花火',
    'blackswan': '黑天鹅',
    'blackswanjiyi': '黑天鹅',
    'acheron': '黄泉',
    'aventurine': '砂金',
    'gallagher': '加拉格尔',
    'robin': '知更鸟',
    'sunday': '星期日',
    'sundayow': '星期日',
    'boothill': '波提欧',
    'littleboothill': '波提欧',
    'jade': '翡翠',
    'firefly': '流萤',
    'sam': '萨姆',
    'yunli': '云璃',
    'jiaoqiu': '椒丘',
    'feixiao': '飞霄',
    'feixiaohy': '飞霄',
    'feixiaoyn': '飞霄',
    'lingsha': '灵砂',
    'moze': '貊泽',
    'rappa': '乱破',
    'rappasy': '乱破',
    'tribbie': '缇宝',
    'jisitribbie': '缇宝',
    'mydei': '遐蝶',
    'mydeimos': '遐蝶',
    'mydeimosly': '遐蝶',
    'aglaea': '阿格莱雅',
    'aglaeahy': '阿格莱雅',
    'castorice': '刻律德拉',
    'castoricehy': '刻律德拉',
    'castoricetitan': '刻律德拉',
    'phainon': '白厄',
    'phainonjiyi': '白厄',
    'phainonly': '白厄',
    'hyacine': '风堇',
    'hyacinetitan': '风堇',
    'anaxa': '阿那克萨',
    'anaxapb': '阿那克萨',
    'cipher': '赛飞儿',
    'shaocipher': '赛飞儿',
    'hysilens': '海瑟音',
    'mem': '忆灵',
    'lykos': '吕科斯',
    'lykosecho': '吕科斯',
    'lykosjiyi': '吕科斯',
    'cyrene': '昔涟',
    'cyrenejiyi': '昔涟',
    'cyrenely': '昔涟',
    'danfeng': '丹枫',
    'yingxing': '应星',
    'baiheng': '白珩',
    'jingliu': '镜流',
    'jingtian': '景天',
    'wenzhao': '文韬',
    'shujie': '舒杰',
    'owen': '欧文',
    'sushang': '素裳',
    'yukong': '驭空',
    'castrux': '寰宇',
    'owl': '智鸮',
    'caelus': '穹',
    'stelle': '星',
    'caelusf': '星',
    'stellem': '穹',
    'playerfan': '开拓者',
    'playertt': '开拓者',
    # 重要NPC
    'pompom': '帕姆',
    'cocolia': '可可利亚',
    'blade': '刃',
    'argenti': '银枝',
    'screwllum': '螺丝咕姆',
    'svarog': '史瓦罗',
    'oleg': '奥列格',
    'tingyun1': '停云',
    'tingyun2': '停云',
    'tingyun3': '停云',
    'tingyun4': '停云',
    'tingyun5': '停云',
    'tingyun6': '停云',
    'tingyun7': '停云',
    'tingyun8': '停云',
    'tingyun9': '停云',
    'fakemar7th': '三月七',
    'fakemar7thB': '三月七',
    'fakemar7thC': '三月七',
    'scott': '斯科特',
    'scottdj': '斯科特',
    'scottqm': '斯科特',
    'scottzy': '斯科特',
    'dahlia': '大丽花',
    'siobhan': '茜芭娜',
    'cerces': '瑟西丝',
    'cercesnpc': '瑟西丝',
    'cerydra': '刻律德菈',
    'empedocles': '恩培多克勒',
    'ianos': '伊阿诺斯',
    'philia': '菲莉亚',
    'pythias': '皮提亚斯',
    'mnestia': '涅斯提亚',
    'evernight': '永夜',
    'phantylia': '幻胧',
    'echo': '回音',
    'elio': '艾利欧',
    'dennis': '丹尼斯',
    'grady': '格雷迪',
    'woolsey': '伍尔西',
    'tiernan': '蒂尔南',
    'giovanni': '乔瓦尼',
    'edward': '爱德华',
    'joshua': '约书亚',
    'thomas': '托马斯',
    'eric': '埃里克',
    'alina': '阿丽娜',
    'oldgoethe': '老歌德',
    'galba': '加尔巴',
    'dobra': '多布拉',
    'gertie': '格蒂',
    'livia': '莉维娅',
    'woolsey': '伍尔西',
    'katrina': '卡特琳娜',
    'granholm': '格兰霍姆',
    'wildfiremumberA': '地火成员',
    'handrake': '汉德拉克',
    'hieronymus': '希罗尼穆斯',
    'oldoti': '奥蒂',
    'oldotisp': '奥蒂',
    'kalvpusuo': '卡尔普索',
    'weiertusi': '维尔特斯',
    'gelisha': '格丽莎',
    'weijiniya': '维吉妮亚',
    'nuodusi': '诺尔多斯',
    'demiteli': '德米特里',
    'tuolemi': '托勒密',
    'suolabisi': '索拉比斯',
    'labinusi': '拉比努斯',
    'gelaweitasi': '格拉维塔斯',
    'khaslana': '卡斯兰娜',
    'ambassador': '使者',
    'messenger': '信使',
}


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
        self._searchBackend = None
        self.conn.create_function("REGEXP", 2, self._regexp)
        self._detectSearchBackend()

    @staticmethod
    def _regexp(pattern, string):
        if string is None:
            return 0
        return 1 if re.search(pattern, string, re.IGNORECASE) else 0

    def _detectSearchBackend(self):
        try:
            self.conn.execute("CREATE VIRTUAL TABLE temp._fts_trigram_test USING fts5(content, tokenize='trigram')")
            self.conn.execute("DROP TABLE temp._fts_trigram_test")
            exists = self.conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='textMapFts'").fetchone()
            self._searchBackend = "fts_trigram" if exists is not None else "like"
        except sqlite3.Error:
            self._searchBackend = "like"
        log.info(f"game={self._game} searchBackend={self._searchBackend}")

    @staticmethod
    def _escapeFtsPhrase(text: str):
        return '"' + text.replace('"', '""') + '"'

    def _selectTextMapFromKeywordLike(self, keyWord: str, langCode: int, limit: int):
        with closing(self.conn.cursor()) as cursor:
            sql1 = f"select hash, content from textMap where lang=? and content like ? limit {limit}"
            cursor.execute(sql1, (langCode, '%{}%'.format(keyWord)))
            return cursor.fetchall()

    def _selectTextMapFromKeywordFts(self, keyWord: str, langCode: int, limit: int):
        with closing(self.conn.cursor()) as cursor:
            sql = f"""select t.hash, t.content
                      from textMapFts f join textMap t on t.id = f.rowid
                      where textMapFts match ? and t.lang = ? and t.content like ?
                      limit {limit}"""
            cursor.execute(sql, (self._escapeFtsPhrase(keyWord), langCode, '%{}%'.format(keyWord)))
            return cursor.fetchall()

    def selectTextMapFromKeyword(self, keyWord: str, langCode: int):
        keyWord = keyWord.strip()
        if keyWord == "":
            return []
        if self._searchBackend == "fts_trigram" and len(keyWord) >= 3:
            try:
                return self._selectTextMapFromKeywordFts(keyWord, langCode, 200)
            except sqlite3.Error as e:
                log.warning(f"FTS search failed, fallback to LIKE: game={self._game} keyword={keyWord} error={e}")
        return self._selectTextMapFromKeywordLike(keyWord, langCode, 200)

    def _buildWordModePatterns(self, expanded_word_groups):
        word_patterns = []
        normalized_groups = []
        for group in expanded_word_groups:
            forms = sorted(set(form.lower() for form in group if form))
            if not forms:
                continue
            normalized_groups.append(forms)
            word_patterns.append([re.compile(r'\b' + re.escape(form) + r'\b', re.IGNORECASE) for form in forms])
        return normalized_groups, word_patterns

    def _filterWordModeCandidates(self, candidates, word_patterns):
        matches = []
        for row in candidates:
            content = row[1]
            if content is None:
                continue
            if all(any(p.search(content) for p in group) for group in word_patterns):
                matches.append(row)
        return matches

    def _selectTextMapFromKeywordWordModeLike(self, normalized_groups, langCode):
        with closing(self.conn.cursor()) as cursor:
            like_conditions = []
            like_params = []
            for group in normalized_groups:
                group_conditions = []
                for form in group:
                    group_conditions.append("content LIKE ?")
                    like_params.append('%{}%'.format(form))
                like_conditions.append("(" + " OR ".join(group_conditions) + ")")

            where_clause = " AND ".join(like_conditions)
            sql = f"select hash, content from textMap where lang=? and ({where_clause}) limit 2000"
            cursor.execute(sql, [langCode] + like_params)
            return cursor.fetchall()

    def _selectTextMapFromKeywordWordModeFts(self, normalized_groups, langCode):
        with closing(self.conn.cursor()) as cursor:
            group_queries = []
            for group in normalized_groups:
                group_queries.append("(" + " OR ".join(self._escapeFtsPhrase(form) for form in group if len(form) >= 3) + ")")
            if not group_queries or any(query == "()" for query in group_queries):
                return self._selectTextMapFromKeywordWordModeLike(normalized_groups, langCode)
            match_query = " AND ".join(group_queries)
            sql = """select t.hash, t.content
                     from textMapFts f join textMap t on t.id = f.rowid
                     where textMapFts match ? and t.lang = ?
                     limit 2000"""
            cursor.execute(sql, (match_query, langCode))
            return cursor.fetchall()

    def selectTextMapFromKeywordWordMode(self, expanded_word_groups, langCode):
        normalized_groups, word_patterns = self._buildWordModePatterns(expanded_word_groups)
        if not normalized_groups:
            return []
        if self._searchBackend == "fts_trigram":
            try:
                candidates = self._selectTextMapFromKeywordWordModeFts(normalized_groups, langCode)
            except sqlite3.Error as e:
                log.warning(f"FTS word search failed, fallback to LIKE: game={self._game} error={e}")
                candidates = self._selectTextMapFromKeywordWordModeLike(normalized_groups, langCode)
        else:
            candidates = self._selectTextMapFromKeywordWordModeLike(normalized_groups, langCode)
        return self._filterWordModeCandidates(candidates, word_patterns)

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

    @staticmethod
    def _extractCharIdFromVoicePath(voicePath: str) -> 'str | None':
        if not voicePath:
            return None
        parts = voicePath.split('_')
        if len(parts) >= 4 and parts[0].startswith('chapter'):
            return parts[2]
        if len(parts) >= 3 and parts[0] == 'vo':
            return parts[1]
        return None

    @staticmethod
    def _charIdToDisplayName(charId: str) -> str:
        if not charId:
            return None
        return _VOICE_PATH_CHAR_MAP.get(charId) or _VOICE_PATH_CHAR_MAP.get(charId.lower())

    def _resolveTalkerName(self, talkerNameHash, voicePath, langCode: int = 1, batchTalkerNames: dict | None = None) -> 'str | None':
        if talkerNameHash is not None:
            if batchTalkerNames is not None:
                talkerName = batchTalkerNames.get(str(talkerNameHash))
                if talkerName:
                    return talkerName
            else:
                talkerNames = self.selectTextMapFromTextHash(str(talkerNameHash), [langCode])
                if len(talkerNames) > 0 and talkerNames[0][0]:
                    return talkerNames[0][0]
        charId = self._extractCharIdFromVoicePath(voicePath)
        displayName = self._charIdToDisplayName(charId)
        if displayName:
            return displayName
        return charId

    def getTalkerNameFromVoice(self, dialogueId, langCode: int = 1) -> 'str | None':
        with closing(self.conn.cursor()) as cursor:
            cursor.execute('SELECT d.talkerNameHash, v.voicePath FROM dialogue d LEFT JOIN voice v ON v.dialogueId=d.dialogueId WHERE d.dialogueId=?', (dialogueId,))
            row = cursor.fetchone()
            if row is None:
                return None
            talkerNameHash, voicePath = row
            return self._resolveTalkerName(talkerNameHash, voicePath, langCode)

    def batchGetTalkerNameFromVoice(self, dialogueIds: list, langCode: int = 1) -> dict:
        if not dialogueIds:
            return {}
        with closing(self.conn.cursor()) as cursor:
            placeholders = ','.join(['?'] * len(dialogueIds))
            cursor.execute(
                f'SELECT d.dialogueId, d.talkerNameHash, v.voicePath FROM dialogue d LEFT JOIN voice v ON v.dialogueId = d.dialogueId WHERE d.dialogueId IN ({placeholders})',
                dialogueIds,
            )
            rows = cursor.fetchall()
            talkerNameHashes = [str(row[1]) for row in rows if row[1] is not None]
            batchTalkerNames = {}
            if talkerNameHashes:
                langStr = str(langCode)
                hashPlaceholders = ','.join(['?'] * len(talkerNameHashes))
                cursor.execute(
                    f'SELECT hash, content FROM textMap WHERE hash IN ({hashPlaceholders}) AND lang = {langStr}',
                    talkerNameHashes,
                )
                for talkerHash, content in cursor.fetchall():
                    batchTalkerNames[str(talkerHash)] = content
            result = {}
            for row in rows:
                dialogueId, talkerNameHash, voicePath = row
                talkerName = self._resolveTalkerName(talkerNameHash, voicePath, langCode, batchTalkerNames)
                if talkerName is not None:
                    result[dialogueId] = talkerName
            return result

    def getTalkQuestId(self, talkId: int) -> int | None:
        with closing(self.conn.cursor()) as cursor:
            sql2 = ('select quest.questId from questTalk, quest '
                    'where talkId=? and quest.questId=questTalk.questId')
            cursor.execute(sql2, (talkId,))
            ans2 = cursor.fetchall()
            if len(ans2) == 0:
                if self._game == "starrail":
                    derivedQuestId = talkId // 100
                    cursor.execute('select questId from quest where questId=?', (derivedQuestId,))
                    derived = cursor.fetchone()
                    if derived is not None:
                        return derived[0]
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

    def getTalkContent(self, talkId: int, coopQuestId: 'int | None', game: str = "genshin") -> 'list[tuple[int, str, int, int]] | None':
        with closing(self.conn.cursor()) as cursor:
            if game == "starrail":
                cursor.execute('SELECT questId FROM questTalk WHERE talkId=?', (talkId,))
                questRow = cursor.fetchone()
                if questRow is None:
                    talkGroupId = talkId // 100
                    sql1 = 'select textHash, talkerType, talkerId, dialogueId from dialogue where talkId between ? and ? order by talkId'
                    cursor.execute(sql1, (talkGroupId * 100, talkGroupId * 100 + 99))
                    ans = cursor.fetchall()
                else:
                    questId = questRow[0]
                    cursor.execute('SELECT talkId FROM questTalk WHERE questId=?', (questId,))
                    talkIds = [r[0] for r in cursor.fetchall()]
                    if not talkIds:
                        talkGroupId = talkId // 100
                        sql1 = 'select textHash, talkerType, talkerId, dialogueId from dialogue where talkId between ? and ? order by talkId'
                        cursor.execute(sql1, (talkGroupId * 100, talkGroupId * 100 + 99))
                        ans = cursor.fetchall()
                    else:
                        placeholders = ','.join(['?'] * len(talkIds))
                        sql1 = f'select textHash, talkerType, talkerId, dialogueId from dialogue where talkId in ({placeholders}) order by talkId'
                        cursor.execute(sql1, talkIds)
                        ans = cursor.fetchall()
            elif coopQuestId is None:
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
            talkerNameHashes = set()
            if self._game == "starrail":
                sql = f"""select d.textHash, d.talkerType, d.talkerId, d.talkId, d.coopQuestId, d.talkerNameHash, v.voicePath
                          from dialogue d left join voice v on v.dialogueId = d.dialogueId where d.textHash in ({placeholders})"""
                cursor.execute(sql, textHashes)
                dialogueRows = cursor.fetchall()
            else:
                sql = f"""select d.textHash, d.talkerType, d.talkerId, d.talkId, d.coopQuestId, null as talkerNameHash, null as voicePath
                          from dialogue d where d.textHash in ({placeholders})"""
                cursor.execute(sql, textHashes)
                dialogueRows = cursor.fetchall()

            talkIds = set()
            npcIds = set()
            for row in dialogueRows:
                talkIds.add(row[3])
                if row[1] == "TALK_ROLE_NPC":
                    npcIds.add(row[2])
                if row[5] is not None:
                    talkerNameHashes.add(str(row[5]))

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

            talkerNamesByHash = {}
            if talkerNameHashes:
                talkerPlaceholders = ','.join(['?'] * len(talkerNameHashes))
                sqlTalker = f"select hash, content from textMap where hash in ({talkerPlaceholders}) and lang = ?"
                cursor.execute(sqlTalker, list(talkerNameHashes) + [langCode])
                for r in cursor.fetchall():
                    talkerNamesByHash[str(r[0])] = r[1]

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
                talkerNameHash = row[5]
                voicePath = row[6]

                talkerName = None
                if self._game == "starrail":
                    talkerName = self._resolveTalkerName(talkerNameHash, voicePath, langCode, talkerNamesByHash)
                elif talkerType == "TALK_ROLE_NPC":
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
