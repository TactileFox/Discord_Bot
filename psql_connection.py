import os
import asyncpg as psy
import matplotlib.pyplot as plt
from asyncpg import Connection
from io import BytesIO
from typing import Final
from discord import Message, Guild, User, Attachment, File, Reaction
from datetime import datetime, timezone

async def create_message_log(message: Message) -> None:

    conn = await get_db_connection()

    await log_user(conn, message.author)
    await log_guild(conn, message.guild)
    await log_channel(conn, message)
    await log_message(conn, message)

    for attachment in message.attachments:
        await log_attachment(conn, attachment, message_id=message.id)

    for user in message.mentions: 
        await log_user(conn, user)
        await log_user_mention(conn, user, message_id=message.id, message_sender_id=message.author.id)

    await conn.close()

# Check, Update, Insert
async def log_user(conn: Connection, user: User) -> None:

    row = await conn.fetchrow(get_user_query(), user.id)

    if not row:
        try:
            await conn.execute(insert_user_query(), user.id, user.name, get_date())
        except Exception as e:
            print(f'Error creating user {user.name} with exception {e}')
    elif row['Username'] != user.name:
        try:
            await conn.execute(update_user_query(), user.name, datetime.now(timezone.utc), user.id)
        except Exception as e:
            print(f'Error updating user {user.name} with exception {e}')

async def log_guild(conn: Connection, guild: Guild) -> None:

    row = await conn.fetchrow(get_guild_query(), guild.id)

    if not row:
        try:
            await conn.execute(insert_quild_query(), guild.id, guild.name, guild.description, get_date())
        except Exception as e:
            print(f'Error inserting guild {guild.name} with exception {e}')
    elif row['Name'] != guild.name or row['Description'] != guild.description:
        try:
            await conn.execute(update_guild_query(), guild.name, guild.description, get_date(), guild.id)
        except Exception as e:
            print(f'Error updating guild {guild.name} with exception {e}')

async def log_channel(conn: Connection, message: Message) -> None:

    channel = message.channel

    row = await conn.fetchrow(get_channel_query(), channel.id)

    # Update channel.name property
    channel_name = create_channel_name(message)

    if not row:
        try:
            await conn.execute(insert_channel_query(), channel.id, channel.type.value, channel_name, channel.guild.id, channel.category.name, get_date())
        except Exception as e:
            print(f'Error inserting channel {channel_name} with exception {e}')
    elif row['Name'] != channel.name or row['ChannelTypeId'] != channel.type.value:
        try:
            await conn.execute(update_channel_query(), channel.name, channel.type.value, channel.id)
        except Exception as e:
            print(f'Error updating channel {channel.name} with exception {e}')

async def log_message(conn: Connection, message: Message) -> None:

    row = await conn.fetchrow(get_message_query(), message.id)

    if not row:
        try:
            await conn.execute(insert_message_query(), message.id, message.author.id, message.guild.id, message.content, message.channel.id, get_date())
        except Exception as e:
            print(f'Error inserting message {message.content[:20]}... with exception {e}')

async def log_attachment(conn: Connection, attachment: Attachment, message_id):

    row = await conn.fetchrow(get_attachment_query(), attachment.id)
    
    if not row:
        try:
            await conn.execute(insert_attachment_query(), attachment.id, attachment.filename, attachment.content_type, attachment.url, message_id, get_date())
            print(f'Attachment {attachment.filename[:20]} added successfully')
        except Exception as e:
            print(f'Error inserting attachment {attachment.filename[:20]} with exception {e}')
    elif row['Filename'] != attachment.filename or row['ContentType'] != attachment.content_type or row['URL'] != attachment.url or row['MessageId'] != message_id:
        return NotImplementedError('Attachment already exists')
    

async def log_user_mention(conn: Connection, user: User, message_id, message_sender_id) -> None:

    # TODO Don't log bot mentions
    # if message_sender_id == bot.id: return

    row = await conn.fetchrow(get_user_mentions_query(), message_id, message_sender_id)

    if not row: 
        try:
            await conn.execute(insert_user_mentions_query(), message_id, message_sender_id, user.id, get_date())
        except Exception as e:
            print(f'Error inserting mention {user.name} with exception {e}')

async def get_message_counts(guild: Guild) -> File:
    
    conn = await get_db_connection()
    data = await conn.fetch('SELECT COUNT("M"."Id"), "U"."Username" FROM "Message" "M" INNER JOIN "User" "U" ON "U"."Id" = "M"."UserId" WHERE "M"."GuildId" = $1 GROUP BY "U"."Username" ORDER BY COUNT("M"."Id") DESC LIMIT 10', guild.id)

    # Create matplotlib graph
    fig, ax = plt.subplots()
    ax.bar([point['Username'] for point in data], [point['count'] for point in data], color='blue')
    ax.set_xlabel('User')
    ax.set_ylabel('Message Count')
    ax.set_title('Message Count by User')

    # Save plot to IO object
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # Create and return file 
    file = File(buf, 'message_count_graph.png')
    plt.close()
    buf.close()
    await conn.close()

    return file

