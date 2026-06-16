import os
import json
import sqlite3
from tqdm import tqdm
from searchIndex import rebuild_search_index

DATA_PATH = os.path.join(os.path.dirname(__file__), "starrail-data")
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "starrail-data.db")

LANG_MAP = [
    (1, "TextMapCHS.json", "简体中文"),
    (2, "TextMapCHT.json", "繁體中文"),
    (3, "TextMapDE.json", "Deutsch"),
    (4, "TextMapEN.json", "English"),
    (5, "TextMapES.json", "Español"),
    (6, "TextMapFR.json", "Français"),
    (7, "TextMapID.json", "Bahasa Indonesia"),
    (8, "TextMapJP.json", "日本語"),
    (9, "TextMapKR.json", "한국어"),
    (10, "TextMapPT.json", "Português"),
    (11, "TextMapRU.json", "Русский язык"),
    (12, "TextMapTH.json", "ภาษาไทย"),
    (13, "TextMapVI.json", "Tiếng Việt"),
    (14, "TextMapMainCHS.json", "简体中文(主线)"),
    (15, "TextMapMainCHT.json", "繁體中文(主线)"),
    (16, "TextMapMainDE.json", "Deutsch(主线)"),
    (17, "TextMapMainEN.json", "English(主线)"),
    (18, "TextMapMainES.json", "Español(主线)"),
    (19, "TextMapMainFR.json", "Français(主线)"),
    (20, "TextMapMainID.json", "Bahasa Indonesia(主线)"),
    (21, "TextMapMainJP.json", "日本語(主线)"),
    (22, "TextMapMainKR.json", "한국어(主线)"),
    (23, "TextMapMainPT.json", "Português(主线)"),
    (24, "TextMapMainRU.json", "Русский язык(主线)"),
    (25, "TextMapMainTH.json", "ภาษาไทย(主线)"),
    (26, "TextMapMainVI.json", "Tiếng Việt(主线)"),
]

SPLIT_LANG_FILES = {
    9: ["TextMapKR_0.json", "TextMapKR_1.json"],
    11: ["TextMapRU_0.json", "TextMapRU_1.json"],
    12: ["TextMapTH_0.json", "TextMapTH_1.json"],
}


def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    ddl_path = os.path.join(os.path.dirname(__file__), "starrailDDL.sql")
    with open(ddl_path, "r", encoding="utf-8") as f:
        ddl = f.read()
    cursor = conn.cursor()
    cursor.executescript(ddl)
    cursor.execute("DELETE FROM langCode")
    for lang_id, code_name, display_name in LANG_MAP:
        cursor.execute(
            "INSERT OR IGNORE INTO langCode (id, codeName, displayName, imported) VALUES (?, ?, ?, 0)",
            (lang_id, code_name, display_name),
        )
    conn.commit()
    cursor.close()
    return conn


def import_text_map(conn):
    cursor = conn.cursor()
    sql = "INSERT OR IGNORE INTO textMap(hash, content, lang) VALUES (?,?,?)"
    for lang_id, code_name, display_name in LANG_MAP:
        print(f"Importing {code_name}...")
        if lang_id in SPLIT_LANG_FILES:
            files = SPLIT_LANG_FILES[lang_id]
        else:
            files = [code_name]
        imported = False
        for file_name in files:
            file_path = os.path.join(DATA_PATH, "TextMap", file_name)
            if not os.path.exists(file_path):
                print(f"  File not found: {file_name}, skipping")
                continue
            text_map = json.load(open(file_path, "r", encoding="utf-8"))
            for hash_val, content in tqdm(text_map.items(), total=len(text_map), desc=file_name):
                cursor.execute(sql, (hash_val, content, lang_id))
            imported = True
        if imported:
            cursor.execute("UPDATE langCode SET imported=1 WHERE id=?", (lang_id,))
        conn.commit()
    cursor.close()


def import_avatars(conn):
    cursor = conn.cursor()
    file_path = os.path.join(DATA_PATH, "ExcelOutput", "AvatarConfig.json")
    avatars = json.load(open(file_path, "r", encoding="utf-8"))
    sql = "INSERT OR IGNORE INTO avatar(avatarId, nameTextMapHash) VALUES (?,?)"
    for avatar in tqdm(avatars, total=len(avatars)):
        avatar_id = avatar.get("AvatarID")
        name_hash = avatar.get("AvatarName", {}).get("Hash")
        if avatar_id is not None and name_hash is not None:
            cursor.execute(sql, (avatar_id, str(name_hash)))
    conn.commit()
    cursor.close()


