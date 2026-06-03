import json
import os
import re

from logger import get_logger

log = get_logger("lyricsData")

LYRICS_DATA_PATH = os.path.join(os.path.dirname(__file__), "lyrics_data.json")

_songs = None


def _load_lyrics_data():
    global _songs
    if _songs is not None:
        return _songs

    if not os.path.exists(LYRICS_DATA_PATH):
        log.warning(f"Lyrics data file not found: {LYRICS_DATA_PATH}")
        _songs = []
        return _songs

    try:
        with open(LYRICS_DATA_PATH, "r", encoding="utf-8") as f:
            _songs = json.load(f)
        log.info(f"Loaded {len(_songs)} songs from lyrics data")
    except Exception as e:
        log.error(f"Failed to load lyrics data: {e}")
        _songs = []

    return _songs


def reload_lyrics_data():
    global _songs
    _songs = None
    return _load_lyrics_data()


def search_lyrics(keyword: str, game: str = None, limit: int = 50):
    songs = _load_lyrics_data()
    if not songs:
        return []

    keyword_lower = keyword.lower()
    results = []

    for song in songs:
        if game and song.get("game") != game:
            continue

        title = song.get("title", "")
        lyrics = song.get("lyrics", "")
        album = song.get("album", "")
        singer = song.get("singer", "")
        composer = song.get("composer", "")
        lyricist = song.get("lyricist", "")

        title_match = keyword_lower in title.lower()
        lyrics_match = keyword_lower in lyrics.lower()
        album_match = keyword_lower in album.lower()
        singer_match = keyword_lower in singer.lower()
        composer_match = keyword_lower in composer.lower()
        lyricist_match = keyword_lower in lyricist.lower()

        if title_match or lyrics_match or album_match or singer_match or composer_match or lyricist_match:
            matched_lines = []
            if lyrics_match:
                for line in lyrics.split("\n"):
                    line = line.strip()
                    if line and keyword_lower in line.lower():
                        matched_lines.append(line)
                        if len(matched_lines) >= 5:
                            break

            result = {
                "title": title,
                "game": song.get("game", "genshin"),
                "album": album,
                "composer": composer,
                "lyricist": lyricist,
                "singer": singer,
                "lyrics": lyrics,
                "matchedLines": matched_lines,
                "matchType": "title" if title_match else "lyrics" if lyrics_match else "album" if album_match else "singer" if singer_match else "composer" if composer_match else "lyricist",
            }
            results.append(result)

        if len(results) >= limit:
            break

    results.sort(key=lambda x: (
        0 if x["matchType"] == "title" else 1 if x["matchType"] == "singer" else 2 if x["matchType"] == "album" else 3,
        x["title"]
    ))

    return results


def get_all_songs(game: str = None):
    songs = _load_lyrics_data()
    if game:
        songs = [s for s in songs if s.get("game") == game]
    return [{"title": s.get("title", ""), "game": s.get("game", "genshin"), "album": s.get("album", ""), "singer": s.get("singer", "")} for s in songs]


def get_song_detail(title: str, game: str = None):
    songs = _load_lyrics_data()
    for song in songs:
        if song.get("title") == title:
            if game and song.get("game") != game:
                continue
            return song
    return None
