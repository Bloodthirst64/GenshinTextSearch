import requests
import json
import os
import re
import time

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'server', 'lyrics_data.json')
SCRAPED_IDS_PATH = os.path.join(os.path.dirname(__file__), 'scraped_ids.json')

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://music.163.com/",
}

# 艺人ID → 游戏分类，从各游戏专属页面获取的歌曲直接归入对应游戏
ARTIST_GAME_MAP = {
    33322908: "genshin",       # 原神
    50971173: "starrail",      # 崩坏：星穹铁道
    12487174: None,            # HOYO-MiX 主账号，需从专辑名判断游戏
}

# HOYO-MiX 主账号下的专辑名关键词 → 游戏分类
ALBUM_GAME_KEYWORDS = [
    (["原神", "Genshin"], "genshin"),
    (["崩坏：星穹铁道", "崩坏星穹铁道", "Honkai Star Rail", "星穹铁道"], "starrail"),
    (["绝区零", "Zenless Zone Zero"], "zzz"),
    (["崩坏3", "崩坏3rd", "Honkai Impact 3rd", "崩坏学园2"], "bh3"),
    (["未定事件簿", "Tears of Themis"], "tot"),
]

# HOYO-MiX 主账号下不含游戏名的专辑 → 游戏分类（精确匹配）
ALBUM_EXACT_MAP = {
    # 原神
    "轻涟 La vaguelette": "genshin",
    "Da Capo": "genshin",
    "Cheer Up": "genshin",
    "「飞彩镌流年」游戏原声EP专辑": "genshin",
    "Hidden Heart": "genshin",
    "Incarnation": "genshin",
    # 崩坏3
    "TruE": "bh3",
    "Regression": "bh3",
    "Oracle": "bh3",
    "Moon Halo": "bh3",
    "Starfall": "bh3",
    "Rubia": "bh3",
    # 未定事件簿
    "Where the Heart Belongs": "tot",
    "未定的注定": "tot",
}

KV_PATTERN = re.compile(r'^[^：:]+[：:]\s*.+$')
INSTRUMENTAL_KEYWORDS = ["伴奏", "Instrumental", "instrumental", "Inst.", "纯音乐", "Off Vocal", "karaoke"]


def detect_game_from_album(album_name):
    if album_name in ALBUM_EXACT_MAP:
        return ALBUM_EXACT_MAP[album_name]
    for keywords, game in ALBUM_GAME_KEYWORDS:
        for kw in keywords:
            if kw in album_name:
                return game
    return None


def fetch_artist_albums(artist_id):
    all_albums = []
    offset = 0
    while True:
        resp = requests.get(
            f"https://music.163.com/api/artist/albums/{artist_id}",
            params={"limit": 50, "offset": offset},
            headers=headers,
            timeout=15,
        )
        data = resp.json()
        albums = data.get("hotAlbums", [])
        if not albums:
            break
        all_albums.extend(albums)
        offset += 50
        if len(albums) < 50:
            break
        time.sleep(0.3)
    return all_albums


def fetch_album_songs(album_id):
    resp = requests.get(
        f"https://music.163.com/api/v1/album/{album_id}",
        headers=headers,
        timeout=15,
    )
    data = resp.json()
    return data.get("songs", [])


def fetch_lyrics(song_id):
    resp = requests.get(
        "https://music.163.com/api/song/lyric",
        params={"id": song_id, "lv": 1, "kv": 1, "tv": -1},
        headers=headers,
        timeout=15,
    )
    data = resp.json()
    return data.get("lrc", {}).get("lyric", "")


def clean_lyrics(raw_lrc):
    """去除时间标签和元数据行，只保留纯歌词"""
    lines = []
    for line in raw_lrc.split("\n"):
        cleaned = re.sub(r"\[\d+:\d+\.\d+\]", "", line).strip()
        if cleaned:
            lines.append(cleaned)
    # 分离：元数据行(key:value) vs 纯歌词行
    lyric_lines = [l for l in lines if not KV_PATTERN.match(l)]
    return lyric_lines, lines


def load_existing_data():
    """加载已有数据，返回 (songs_by_key, scraped_ids)"""
    songs_by_key = {}
    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            for song in data:
                key = (song.get("title", ""), song.get("game", ""))
                songs_by_key[key] = song
        except Exception:
            pass

    scraped_ids = set()
    if os.path.exists(SCRAPED_IDS_PATH):
        try:
            with open(SCRAPED_IDS_PATH, "r", encoding="utf-8") as f:
                scraped_ids = set(json.load(f))
        except Exception:
            pass

    return songs_by_key, scraped_ids


