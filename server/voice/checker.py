from abc import ABC, abstractmethod

from voice.genshin_reader import langPackages as genshin_langPackages, langCodes as genshin_langCodes, checkAudioBin as genshin_checkAudioBin, getAudioBin as genshin_getAudioBin
from voice.starrail_reader import langPackages as starrail_langPackages, langCodes as starrail_langCodes, checkAudioBin as starrail_checkAudioBin, getAudioBin as starrail_getAudioBin, loadLangPackages as starrail_loadLangPackages, _availableLangs as starrail_availableLangs


class VoicePackChecker(ABC):
    """语音包检查器抽象基类，统一不同游戏的语音包操作接口"""

    @abstractmethod
    def ensure_loaded(self) -> None:
        """确保语言包已加载"""

    @abstractmethod
    def get_lang_packages(self) -> dict:
        """获取已加载的语言包字典"""

    @abstractmethod
    def get_lang_codes(self) -> dict:
        """获取语言代码到名称的映射"""

    @abstractmethod
    def check_audio_bin(self, voice_path: str, lang_code: int) -> bool:
        """检查指定语言的音频文件是否存在"""

    @abstractmethod
    def get_audio_bin(self, voice_path: str, lang_code: int):
        """获取指定语言的音频二进制数据"""

    @abstractmethod
    def has_available_langs(self) -> bool:
        """是否有可用的语言（语言包未加载时的降级判断）"""

    def check_voice_exists(self, voice_path: str, langs: list[int]) -> bool:
        """检查语音文件是否在任一语言中存在"""
        for lang in langs:
            if lang in self.get_lang_packages() and self.check_audio_bin(voice_path, lang):
                return True
        return False

    def should_append_voice(self, voice_path: str, langs: list[int]) -> bool:
        """判断是否应将语音路径加入结果列表"""
        if self.get_lang_packages():
            return self.check_voice_exists(voice_path, langs)
        return self.has_available_langs()

    def get_loaded_voice_packs(self) -> dict:
        """获取已加载的语音包信息 {code: name}"""
        if self.get_lang_packages():
            return {code: self.get_lang_codes()[code] for code in self.get_lang_packages()}
        if self.has_available_langs():
            return self._get_available_lang_info()
        return {}

    def _get_available_lang_info(self) -> dict:
        """获取可用语言信息（子类可覆写）"""
        return {}


class GenshinVoicePackChecker(VoicePackChecker):

    def ensure_loaded(self) -> None:
        # 原神语言包在模块导入时已加载
        pass

    def get_lang_packages(self) -> dict:
        return genshin_langPackages

    def get_lang_codes(self) -> dict:
        return genshin_langCodes

    def check_audio_bin(self, voice_path: str, lang_code: int) -> bool:
        return genshin_checkAudioBin(voice_path, lang_code)

    def get_audio_bin(self, voice_path: str, lang_code: int):
        return genshin_getAudioBin(voice_path, lang_code)

    def has_available_langs(self) -> bool:
        return bool(genshin_langPackages)


class StarrailVoicePackChecker(VoicePackChecker):

    def ensure_loaded(self) -> None:
        starrail_loadLangPackages()

    def get_lang_packages(self) -> dict:
        return starrail_langPackages

    def get_lang_codes(self) -> dict:
        return starrail_langCodes

    def check_audio_bin(self, voice_path: str, lang_code: int) -> bool:
        return starrail_checkAudioBin(voice_path, lang_code)

    def get_audio_bin(self, voice_path: str, lang_code: int):
        return starrail_getAudioBin(voice_path, lang_code)

    def has_available_langs(self) -> bool:
        return bool(starrail_availableLangs)

    def _get_available_lang_info(self) -> dict:
        return {code: starrail_langCodes[code] for code in starrail_availableLangs}


_checkers = {
    "genshin": GenshinVoicePackChecker,
    "starrail": StarrailVoicePackChecker,
}


def get_checker(game: str) -> VoicePackChecker:
    """根据游戏类型获取对应的语音包检查器"""
    checker_class = _checkers.get(game)
    if checker_class is None:
        raise ValueError(f"Unsupported game type: {game}")
    return checker_class()
