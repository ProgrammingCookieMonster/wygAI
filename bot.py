import discord
import asyncio
import os
from dotenv import load_dotenv
from rag import answer_question

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

# single queue — one request processed at a time
request_queue = asyncio.Queue()

# mapping user_id --> thread_id
user_threads = {}

async def queue_worker():
    """Processes one question at a time from the queue."""
    while True:
        user_message, question, status_msg = await request_queue.get()

        try:
            await status_msg.edit(content="⚙️ Working on your answer...")

            # run blocking RAG call in a thread -- flush system if mode gets blocked
            answer = await asyncio.to_thread(answer_question, question)

            await status_msg.edit(content=f"✅ {answer}")

        except Exception as e:
            print(f"Error: {e}")
            await status_msg.edit(
                content="❌ Something went wrong. Contact the Union Board for important questions or the bot owner for technical issues.")
        finally:
            request_queue.task_done()


@client.event
async def on_ready():
    print(f"Smurfette online as {client.user}")
    asyncio.create_task(queue_worker())
    # sync tree
    try:
        await tree.sync()
        print("Slash commands synced.")
    except Exception as e:
        print(f"Failed to sync slash commands: ", e)

async def get_or_create_user_thread(message: discord.Message) -> discord.Thread:
    """Return an existing private thread for this user, or create a new one"""
    user_id = message.author.id
    channel = message.channel

    # 1 try to fetch already existing thread
    if user_id in user_threads:
        thread_id = user_threads[user_id]
        thread = client.get_channel(thread_id)
        if thread is None:
            try:
                thread = await client.fetch_channel(thread_id)
            except Exception:
                thread = None

        # if thread was archived --> reopen and reuse
        if isinstance(thread, discord.Thread):
            if thread.archived:
                try:
                    await thread.edit(archived=False)
                except discord.HTTPException:
                    pass # if it fails, just create another one
            return thread

    # 2 create new thread
    try:
        thread = await channel.create_thread(
            name=f"Questions from {message.author.display_name}",
            type=discord.ChannelType.private_thread,
            auto_archive_duration=60 # archive it after 1h of inactivity
        )
    except discord.HTTPException:
        # fallback -- use the channel it was mention on (should not happen?)
        thread = channel

    # remember user_thread
    if isinstance(thread, discord.Thread):
        user_threads[user_id] = thread.id

    return thread

@client.event
async def on_message(message: discord.Message):
    # ignore own bot message
    if message.author == client.user:
        return

    # 1 -- message is inside existing thread --> all messages here are queries without the need to mention the bot
    if isinstance(message.channel, discord.Thread) and message.channel.owner_id == client.user.id:
        question = message.content.strip()
        if not question:
            return

        status_msg = await message.channel.send("⏳ Received! Adding your question to the queue...")
        await request_queue.put((message, question, status_msg))
        return

    # 2 -- message in the bot public channel --> user needs to mention the bot to call on it
    # bot tries to fetch old thread or creates a new one
    if not client.user.mentioned_in(message):
        return

    # extract the question from the mentioned query
    question = message.content.replace(f'<@{client.user.id}>', '').strip()
    if not question:
        await message.reply(
            "👋 Hey! I can help with questions about SHV and (soon to come) general student life at Högskolan Väst. "
            "State a question when mentioning me."
        )
        return

    # get or create private thread for this user
    thread = await get_or_create_user_thread(message)

    # queue info
    queue_size = request_queue.qsize()
    if queue_size == 0:
        status_text = "⏳ It is your turn in the queue, answering..."
    else:
        status_text = (
            f"📋 You are **number {queue_size + 1}** in the queue.\n"
            f"This bot runs on very limited hardware, so answers can take a while."
        )
    status_msg = await thread.send(status_text)

    # add to queue
    await request_queue.put((message, question, status_msg))

# === slash command: /help ===
@tree.command(name="help", description="Shows how to use the Smurfette bot.")
async def help_command(interaction: discord.Interaction):
    await interaction.response.send_message(
        "👋 **How to use Smurfette:**\n"
        "- Mention me in this public channel to start a private thread.\n"
        "- Ask your question inside the thread.\n"
        "- I will answer one question at a time.\n"
        "- If your thread is archived, mention me again and I will reopen it.\n"
        "- I can help with questions regarding SHV and student life at Högskolan Väst.",
        ephemeral=True
    )

client.run(TOKEN)