def main():
    print("=" * 60)
    print("HOYO-MiX Lyrics Scraper (Incremental)")
    print("=" * 60)

    existing, scraped_ids = load_existing_data()
    print(f"Existing songs: {len(existing)}")
    print(f"Already scraped song IDs: {len(scraped_ids)}")

    # Step 1: 收集所有专辑，记录每首歌对应的游戏
    print("\n[Step 1] Collecting all albums and songs from artist pages...")

    # song_id → game 的映射，优先使用游戏专属页面的分类
    song_game_map = {}
    # song_id → (name, artists, album) 的映射
    song_info_map = {}

    # 先处理游戏专属页面（分类更准确）
    for artist_id, game in ARTIST_GAME_MAP.items():
        if game is None:
            continue  # HOYO-MiX 主账号最后处理
        print(f"\n  Fetching albums for artist_id={artist_id} (game={game})")
        albums = fetch_artist_albums(artist_id)
        print(f"  Found {len(albums)} albums")

        for album in albums:
            album_id = album.get("id")
            album_name = album.get("name", "")
            songs = fetch_album_songs(album_id)
            for s in songs:
                sid = s.get("id")
                name = s.get("name", "")
                artists = ", ".join([a.get("name", "") for a in s.get("artists", [])])
                song_game_map[sid] = game  # 游戏专属页面的分类优先
                song_info_map[sid] = (name, artists, album_name)
            time.sleep(0.3)

    # 再处理 HOYO-MiX 主账号（只补充不在游戏专属页面中的歌曲）
    print(f"\n  Fetching albums for HOYO-MiX main account (id={12487174})")
    albums = fetch_artist_albums(12487174)
    print(f"  Found {len(albums)} albums")

    for album in albums:
        album_id = album.get("id")
        album_name = album.get("name", "")
        songs = fetch_album_songs(album_id)
        for s in songs:
            sid = s.get("id")
            name = s.get("name", "")
            artists = ", ".join([a.get("name", "") for a in s.get("artists", [])])
            if sid not in song_game_map:
                # 从专辑名推断游戏
                game = detect_game_from_album(album_name)
                song_game_map[sid] = game
            if sid not in song_info_map:
                song_info_map[sid] = (name, artists, album_name)
        time.sleep(0.3)

    unique_ids = list(song_game_map.keys())
    print(f"\n  Total unique songs: {len(unique_ids)}")

    # Step 2: 增量获取歌词（按 song_id 去重，爬过的直接跳过）
    print("\n[Step 2] Fetching lyrics (incremental by song_id)...")

    new_count = 0
    skip_count = 0
    for i, song_id in enumerate(unique_ids):
        # 增量：已检查过的 song_id 直接跳过
        if song_id in scraped_ids:
            skip_count += 1
            continue

        name, artists, album_name = song_info_map[song_id]
        game = song_game_map[song_id]

        # 无论结果如何，标记为已检查
        scraped_ids.add(song_id)

        if not game:
            continue  # 无法分类的跳过

        if any(kw in name for kw in INSTRUMENTAL_KEYWORDS):
            continue

        if i % 200 == 0:
            print(f"  [{i+1}/{len(unique_ids)}] Processing...")

        try:
            raw_lrc = fetch_lyrics(song_id)
            if not raw_lrc:
                continue

            lyric_lines, all_lines = clean_lyrics(raw_lrc)

            if len(lyric_lines) < 3:
                continue

            key = (name, game)
            existing[key] = {
                "title": name,
                "game": game,
                "album": album_name,
                "composer": "",
                "lyricist": "",
                "singer": artists,
                "lyrics": "\n".join(lyric_lines),
                "source": "netease",
                "_netease_id": song_id,
            }
            new_count += 1
        except Exception:
            pass
        time.sleep(0.1)

    print(f"\n  New songs added: {new_count}")
    print(f"  Already scraped (skipped): {skip_count}")

    # Step 3: 保存（不输出 _netease_id 到最终文件）
    print("\n[Step 3] Saving...")

    output = []
    for song in existing.values():
        clean = {k: v for k, v in song.items() if not k.startswith("_")}
        output.append(clean)

    output.sort(key=lambda x: (x["game"], x["title"]))

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    with open(SCRAPED_IDS_PATH, "w", encoding="utf-8") as f:
        json.dump(list(scraped_ids), f)

    print(f"\nDone! Saved {len(output)} songs with lyrics")
    for game in sorted(set(s["game"] for s in output)):
        count = sum(1 for s in output if s["game"] == game)
        print(f"  {game}: {count} songs")


if __name__ == "__main__":
    main()
