import os

from AudioReader.FilePackager import Package, fnv_hash_64
import config

langCodes = {
    1: "Chinese(PRC)",
    4: "English",
    9: "Japanese",
    10: "Korean"
}

langPackages: 'dict[int, Package]' = {}

_loaded = False


def loadLangPackages():
    global _loaded
    if _loaded:
        return
    _loaded = True

    starrail_path = config.getAssetDir("starrail")
    if not starrail_path:
        return
    paths = [
        os.path.join(starrail_path, "Persistent", "Audio", "AudioPackage", "Windows"),
        os.path.join(starrail_path, "StreamingAssets", "Audio", "AudioPackage", "Windows")
    ]

    langToCode = {
        "Chinese(PRC)": 1,
        "English": 4,
        "Japanese": 9,
        "Korean": 10
    }
    for pathDir in paths:
        if not os.path.exists(pathDir):
            continue

        for langName, code in langToCode.items():
            if code in langPackages:
                continue
            langPackPath = os.path.join(pathDir, langName)
            if not os.path.exists(langPackPath):
                continue
            files = os.listdir(langPackPath)
            if len(files) < 10:
                continue

            voicePack = Package()
            for fileName in files:
                if not fileName.endswith('.pck'):
                    continue
                fobj = open(os.path.join(langPackPath, fileName), "rb")
                voicePack.addfile(fobj)
            langPackages[code] = voicePack

            print("loaded starrail voice pack: " + langName)


def getAudioBin(path: str, langCode: int):
    if langCode not in langCodes:
        raise "No voice-over for this language!"
    langStr = langCodes[langCode]
    hashVal = fnv_hash_64((langStr + "\\" + path).lower())
    try:
        voicePack = langPackages[langCode]

        wemFiles = voicePack.get_file_data_by_hash(hashVal, langid=0, mode=2)
        wenBin, pckPath = wemFiles[0]
        return wenBin
    except FileNotFoundError | KeyError:
        return None


def checkAudioBin(path: str, langCode: int):
    if langCode not in langPackages:
        return False
    langStr = langCodes[langCode]
    hashVal = fnv_hash_64((langStr + "\\" + path).lower())
    voicePack = langPackages[langCode]

    return voicePack.check_file_by_hash(hashVal, langid=0, mode=2)