def import_npcs(conn):
    cursor = conn.cursor()
    file_path = os.path.join(DATA_PATH, "ExcelOutput", "NPCData.json")
    npcs = json.load(open(file_path, "r", encoding="utf-8"))
    sql = "INSERT OR IGNORE INTO npc(npcId, textHash) VALUES (?,?)"
    for npc in tqdm(npcs, total=len(npcs)):
        npc_id = npc.get("ID")
        npc_name_hash = npc.get("DefaultNPCName", {}).get("Hash")
        if npc_id is not None:
            cursor.execute(sql, (npc_id, str(npc_name_hash) if npc_name_hash is not None else None))
    conn.commit()
    cursor.close()


def import_dialogue(conn):
    cursor = conn.cursor()
    file_path = os.path.join(DATA_PATH, "ExcelOutput", "TalkSentenceConfig.json")
    dialogues = json.load(open(file_path, "r", encoding="utf-8"))
    sql = "INSERT OR IGNORE INTO dialogue(talkId, textHash, talkerNameHash, dialogueId) VALUES (?,?,?,?)"
    for entry in tqdm(dialogues, total=len(dialogues)):
        talk_id = entry.get("TalkSentenceID")
        text_hash = entry.get("TalkSentenceText", {}).get("Hash")
        talker_name_hash = entry.get("TextmapTalkSentenceName", {}).get("Hash")
        voice_id = entry.get("VoiceID")
        if talk_id is not None and text_hash is not None:
            cursor.execute(
                sql,
                (
                    talk_id,
                    str(text_hash),
                    str(talker_name_hash) if talker_name_hash is not None else None,
                    voice_id,
                ),
            )
    conn.commit()
    cursor.close()


def import_fetters(conn):
    cursor = conn.cursor()
    file_path = os.path.join(DATA_PATH, "ExcelOutput", "VoiceAtlas.json")
    fetters = json.load(open(file_path, "r", encoding="utf-8"))
    sql = "INSERT OR IGNORE INTO fetters(avatarId, voiceTitleTextMapHash, voiceFileTextTextMapHash, voiceFile) VALUES (?,?,?,?)"
    for fetter in tqdm(fetters, total=len(fetters)):
        avatar_id = fetter.get("AvatarID")
        voice_title_hash = fetter.get("VoiceTitle", {}).get("Hash")
        voice_file_hash = fetter.get("Voice_M", {}).get("Hash")
        audio_id = fetter.get("AudioID")
        if avatar_id is not None:
            cursor.execute(
                sql,
                (
                    avatar_id,
                    str(voice_title_hash) if voice_title_hash is not None else None,
                    str(voice_file_hash) if voice_file_hash is not None else None,
                    audio_id,
                ),
            )
    conn.commit()
    cursor.close()


def import_quests(conn):
    cursor = conn.cursor()
    file_path = os.path.join(DATA_PATH, "ExcelOutput", "MainMission.json")
    quests = json.load(open(file_path, "r", encoding="utf-8"))
    sql = "INSERT OR IGNORE INTO quest(questId, titleTextMapHash, chapterId) VALUES (?,?,?)"
    for quest in tqdm(quests, total=len(quests)):
        quest_id = quest.get("MainMissionID")
        title_hash = quest.get("Name", {}).get("Hash")
        chapter_id = quest.get("ChapterID")
        if chapter_id == 0:
            chapter_id = None
        if quest_id is not None:
            cursor.execute(
                sql,
                (
                    quest_id,
                    str(title_hash) if title_hash is not None else None,
                    chapter_id,
                ),
            )
    conn.commit()
    cursor.close()


