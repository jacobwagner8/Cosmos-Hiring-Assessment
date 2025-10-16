import discord
import json
import asyncio
import os

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Configure intents (must also be enabled in the Developer Portal)
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    all_data = {}

    # Loop through all guilds (servers) the bot is in
    for guild in client.guilds:
        print(f"\nFetching data from guild: {guild.name}")
        guild_data = {"channels": {}}

        # Loop through all text channels in the guild
        for channel in guild.text_channels:
            print(f"  Retrieving messages from channel: {channel.name}")
            messages = []
            try:
                async for msg in channel.history(limit=None):  # Retrieve full history
                    messages.append({
                        "id": msg.id,
                        "author": msg.author.name,
                        "content": msg.content,
                        "timestamp": msg.created_at.isoformat()
                    })
            except Exception as e:
                print(f"    Skipped {channel.name}: {e}")
                continue

            guild_data["channels"][channel.name] = messages

        all_data[guild.name] = guild_data

    # Save all messages to JSON
    with open("discord_data.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print("\n✅ Data collection complete. Saved to discord_data.json")
    await client.close()

# Run the bot
asyncio.run(client.start(TOKEN))
