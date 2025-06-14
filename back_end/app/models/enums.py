from enum import IntEnum


class ChannelType(IntEnum):
    TEXT: 0
    PRIVATE: 1
    VOICE: 2
    GROUP: 3
    CATEGORY: 4
    NEWS: 5
    NEWS_THREAD: 10
    PUBLIC_THREAD: 11
    PRIVATE_THREAD: 12
    STAGE_VOICE: 13
    FORUM: 15
    MEDIA: 16

    @classmethod
    def label_from_value(cls, value: int) -> str:
        labels = {
            cls.TEXT: 'TEXT',
            cls.PRIVATE: 'PRIVATE',
            cls.VOICE: 'VOICE',
            cls.GROUP: 'GROUP',
            cls.CATEGORY: 'CATEGORY',
            cls.NEWS: 'NEWS',
            cls.NEWS_THREAD: 'NEWS_THREAD',
            cls.PUBLIC_THREAD: 'PUBLIC_THREAD',
            cls.PRIVATE_THREAD: 'PRIVATE_THREAD',
            cls.STAGE_VOICE: 'STAGE_VOICE',
            cls.FORUM: 'FORUM',
            cls.MEDIA: 'MEDIA'
        }
        return labels.get(value, 'UNKNOWN')

    @classmethod
    def value_from_label(cls, label: str) -> int:
        values = {
            'TEXT': cls.TEXT,
            'PRIVATE': cls.PRIVATE,
            'VOICE': cls.VOICE,
            'GROUP': cls.GROUP,
            'CATEGORY': cls.CATEGORY,
            'NEWS': cls.NEWS,
            'NEWS_THREAD': cls.NEWS_THREAD,
            'PUBLIC_THREAD': cls.PUBLIC_THREAD,
            'PRIVATE_THREAD': cls.PRIVATE_THREAD,
            'STAGE_VOICE': cls.STAGE_VOICE,
            'FORUM': cls.FORUM,
            'MEDIA': cls.MEDIA
        }
        return values.get(label, None)