async def log_message_edit(before: Message, after: Message) -> None:
    
    conn = await get_db_connection()

    row = await conn.fetchrow('SELECT "Id" FROM "Message" WHERE "Id" = $1', before.id) # Check if before message exists

    if not row: 
        await create_message_log(before)
    try: 
        # Log attachments in before that aren't in after as deleted
        for attachment in before.attachments:
            if attachment not in after.attachments:
                # Delete record
                await conn.execute(delete_attachment_query(), get_date(), get_date(), attachment.url, before.id) 
        # Log new attachments
        for attachment in after.attachments:
            if attachment not in before.attachments:
                # Insert record
                await log_attachment(conn, attachment, before.id)
        for mention in before.mentions:
            if mention not in after.mentions:
                # Delete record
                await conn.execute(delete_user_mention_query(), get_date(), get_date(), before.id, mention.id)
        for mention in after.mentions:
            if mention not in before.mentions:
                # Insert record
                await log_user_mention(conn, mention, before.id, before.author.id)
        await conn.execute(update_message_query(), after.content, 1, 0, get_date(), None, after.id)
    except Exception as e:
        print(f'Error updating message with exception {e}')
    try:
        await conn.execute(insert_message_edit_query(), before.id, before.content, after.content, get_date())
    except Exception as e:
        print(f'Error inserting message edit with exception {e}')

    await conn.close()
async def log_message_deletion(message: Message) -> None:

    conn = await get_db_connection()

    row = await conn.fetchrow('SELECT "Id" FROM "Message" WHERE "Id" = $1', message.id)

    if not row:
        await create_message_log(message)
    try: 
        await conn.execute("""UPDATE "Message" SET "DeleteDateUTC" = $1, "Deleted" = $2, "UpdateDateUTC" = $3 WHERE "Id" = $4""", get_date(), 1, get_date(), message.id)
    except Exception as e:
        print(f'Error updating message {message.id} with exception {e}')
    
    await conn.close()
async def log_message_reaction(reaction: Reaction, user: User) -> None:

    conn = await get_db_connection()

    await log_user(get_db_connection(), user)

    self_react = int(reaction.message.author.id == user.id) 

    try:
        emoji_name = reaction.emoji.name if type(reaction.emoji) != str else reaction.emoji
        # TODO put insert reaction query into a new function.
        await conn.execute(insert_reaction_query(), reaction.message.id, user.id, emoji_name, self_react, get_date())
    except Exception as e:
        print(f'Error inserting reaction {emoji_name} with exception {e}')

    await conn.close()
async def log_reaction_deletion(reaction: Reaction, user: User) -> None:

    conn = await get_db_connection()

    try:
        emoji_name = reaction.emoji.name if type(reaction.emoji) != str else reaction.emoji
        await conn.execute(delete_reaction_query(), get_date(), reaction.message.id, user.id, emoji_name)
    except Exception as e:
        print(f'Error updating reaction {emoji_name} with exception {e}')

    await conn.close()
async def log_reaction_clear(reactions: list[Reaction], message: Message) -> None:

    conn = await get_db_connection()
    row = conn.fetchrow('SELECT "Id" FROM "Reactions" WHERE "MessageId" = $1 AND "Deleted" = 0 LIMIT 1', (message.id,))

    if not row:
        return
    else:
        for reaction in reactions:
            try:
                await conn.execute('UPDATE "Reactions" SET "DeleteDateUTC" = $1, "Deleted" = 1 WHERE "MessageId" = $2 AND "Deleted" = 0', get_date(), message.id)
            except Exception as e:
                emoji_name = reaction.emoji.name if type(reaction.emoji) != str else reaction.emoji 
                print(f'Error deleting reaction {emoji_name} with exception {e}')

    await conn.close()

async def get_last_updated_message(channel_id) -> tuple:

    conn = await get_db_connection()

    row = await conn.fetchrow('SELECT "M"."Id" AS "MessageId", "M"."Content", "U"."Username", "M"."Deleted" FROM "Message" "M" INNER JOIN "User" "U" ON "U"."Id" = "M"."UserId" WHERE "M"."ChannelId" = $1 AND "M"."UpdateDateUTC" IS NOT NULL ORDER BY "M"."UpdateDateUTC" DESC LIMIT 1', channel_id)

    if not row:
        return (None,)
    if row['Deleted'] == 0:
        username = row['Username']
        row = await conn.fetchrow('SELECT "BeforeContent", "AfterContent" FROM "MessageEditHistory" WHERE "MessageId" = $1 ORDER BY "CreateDateUTC" DESC LIMIT 1', row['MessageId'])
        await conn.close()
        return (row['MessageId'], row['Content'], username, 'edited')
    else:
        await conn.close()
        return (None, row['Content'], row['Username'], 'deleted')

