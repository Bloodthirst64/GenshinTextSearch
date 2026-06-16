import re
import databaseHelper
import config

NICKNAME_DEFAULTS = {
    "genshin": "旅行者",
    "starrail": "开拓者"
}


def replace(textMap: str, playerIsMale: bool, lang: int, game: str = "genshin"):
    db = databaseHelper.get_db(game)
    text1 = re.sub(r'\{M#(.*?)}\{F#(.*?)}', '\\1' if playerIsMale else '\\2', textMap)
    text1 = re.sub(r'\{F#(.*?)}\{M#(.*?)}', '\\2' if playerIsMale else '\\1', text1)

    if game == "genshin":
        def replaceSexPro(match: 're.Match'):
            isMate = match.group(1) == "MATE"
            if isMate == playerIsMale:
                return db.getManualTextMap(match.group(3), lang)
            else:
                return db.getManualTextMap(match.group(2), lang)

        text2 = re.sub(r'\{(.*?)AVATAR#SEXPRO\[(.*?)\|(.*?)]}', replaceSexPro, text1)

        wanderName = db.getWanderName(lang) or "流浪者"
        text3 = re.sub(r"\{REALNAME\[ID\(1\)\|HOSTONLY\(true\)]}", wanderName, text2)
    else:
        text2 = text1
        text3 = text2

    nickname = config.getNickname(game)
    if not nickname:
        nickname = db.getTravellerName(lang) or NICKNAME_DEFAULTS.get(game, "旅行者")
    if nickname == "{NICKNAME}":
        nickname = NICKNAME_DEFAULTS.get(game, "旅行者")
    text4 = re.sub(r"\{NICKNAME}", nickname, text3)

    return text4


def process_translates(translates: list[tuple[str, int]], is_male: bool, game: str = "genshin") -> dict[int, str]:
    """处理翻译列表中的占位符，返回 {langCode: content} 映射"""
    result = {}
    for content, lang in translates:
        if content.startswith("#"):
            result[lang] = replace(content, is_male, lang, game)[1:]
        elif game == "starrail" and ("{M#" in content or "{F#" in content or "{NICKNAME}" in content):
            result[lang] = replace(content, is_male, lang, game)
        else:
            result[lang] = content
    return result


if __name__ == "__main__":
    print(replace(
        "#嗯，{NICKNAME}{M#他们}{F#她们}今天也会来参加庆祝活动。\n{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_HE|INFO_FEMALE_PRONOUN_SHE]}是特别的，不需要神之眼也可以使用元素力。{REALNAME[ID(1)|HOSTONLY(true)]}",
        True, 1))
