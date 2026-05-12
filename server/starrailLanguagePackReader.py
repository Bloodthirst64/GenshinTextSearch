import os
import pickle
import struct
import sys

from AudioReader.FilePackager import Package
import config

_anime_wwise_path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'AnimeWwise'))
_cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.starrail_voice_cache.pkl')

langCodes = {
    1: "Chinese(PRC)",
    4: "English",
    9: "Japanese",
    10: "Korean"
}

langPackages: 'dict[int, Package]' = {}
_voicePathToHash: 'dict[str, dict[int, int]]' = {}
_hashToLangId: 'dict[int, int]' = {}
_loaded = False


def _loadMapperFromCache():
    global _voicePathToHash
    if not os.path.exists(_cache_path):
        return False
    try:
        with open(_cache_path, 'rb') as f:
            _voicePathToHash = pickle.load(f)
        print(f"Loaded {len(_voicePathToHash)} voice path mappings from cache")
        return True
    except Exception:
        return False


def _saveMapperToCache():
    try:
        with open(_cache_path, 'wb') as f:
            pickle.dump(_voicePathToHash, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception:
        pass


def _loadMapper():
    global _voicePathToHash
    if _loadMapperFromCache():
        return

    map_path = os.path.join(_anime_wwise_path, 'maps', 'hkrpg.map')
    if not os.path.exists(map_path):
        print("hkrpg.map not found, starrail voice playback will not work")
        return

    if _anime_wwise_path not in sys.path:
        sys.path.insert(0, _anime_wwise_path)

    try:
        from mapper import Mapper
    except ImportError:
        print("Failed to import AnimeWwise mapper, starrail voice playback will not work")
        return

    mapper = Mapper(map_path)

    mapperLangToCode = {}
    for i, lang_name in enumerate(mapper.languages):
        if lang_name == "Chinese(PRC)":
            mapperLangToCode[i] = 1
        elif lang_name.startswith("English"):
            mapperLangToCode[i] = 4
        elif lang_name == "Japanese":
            mapperLangToCode[i] = 9
        elif lang_name == "Korean":
            mapperLangToCode[i] = 10

    for key_hex in mapper.keys:
        result = mapper.get_key(key_hex)
        if result and len(result) >= 1:
            path = result[0]
            name = path.split('\\')[-1].lower()
            if name.endswith('.wem'):
                name = name[:-4]

            packed = mapper.keys[key_hex]
            lang_idx = (packed >> 22) & 0x03
            lang_code = mapperLangToCode.get(lang_idx)

            if lang_code is not None:
                key_bytes = bytes.fromhex(key_hex)
                hash_val = struct.unpack('>Q', key_bytes)[0]

                if name not in _voicePathToHash:
                    _voicePathToHash[name] = {}
                _voicePathToHash[name][lang_code] = hash_val

    mapper.reset()
    print(f"Loaded {len(_voicePathToHash)} voice path to hash mappings")
    _saveMapperToCache()


def loadLangPackages():
    global _loaded, _hashToLangId
    if _loaded:
        return
    _loaded = True

    starrail_path = config.getAssetDir("starrail")
    if not starrail_path:
        return

    _loadMapper()

    pkg = Package()
    loaded_langs = set()

    persistent_path = os.path.join(starrail_path, "Persistent", "Audio", "AudioPackage", "Windows")

    if os.path.exists(persistent_path):
        for code, langName in langCodes.items():
            lang_dir = os.path.join(persistent_path, langName)
            if os.path.exists(lang_dir):
                has_external = False
                for fn in sorted(os.listdir(lang_dir)):
                    if fn.endswith('.pck') and fn.startswith('External'):
                        pkg.addfile(open(os.path.join(lang_dir, fn), 'rb'))
                        has_external = True
                if has_external:
                    loaded_langs.add(code)
                    print(f"loaded starrail voice pack: {langName}")

    for langid, hashmap in pkg.streamfiles_map.items():
        for hash_val in hashmap:
            _hashToLangId[hash_val] = langid

    for code in loaded_langs:
        langPackages[code] = pkg


def _getAudioHash(path: str, langCode: int):
    vp_lower = path.lower()
    if vp_lower in _voicePathToHash:
        lang_hashes = _voicePathToHash[vp_lower]
        if langCode in lang_hashes:
            return lang_hashes[langCode]
    return None


def getAudioBin(path: str, langCode: int):
    if langCode not in langPackages:
        return None

    hashVal = _getAudioHash(path, langCode)
    if hashVal is None:
        return None

    try:
        voicePack = langPackages[langCode]
        langid = _hashToLangId.get(hashVal, 0)
        wemFiles = voicePack.get_file_data_by_hash(hashVal, langid=langid, mode=2)
        wenBin, pckPath = wemFiles[0]
        return wenBin
    except (FileNotFoundError, KeyError):
        return None


def checkAudioBin(path: str, langCode: int):
    if langCode not in langPackages:
        return False

    hashVal = _getAudioHash(path, langCode)
    if hashVal is None:
        return False

    return hashVal in _hashToLangId
