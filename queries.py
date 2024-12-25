def get_attachment() -> str:
    return 'SELECT * FROM "Attachments" WHERE "Id" = $1'


def insert_attachment() -> str:
    return (
        'INSERT INTO "Attachments" ('
        '"Id", "Filename", "ContentType", "URL", "MessageId", "CreateDateUTC")'
        ' VALUES ($1, $2, $3, $4, $5, $6)'
    )


def update_attachment(deletion: bool = False) -> str:
    if deletion:
        return (
            'UPDATE "Attachments" SET "URL" = $1, "UpdateDateUTC" = $2, '
            '"DeleteDateUTC" = $2, "Deleted" = 1 WHERE "Id" = $3'
        )
    else:
        return (
            'UPDATE "Attachments" SET "URL" = $1, "UpdateDateUTC" = $2 '
            'WHERE "Id" = $3'
        )


def get_channel() -> str:
    return 'SELECT * FROM "Channel" WHERE "Id" = $1'


def insert_channel() -> str:
    return (
        'INSERT INTO "Channel" ("Id", "ChannelTypeId", "Name", "GuildId", '
        '"CategoryName", "CreateDateUTC", "NSFW") '
        'VALUES ($1, $2, $3, $4, $5, $6, $7)'
    )


def update_channel() -> str:
    return (
        'UPDATE "Channel" SET "Name" = $1, "CategoryName" = $2, '
        '"UpdateDateUTC" = $3, "NSFW" = $4 WHERE "Id" = $5'
    )


def get_guild() -> str:
    return 'SELECT * FROM "Guild" WHERE "Id" = $1'


def insert_guild() -> str:
    return (
        'INSERT INTO "Guild" ("Id", "Name", "Description", "CreateDateUTC") '
        'VALUES ($1, $2, $3, $4)'
    )


def update_guild() -> str:
    return (
        'UPDATE "Guild" SET "Name" = $1, "Description" = $2, '
        '"UpdateDateUTC" = $3 WHERE "Id" = $4'
    )


def get_message() -> str:
    return 'SELECT * FROM "Message" WHERE "Id" = $1'


def insert_message() -> str:
    return (
        'INSERT INTO "Message" ("Id", "UserId", "GuildId", "Content", '
        '"ChannelId", "CreateDateUTC") VALUES ($1, $2, $3, $4, $5, $6)'
    )


def update_message(deletion: bool = False) -> str:
    if deletion:
        return (
            'UPDATE "Message" SET "UpdateDateUTC" = $1, "DeleteDateUTC" = $1, '
            '"Deleted" = 1 WHERE "Id" = $2'
        )
    else:
        return (
            'UPDATE "Message" SET "Content" = $1, "UpdateDateUTC" = $2, '
            '"Edited" = 1 WHERE "Id" = $3'
        )


def insert_message_edit() -> str:
    return (
        'INSERT INTO "MessageEditHistory" ("MessageId", "BeforeContent", '
        '"AfterContent", "CreateDateUTC") VALUES ($1, $2, $3, $4)'
    )


def insert_reaction() -> str:
    return (
        'INSERT INTO "Reactions" ("Id", "MessageId", "UserId", "Emoji", '
        '"SelfReact", "CreateDateUTC") VALUES ($1, $2, $3, $4, $5, $6)'
    )


def update_reaction(emoji: bool = False, all: bool = False) -> str:
    query: str = (
        'UPDATE "Reactions" SET "DeleteDateUTC" = $1, "Deleted" = 1 '
        'WHERE '
    )
    if all:
        query += '"MessageId" = $2'
    elif emoji:
        query += '"MessageId" = $2 AND "Emoji" = $3'
    else:
        query += '"MessageId" = $2 AND "Emoji" = $3 AND "UserId" = $4'
    return query


def insert_user_mentions() -> str:
    return (
        'INSERT INTO "UserMentions" ("Id", "MessageId", "AuthorId", '
        '"RecipientId", "CreateDateUTC") VALUES ($1, $2, $3, $4, $5)'
    )


def update_user_mentions() -> str:
    return (
        'UPDATE "UserMentions" SET "UpdateDateUTC" = $1, '
        '"DeleteDateUTC" = $1, "Deleted" = 1 WHERE "MessageId" = $2 AND '
        '"RecipientId" = $3'
    )


def get_user() -> str:
    return 'SELECT * FROM "User" WHERE "Id" = $1'


def insert_user() -> str:
    return (
        'INSERT INTO "User" ("Id", "Username", "CreateDateUTC") '
        'VALUES ($1, $2, $3)'
    )


def update_user() -> str:
    return (
        'UPDATE "User" SET "Username" = $1, "UpdateDateUTC" = $2'
        'WHERE "Id" = $3'
    )


def snipe_query() -> str:
    return """
    SELECT
        CASE
            WHEN m."Deleted" = 0 THEN meh."BeforeContent"
            ELSE NULL
        END AS "BeforeText",
        COALESCE(meh."AfterContent", m."Content") AS "CurrentText",
        u."Username",
        CASE
            WHEN m."Deleted" = 1 THEN 'Deleted'
            WHEN m."Edited" = 1 THEN 'Edited'
        END AS "Action",
        a."URL"

    FROM "Message" m
    INNER JOIN "User" u
        ON U."Id" = m."UserId"
    LEFT JOIN LATERAL (
        SELECT meh."BeforeContent",
            meh."AfterContent"
        FROM "MessageEditHistory" meh
        WHERE meh."MessageId" = m."Id"
        ORDER BY meh."CreateDateUTC" DESC
        LIMIT 1
    ) meh ON 1=1
    LEFT JOIN LATERAL (
        SELECT a."URL"
        FROM "Attachments" a
        WHERE a."Deleted" = 1
            AND a."MessageId" = m."Id"
            AND a."DeleteDateUTC" > m."UpdateDateUTC"
        ORDER BY a."DeleteDateUTC" DESC
        LIMIT 1
    ) a ON 1=1
    WHERE m."UpdateDateUTC" IS NOT NULL
        AND m."ChannelId" = $1
    ORDER BY m."UpdateDateUTC" DESC
    LIMIT 1;
"""
