import requests
import json
import os
import re
import time

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'server', 'lyrics_data.json')
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://music.163.com/",
}

ARTIST_IDS = [
    (12487174, "HOYO-MiX"),
    (33322908, "原神"),
    (50971173, "崩坏：星穹铁道"),
]

all_albums = []
for artist_id, artist_name in ARTIST_IDS:
    print(f"Fetching albums for: {artist_name} (id={artist_id})")
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
        for a in albums:
            all_albums.append((a.get("id"), a.get("name", ""), artist_name))
        offset += 50
        if len(albums) < 50:
            break
        time.sleep(0.3)

print(f"Total albums: {len(all_albums)}")

all_song_ids = []
for album_id, album_name, artist_name in all_albums:
    resp = requests.get(
        f"https://music.163.com/api/v1/album/{album_id}",
        headers=headers,
        timeout=15,
    )
    data = resp.json()
    songs = data.get("songs", [])
    for s in songs:
        all_song_ids.append(s.get("id"))
    time.sleep(0.3)

unique_ids = list(set(all_song_ids))
print(f"Total unique song IDs: {len(unique_ids)}")

KV_PATTERN = re.compile(r'^[^：:]+[：:]\s*.+$')
INSTRUMENTAL_KEYWORDS = ["伴奏", "Instrumental", "instrumental", "Inst.", "纯音乐", "Off Vocal", "karaoke"]

songs_with_lyrics = {}
for i, song_id in enumerate(unique_ids):
    if i % 200 == 0:
        print(f"  Processing {i+1}/{len(unique_ids)}...")
    try:
        resp = requests.get(
            f"https://music.163.com/api/song/detail",
            params={"id": song_id, "ids": f"[{song_id}]"},
            headers=headers,
            timeout=15,
        )
        data = resp.json()
        songs = data.get("songs", [])
        if not songs:
            continue
        s = songs[0]
        name = s.get("name", "")
        artists = ", ".join([a.get("name", "") for a in s.get("artists", [])])
        album = s.get("album", {}).get("name", "")

        if any(kw in name for kw in INSTRUMENTAL_KEYWORDS):
            continue

        lyrics_resp = requests.get(
            "https://music.163.com/api/song/lyric",
            params={"id": song_id, "lv": 1, "kv": 1, "tv": -1},
            headers=headers,
            timeout=15,
        )
        lyrics_data = lyrics_resp.json()
        lrc = lyrics_data.get("lrc", {}).get("lyric", "")

        if not lrc:
            continue

        lines = []
        for line in lrc.split("\n"):
            cleaned = re.sub(r"\[\d+:\d+\.\d+\]", "", line).strip()
            if cleaned:
                lines.append(cleaned)

        lyric_lines = [l for l in lines if not KV_PATTERN.match(l)]

        if len(lyric_lines) < 3:
            continue

        game = "genshin"
        text = f"{name} {album} {artists}"
        if any(kw in text for kw in ["崩坏：星穹铁道", "崩坏星穹铁道", "Honkai Star Rail", "Star Rail", "星穹铁道"]):
            game = "starrail"
        elif any(kw in text for kw in ["绝区零", "Zenless Zone Zero"]):
            game = "zzz"
        elif any(kw in text for kw in ["崩坏3", "崩坏3rd", "Honkai Impact 3rd"]):
            game = "bh3"
        elif any(kw in text for kw in ["未定事件簿", "Tears of Themis"]):
            game = "tot"

        key = (name, game)
        if key not in songs_with_lyrics:
            songs_with_lyrics[key] = {
                "title": name,
                "game": game,
                "album": album,
                "composer": "",
                "lyricist": "",
                "singer": artists,
                "lyrics": "\n".join(lyric_lines),
                "source": "netease",
            }
    except Exception:
        pass
    time.sleep(0.1)

output = sorted(songs_with_lyrics.values(), key=lambda x: (x["game"], x["title"]))

with open(DATA_PATH, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\nDone! Saved {len(output)} songs with lyrics")
for game in sorted(set(s["game"] for s in output)):
    count = sum(1 for s in output if s["game"] == game)
    print(f"  {game}: {count} songs")
