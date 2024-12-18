import os
import psycopg2 as psy
import matplotlib.pyplot as plt
from io import BytesIO
from psycopg2.extensions import connection
from typing import Final
from dotenv import load_dotenv
from discord import Message, Guild, User, Attachment, File, Reaction
from datetime import datetime, timezone

async def create_message_log(message: Message) -> None:

    conn = get_db_connection()

    log_user(conn, message.author)
    log_guild(conn, message.guild)
    log_channel(conn, message)
    log_message(conn, message)

    for attachment in message.attachments:
        log_attachment(conn, attachment, message_id=message.id)

    for user in message.mentions: 
        log_user(conn, user)
        log_user_mention(conn, user, message_id=message.id, message_sender_id=message.author.id)

    conn.close()

# Check, Update, Insert
def log_user(conn: connection, user: User) -> None:

    cur = conn.cursor()
    cur.execute(get_user_query(), (user.id,))
    row = cur.fetchone()

    if not row:
        try:
            cur.execute(insert_user_query(), (user.id, user.name, get_date()))
            conn.commit()
        except Exception as e:
            print(f'Error creating user {user.name} with exception {e}')
    elif row[1] != user.name:
        try:
            cur.execute(update_user_query(), (user.name, datetime.now(timezone.utc), user.id))
            conn.commit()
        except Exception as e:
            print(f'Error updating user {user.name} with exception {e}')

    cur.close()   
def log_guild(conn: connection, guild: Guild) -> None:

    cur = conn.cursor()
    cur.execute(get_guild_query(), (guild.id,))
    row = cur.fetchone()

    if not row:
        try:
            cur.execute(insert_quild_query(), (guild.id, guild.name, guild.description, get_date()))
            conn.commit()
        except Exception as e:
            print(f'Error inserting guild {guild.name} with exception {e}')
    elif row[0] == guild.id and (row[1] != guild.name or row[2] != guild.description):
        try:
            cur.execute(update_guild_query(), (guild.name, guild.description, get_date(), guild.id))
            conn.commit()
        except Exception as e:
            print(f'Error updating guild {guild.name} with exception {e}')

    cur.close()
def log_channel(conn: connection, message: Message) -> None:

    channel = message.channel
    cur = conn.cursor()
    cur.execute(get_channel_query(), (channel.id,))
    row = cur.fetchone()
    
    # Update channel.name if it doesn't have one
    channel_name = create_channel_name(message)

    if not row:
        try:
            cur.execute(insert_channel_query(), (channel.id, channel.type.value, channel_name, channel.guild.id, channel.category.name, get_date()))
            conn.commit()
        except Exception as e:
            print(f'Error inserting channel {channel_name} with exception {e}')
    elif row[1] != channel.name or row[2] != channel.type.value:
        try:
            cur.execute(update_channel_query(), (channel.name, channel.type.value, channel.id))
            conn.commit()
        except Exception as e:
            print(f'Error updating channel {channel.name} with exception {e}')

    cur.close()
def log_message(conn: connection, message: Message) -> None:

    cur = conn.cursor()
    cur.execute(get_message_query(), (message.id,))
    row = cur.fetchone()

    if not row:
        try:
            cur.execute(insert_message_query(), (message.id, message.author.id, message.guild.id, message.content, message.channel.id, get_date()))
            conn.commit()
        except Exception as e:
            print(f'Error inserting message {message.content[:20]}... with exception {e}')

    cur.close()
def log_attachment(conn: connection, attachment: Attachment, message_id):

    cur = conn.cursor()
    cur.execute(get_attachment_query(), (attachment.id,))
    row = cur.fetchone()
    
    if not row:
        try:
            cur.execute(insert_attachment_query(), (attachment.id, attachment.filename, attachment.content_type, attachment.url, message_id, get_date()))
            conn.commit()
            print(f'Attachment {attachment.filename[:20]} added successfully')
        except Exception as e:
            print(f'Error inserting attachment {attachment.filename[:20]} with exception {e}')
    elif row[1] != attachment.filename or row[2] != attachment.content_type or row[3] != attachment.url or row[4] != message_id:
        return NotImplementedError('Attachment already exists')
    
    cur.close()
def log_user_mention(conn: connection, user: User, message_id, message_sender_id) -> None:

    # TODO Don't log bot mentions
    # if message_sender_id == bot.id: return

    cur = conn.cursor()
    cur.execute(get_user_mentions_query(), (message_id, message_sender_id))
    row = cur.fetchone()
    if not row: 
        try:
            cur.execute(insert_user_mentions_query(), (message_id, message_sender_id, user.id, get_date()))
            conn.commit()
        except Exception as e:
            print(f'Error inserting mention {user.name} with exception {e}')

    cur.close()