# Helpers
def create_channel_name(message: Message):
    if message.channel.type in ('private', 'group'):
        return f'DM with {message.author}'
    else:
        return message.channel.name
def get_date():
    return datetime.now(timezone.utc).replace(tzinfo=None)
async def get_db_connection() -> Connection:

    DB_NAME: Final[str] = os.getenv('DB_NAME')
    DB_USER: Final[str] = os.getenv('DB_USER')
    DB_PASS: Final[str] = os.getenv('DB_PASS')
    DB_HOST: Final[str] = os.getenv('DB_HOST')
    DB_PORT: Final[str] = os.getenv('DB_PORT')
    return await psy.connect(database=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)

# Queries
def get_user_query():
    return 'SELECT "Id", "Username" FROM "User" WHERE "Id" = $1 LIMIT 1'
def insert_user_query():
    return """INSERT INTO "User" ("Id", "Username", "CreateDateUTC") VALUES ($1, $2, $3)"""
def update_user_query():
    return """UPDATE "User" SET "Username" = $1, "UpdateDateUTC" = $2 WHERE "Id" = $3"""
def get_guild_query():
    return 'SELECT "Id", "Name", "Description" FROM "Guild" WHERE "Id" = $1 LIMIT 1'
def insert_quild_query():
    return """INSERT INTO "Guild" ("Id", "Name", "Description", "CreateDateUTC") VALUES ($1, $2, $3, $4)"""
def update_guild_query():
    return """UPDATE "Guild" SET "Name" = $1, "Description" = $2, "UpdateDateUTC" = $3 WHERE "Id" = $4"""
def get_channel_query():
    return 'SELECT "Id", "Name", "ChannelTypeId" FROM "Channel" WHERE "Id" = $1 LIMIT 1'
def insert_channel_query():
    return """INSERT INTO "Channel" ("Id", "ChannelTypeId", "Name", "GuildId", "CategoryName", "CreateDateUTC") VALUES ($1, $2, $3, $4, $5, $6)"""
def update_channel_query():
    return """UPDATE "Channel" SET "Name"=$1, "ChannelTypeId"=$2 WHERE "Id"=$3"""
def get_message_query():
    return 'SELECT "Id" FROM "Message" WHERE "Id" = $1'
def insert_message_query():
    return """INSERT INTO "Message" ("Id", "UserId", "GuildId", "Content", "ChannelId", "CreateDateUTC") VALUES ($1, $2, $3, $4, $5, $6)"""
def update_message_query():
    return 'UPDATE "Message" SET "Content" = $1, "Edited" = $2, "Deleted" = $3, "UpdateDateUTC" = $4, "DeleteDateUTC" = $5 WHERE "Id" = $6'
def get_attachment_query():
    return 'SELECT "Id", "Filename", "ContentType" FROM "Attachments" WHERE "Id" = $1'
def insert_attachment_query():
    return """INSERT INTO "Attachments" ("Id", "Filename", "ContentType", "URL", "MessageId", "CreateDateUTC") VALUES ($1, $2, $3, $4, $5, $6)"""
def delete_attachment_query():
    return """UPDATE "Attachments" SET "Deleted" = 1, "DeleteDateUTC" = $1, "UpdateDateUTC" = $2 WHERE "URL" = $3 and "MessageId" = $4"""
def update_attachment_query():
    return NotImplementedError('Update Attachment Query not written yet')
def get_user_mentions_query():
    return 'SELECT "MessageId" FROM "UserMentions" WHERE "MessageId" = $1 AND "RecipientId" = $2'
def insert_user_mentions_query():
    return """INSERT INTO "UserMentions" ("MessageId", "AuthorId", "RecipientId", "CreateDateUTC") VALUES ($1, $2, $3, $4)"""
def delete_user_mention_query():
    return """UPDATE "UserMentions" SET "Deleted" = 1, "DeleteDateUTC" = $1, "UpdateDateUTC" = $2 WHERE "MessageId" = $3 AND "RecipientId" = $4"""
def insert_message_edit_query():
    return 'INSERT INTO "MessageEditHistory" ("MessageId", "BeforeContent", "AfterContent", "CreateDateUTC") VALUES ($1, $2, $3, $4)'
def insert_reaction_query():
    return """INSERT INTO "Reactions" ("MessageId", "UserId", "Emoji", "SelfReact", "CreateDateUTC") VALUES ($1, $2, $3, $4, $5)"""
def delete_reaction_query():
    return 'UPDATE "Reactions" SET "DeleteDateUTC" = $1, "Deleted" = 1 WHERE "MessageId" = $2 AND "UserId" = $3 AND "Emoji" = $4 AND "Deleted" = 0'