def import_quest_talk(conn):
    cursor = conn.cursor()
    file_path = os.path.join(DATA_PATH, "ExcelOutput", "TalkSentenceConfig.json")
    dialogues = json.load(open(file_path, "r", encoding="utf-8"))
    quest_path = os.path.join(DATA_PATH, "ExcelOutput", "MainMission.json")
    quests = json.load(open(quest_path, "r", encoding="utf-8"))
    main_mission_ids = set(q.get("MainMissionID") for q in quests)

    # Also load SubMission data to improve matching
    sub_mission_path = os.path.join(DATA_PATH, "ExcelOutput", "SubMission.json")
    sub_mission_ids = set()
    sub_to_main = {}
    if os.path.exists(sub_mission_path):
        sub_missions = json.load(open(sub_mission_path, "r", encoding="utf-8"))
        for sm in sub_missions:
            sm_id = sm.get("SubMissionID")
            if sm_id is not None:
                sub_mission_ids.add(sm_id)
                # Derive MainMissionID from SubMissionID (typically first 7 digits)
                s = str(sm_id)
                if len(s) >= 7:
                    sub_to_main[sm_id] = int(s[:7])

    sql = "INSERT OR IGNORE INTO questTalk(questId, talkId) VALUES (?,?)"
    count = 0
    for entry in tqdm(dialogues, total=len(dialogues), desc="questTalk"):
        talk_id = entry.get("TalkSentenceID")
        if talk_id is None:
            continue
        s = str(talk_id)
        candidates = [talk_id // 100]
        if len(s) >= 7:
            candidates.append(int(s[:6] + "01"))
            # Also try first 7 digits directly (common SubMission → MainMission pattern)
            candidates.append(int(s[:7]))
        if len(s) >= 5:
            candidates.append(int(s[:5] + "01"))
        if len(s) >= 4:
            candidates.append(int(s[:4] + "01"))
        # Try more prefix lengths for better coverage
        if len(s) >= 8:
            candidates.append(int(s[:8] + "01"))
            candidates.append(talk_id // 10000 * 100 + 1)
        if len(s) >= 6:
            candidates.append(int(s[:6] + "001"))
        matched = None
        for c in candidates:
            if c in main_mission_ids:
                matched = c
                break
        # If not matched to MainMission directly, try via SubMission
        if matched is None:
            for c in candidates:
                if c in sub_mission_ids:
                    main_id = sub_to_main.get(c)
                    if main_id and main_id in main_mission_ids:
                        matched = main_id
                        break
        if matched is not None:
            cursor.execute(sql, (matched, talk_id))
            count += 1
    conn.commit()
    cursor.close()
    print(f"  Imported {count} questTalk mappings")


def import_voice(conn):
    cursor = conn.cursor()
    file_path = os.path.join(DATA_PATH, "ExcelOutput", "VoiceConfig.json")
    voices = json.load(open(file_path, "r", encoding="utf-8"))
    sql = "INSERT OR IGNORE INTO voice(dialogueId, voicePath, gameTrigger, avatarId) VALUES (?,?,?,?)"
    for voice in tqdm(voices, total=len(voices)):
        voice_id = voice.get("VoiceID")
        voice_path = voice.get("VoicePath")
        voice_type = voice.get("VoiceType")
        if voice_id is not None and voice_path is not None:
            cursor.execute(sql, (voice_id, voice_path, voice_type, 0))
    conn.commit()
    cursor.close()


def import_chapters(conn):
    cursor = conn.cursor()
    file_path = os.path.join(DATA_PATH, "ExcelOutput", "MissionChapterConfig.json")
    chapters = json.load(open(file_path, "r", encoding="utf-8"))
    sql = "INSERT OR IGNORE INTO chapter(chapterId, chapterTitleTextMapHash, chapterNumTextMapHash) VALUES (?,?,?)"
    for chapter in tqdm(chapters, total=len(chapters)):
        chapter_id = chapter.get("ID")
        chapter_name = chapter.get("ChapterName", "")
        stage_name = chapter.get("StageName", "")
        if chapter_id is not None:
            cursor.execute(
                sql,
                (
                    chapter_id,
                    chapter_name if chapter_name else None,
                    stage_name if stage_name else None,
                ),
            )
    conn.commit()
    cursor.close()


def main():
    print("Initializing database...")
    conn = init_db()
    print("Importing TextMap...")
    import_text_map(conn)
    print("Importing avatars...")
    import_avatars(conn)
    print("Importing NPCs...")
    import_npcs(conn)
    print("Importing dialogue...")
    import_dialogue(conn)
    print("Importing fetters...")
    import_fetters(conn)
    print("Importing quests...")
    import_quests(conn)
    print("Importing quest-talk mapping...")
    import_quest_talk(conn)
    print("Importing voice...")
    import_voice(conn)
    print("Importing chapters...")
    import_chapters(conn)
    print("Building search index...")
    backend, elapsed_ms = rebuild_search_index(conn)
    print(f"Search index backend={backend}, elapsed={elapsed_ms:.2f}ms")
    print("Done!")
    conn.close()


if __name__ == "__main__":
    main()
