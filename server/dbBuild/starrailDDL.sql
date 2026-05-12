create table avatar
(
    id              integer
        constraint avatar_pk
            primary key autoincrement,
    avatarId        integer,
    nameTextMapHash text
);

create index avatar_avatarId_index
    on avatar (avatarId);

create table chapter
(
    id                      integer
        constraint chapter_pk
            primary key autoincrement,
    chapterId               integer,
    chapterTitleTextMapHash text,
    chapterNumTextMapHash   text
);

create index chapter_chapterId_index
    on chapter (chapterId);

create table dialogue
(
    id         integer
        constraint dialogue_pk
            primary key autoincrement,
    talkerType TEXT,
    talkerId   integer,
    talkId     integer,
    textHash   text,
    dialogueId integer
        constraint dialogue_pk_2
            unique,
    coopQuestId integer
);

create index dialogue_textHash_index
    on dialogue (textHash);

create table fetters
(
    id                       integer
        constraint fetters_pk
            primary key autoincrement,
    fetterId                 integer,
    avatarId                 integer,
    voiceTitleTextMapHash    text,
    voiceFileTextTextMapHash text,
    voiceFile                integer
);

create index fetters_voiceFileTextTextMapHash_index
    on fetters (voiceFileTextTextMapHash);

create index fetters_voiceFile_index
    on fetters (voiceFile);

create table langCode
(
    id          integer
        constraint langCode_pk
            primary key autoincrement,
    codeName    TEXT
        constraint langCode_pk_2
            unique,
    displayName TEXT,
    imported    INT
);

create table quest
(
    id               integer
        constraint quest_pk
            primary key autoincrement,
    questId          integer,
    titleTextMapHash text,
    chapterId        integer
);

create index quest_questId_index
    on quest (questId);

create table questTalk
(
    id      integer
        constraint questTalk_pk
            primary key autoincrement,
    questId integer,
    talkId  integer
);

create index questTalk_talkId_index
    on questTalk (talkId);

create table textMap
(
    id      integer
        constraint textMap_pk
            primary key autoincrement,
    hash    text,
    content TEXT,
    lang    integer,
    constraint textMap_pk_2
        unique (lang, hash)
);

create index textMap_hash_index
    on textMap (hash);

create index textMap_lang_index
    on textMap (lang);

create table voice
(
    id          integer
        constraint voice_pk
            primary key autoincrement,
    dialogueId  integer,
    voicePath   TEXT,
    gameTrigger TEXT,
    avatarId    integer
);

create index voice_dialogueId_index
    on voice (dialogueId);

create table npc
(
    id       integer
        constraint npc_pk
            primary key autoincrement,
    npcId    integer
        constraint npc_pk_2
            unique,
    textHash text
);

create index npc_npcId_index
    on npc (npcId);

create table manualTextMap
(
    id        integer
        constraint manualTextMap_pk
            primary key,
    textMapId text,
    textHash  text
);

create unique index manualTextMap_textMapId_uindex
    on manualTextMap (textMapId);