def get_message_counts(guild: Guild) -> File:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT COUNT("M"."Id"), "U"."Username" FROM "Message" "M" INNER JOIN "User" "U" ON "U"."Id" = "M"."UserId" WHERE "M"."GuildId" = %s GROUP BY "U"."Username" ORDER BY COUNT("M"."Id") DESC LIMIT 10', (guild.id,))
    data = cur.fetchall()

    # Create matplotlib graph
    fig, ax = plt.subplots()
    ax.bar([user for count, user in data], [count for count, user in data], color='blue')
    ax.set_xlabel('User')
    ax.set_ylabel('Message Count')
    ax.set_title('Message Count by User')

    # Save plot to IO object
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # Create and return file 
    file = File(buf, 'message_count_graph.png') # File stored in buf, title
    plt.close()
    buf.close()
    cur.close()
    conn.close()

    return file

async def log_message_edit(before: Message, after: Message) -> None:
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT "Id" FROM "Message" WHERE "Id" = %s', (before.id,)) # Check if before message exists
    row = cur.fetchone()

    if not row: 
        await create_message_log(before)
    try: 
        # Log attachments in before that aren't in after as deleted
        for attachment in before.attachments:
            if attachment not in after.attachments:
                # Delete record
                cur.execute(delete_attachment_query(), (get_date(), get_date(), attachment.url, before.id)) 
                conn.commit()
        # Log new attachments
        for attachment in after.attachments:
            if attachment not in before.attachments:
                # Insert record
                log_attachment(conn, attachment, before.id)
        for mention in before.mentions:
            if mention not in after.mentions:
                # Delete record
                cur.execute(delete_user_mention_query(), (get_date(), get_date(), before.id, mention.id))
                conn.commit()
        for mention in after.mentions:
            if mention not in before.mentions:
                # Insert record
                log_user_mention(conn, mention, before.id, before.author.id)
        cur.execute(update_message_query(), (after.content, 1, 0, get_date(), None, after.id))
        conn.commit()
    except Exception as e:
        print(f'Error updating message with exception {e}')
    try:
        cur.execute('INSERT INTO "MessageEditHistory" ("MessageId", "BeforeContent", "AfterContent", "CreateDateUTC") VALUES (%s, %s, %s, %s)', (before.id, before.content, after.content, get_date()))
        conn.commit()
    except Exception as e:
        print(f'Error inserting message edit with exception {e}')
        
    conn.commit()
    cur.close()
    conn.close()
async def log_message_deletion(message: Message) -> None:

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT "Id" FROM "Message" WHERE "Id" = %s', (message.id,))
    row = cur.fetchone()

    if not row:
        create_message_log(message)
    try: 
        cur.execute("""UPDATE "Message" SET "DeleteDateUTC" = %s, "Deleted" = %s, "UpdateDateUTC" = %s WHERE "Id" = %s""", (get_date(), 1, get_date(), message.id))
        conn.commit()
    except Exception as e:
        print(f'Error updating message {message.id} with exception {e}')
    
    cur.close()
    conn.close()
def log_message_reaction(reaction: Reaction, user: User) -> None:

    conn = get_db_connection()
    cur = conn.cursor()
    log_user(get_db_connection(), user)

    self_react = int(reaction.message.author.id == user.id) 

    try:
        emoji_name = reaction.emoji.name if type(reaction.emoji) != str else reaction.emoji
        # TODO put insert reaction query into a new function.
        cur.execute("""INSERT INTO "Reactions" ("MessageId", "UserId", "Emoji", "SelfReact", "CreateDateUTC") VALUES (%s, %s, %s, %s, %s)""", (reaction.message.id, user.id, emoji_name, self_react, get_date()))
        conn.commit()
    except Exception as e:
        print(f'Error inserting reaction {emoji_name} with exception {e}')
    cur.close()
    conn.close()
def log_reaction_deletion(reaction: Reaction, user: User) -> None:

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        emoji_name = reaction.emoji.name if type(reaction.emoji) != str else reaction.emoji
        #TODO: modularize query
        cur.execute('UPDATE "Reactions" SET "DeleteDateUTC" = %s, "Deleted" = 1 WHERE "MessageId" = %s AND "UserId" = %s AND "Emoji" = %s AND "Deleted" = 0', (get_date(), reaction.message.id, user.id, emoji_name))
        conn.commit()
    except Exception as e:
        print(f'Error updating reaction {emoji_name} with exception {e}')

    cur.close()
    conn.close()
def log_reaction_clear(reactions: list[Reaction], message: Message) -> None:

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT "Id" FROM "Reactions" WHERE "MessageId" = %s AND "Deleted" = 0 LIMIT 1', (message.id,))
    row = cur.fetchone()

    if not row:
        return
    else:
        for reaction in reactions:
            try:
                cur.execute('UPDATE "Reactions" SET "DeleteDateUTC" = %s, "Deleted" = 1 WHERE "MessageId" = %s AND "Deleted" = 0', (get_date(), message.id))
                conn.commit()
            except Exception as e:
                emoji_name = reaction.emoji.name if type(reaction.emoji) != str else reaction.emoji 
                print(f'Error deleting reaction {emoji_name} with exception {e}')

    cur.close()
    conn.close()

