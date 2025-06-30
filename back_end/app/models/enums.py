from enum import IntEnum


class ChannelType(IntEnum):
    TEXT = 0
    PRIVATE = 1
    VOICE = 2
    GROUP = 3
    CATEGORY = 4
    NEWS = 5
    NEWS_THREAD = 10
    PUBLIC_THREAD = 11
    PRIVATE_THREAD = 12
    STAGE_VOICE = 13
    GUILD_DIRECTORY = 14
    FORUM = 15
    MEDIA = 16
