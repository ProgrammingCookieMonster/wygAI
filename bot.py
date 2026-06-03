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

@client.event
async def on_ready():
    print(f"Bot online as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if not client.user.mentioned_in(message):
        return

    question = message.content.replace(
        f'<@{client.user.id}>', ''
    ).strip()

    if not question:
        await message.reply(
            "Ställ en fråga om kårens rutiner och processer."
        )
        return

    async with message.channel.typing():
        answer = await asyncio.get_event_loop().run_in_executor(
            None, answer_question, question
        )

    await message.reply(answer)

client.run(TOKEN)