def get_last_updated_message(channel_id) -> tuple:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT "M"."Id", "M"."Content", "U"."Username", "M"."Deleted" FROM "Message" "M" INNER JOIN "User" "U" ON "U"."Id" = "M"."UserId" WHERE "M"."ChannelId" = %s AND "M"."UpdateDateUTC" IS NOT NULL ORDER BY "M"."UpdateDateUTC" DESC LIMIT 1', (channel_id,))
    row = cur.fetchone()

    #TODO clean up variable names
    if not row:
        return (None,)
    if row[3] == 0:
        username = row[2]
        cur.execute('SELECT "BeforeContent", "AfterContent" FROM "MessageEditHistory" WHERE "MessageId" = %s ORDER BY "CreateDateUTC" DESC LIMIT 1', (row[0],))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return (row[0], row[1], username, 'edited')
    else:
        cur.close()
        conn.close()
        return (None, row[1], row[2], 'deleted')

# Helpers
def create_channel_name(message: Message):
    if message.channel.type in ('private', 'group'):
        return f'DM with {message.author}'
    else:
        return message.channel.name
def get_date():
    return datetime.now(timezone.utc)
def get_db_connection():
    load_dotenv()
    DB_NAME: Final[str] = os.getenv('DB_NAME')
    DB_USER: Final[str] = os.getenv('DB_USER')
    DB_PASS: Final[str] = os.getenv('DB_PASS')
    DB_HOST: Final[str] = os.getenv('DB_HOST')
    DB_PORT: Final[str] = os.getenv('DB_PORT')
    return psy.connect(database=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)

# Queries
def get_user_query():
    return 'SELECT "Id", "Username" FROM "User" WHERE "Id" = %s LIMIT 1'
def insert_user_query():
    return """INSERT INTO "User" ("Id", "Username", "CreateDateUTC") VALUES (%s, %s, %s)"""
def update_user_query():
    return """UPDATE "User" SET "Username" = %s, "UpdateDateUTC" = %s WHERE "Id" = %s"""
def get_guild_query():
    return 'SELECT "Id", "Name", "Description" FROM "Guild" WHERE "Id" = %s LIMIT 1'
def insert_quild_query():
    return """INSERT INTO "Guild" ("Id", "Name", "Description", "CreateDateUTC") VALUES (%s, %s, %s, %s)"""
def update_guild_query():
    return """UPDATE "Guild" SET "Name" = %s, "Description" = %s, "UpdateDateUTC" = %s WHERE "Id" = %s"""
def get_channel_query():
    return 'SELECT "Id", "Name", "ChannelTypeId" FROM "Channel" WHERE "Id" = %s LIMIT 1'
def insert_channel_query():
    return """INSERT INTO "Channel" ("Id", "ChannelTypeId", "Name", "GuildId", "CategoryName", "CreateDateUTC") VALUES (%s, %s, %s, %s, %s, %s)"""
def update_channel_query():
    return """UPDATE "Channel" SET "Name"=%s, "ChannelTypeId"=%s WHERE "Id"=%s"""
def get_message_query():
    return 'SELECT "Id" FROM "Message" WHERE "Id" = %s'
def insert_message_query():
    return """INSERT INTO "Message" ("Id", "UserId", "GuildId", "Content", "ChannelId", "CreateDateUTC") VALUES (%s, %s, %s, %s, %s, %s)"""
def update_message_query():
    return 'UPDATE "Message" SET "Content" = %s, "Edited" = %s, "Deleted" = %s, "UpdateDateUTC" = %s, "DeleteDateUTC" = %s WHERE "Id" = %s'
def get_attachment_query():
    return 'SELECT "Id", "Filename", "ContentType" FROM "Attachments" WHERE "Id" = %s'
def insert_attachment_query():
    return """INSERT INTO "Attachments" ("Id", "Filename", "ContentType", "URL", "MessageId", "CreateDateUTC") VALUES (%s, %s, %s, %s, %s, %s)"""
def delete_attachment_query():
    return """UPDATE "Attachments" SET "Deleted" = 1, "DeleteDateUTC" = %s, "UpdateDateUTC" = %s WHERE "URL" = %s and "MessageId" = %s"""
def update_attachment_query():
    return NotImplementedError('Update Attachment Query not written yet')
def get_user_mentions_query():
    return 'SELECT "MessageId" FROM "UserMentions" WHERE "MessageId" = %s AND "RecipientId" = %s'
def insert_user_mentions_query():
    return """INSERT INTO "UserMentions" ("MessageId", "AuthorId", "RecipientId", "CreateDateUTC") VALUES (%s, %s, %s, %s)"""
def delete_user_mention_query():
    return """UPDATE "UserMentions" SET "Deleted" = 1, "DeleteDateUTC" = %s, "UpdateDateUTC" = %s WHERE "MessageId" = %s AND "RecipientId" = %s"""