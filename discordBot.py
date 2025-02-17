import discord
from discord.ext import commands, tasks
import asyncio
import time

TOKEN = "MTM0MDkzMzQ4NTU2NDUyNjU5Mg.G3sWwP.5S0C8zzf8DTIx0efgSTmvF-H1e619vwZ0hjBIQ"
GUILD_ID = 1338043993103142912  # Your server ID
AFK_CHANNEL_ID = 1338046891577049099  # AFK channel ID
AUDIO_FILE = "you digging in me Sound effect.mp3"
AFK_TIME_LIMIT = 5 * 60  # 15 minutes in seconds
AUDIO_PLAY_TIME = 5 * 60  # 5 minutes in seconds

intents = discord.Intents.default()
intents.voice_states = True
intents.members = True  # Required to track user activity

bot = commands.Bot(command_prefix="!", intents=intents)

# Store the last active timestamp for users
user_activity = {}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    check_afk_users.start()  # Start the AFK check loop

@bot.event
async def on_voice_state_update(member, before, after):
    """ Updates the last active time when a user speaks or joins a channel. """
    if after.channel:
        user_activity[member.id] = time.time()

@tasks.loop(seconds=60)  # Run every minute
async def check_afk_users():
    """ Checks for users who have been inactive for 15 minutes. """
    guild = bot.get_guild(GUILD_ID)
    
    for member in guild.members:
        if member.voice and member.voice.channel:  # User must be in a voice channel
            last_active = user_activity.get(member.id, time.time())  
            if time.time() - last_active > AFK_TIME_LIMIT:  # AFK for 15+ mins
                print(f"Moving {member.name} to AFK channel")
                await move_to_afk(member)

async def move_to_afk(member):
    """ Moves a user to the AFK channel, plays an MP3 for 5 minutes, then disconnects them. """
    guild = bot.get_guild(GUILD_ID)
    afk_channel = guild.get_channel(AFK_CHANNEL_ID)

    if afk_channel:
        await member.move_to(afk_channel)  # Move to AFK channel
        print(f"{member.name} moved to AFK channel. Playing audio...")

        voice_client = await afk_channel.connect()
        voice_client.play(discord.FFmpegPCMAudio(AUDIO_FILE))

        await asyncio.sleep(AUDIO_PLAY_TIME)  # Wait 5 minutes while playing audio

        await voice_client.disconnect()  # Disconnect bot
        if member.voice and member.voice.channel == afk_channel:
            await member.move_to(None)  # Forcefully disconnect the user
            print(f"{member.name} has been disconnected after AFK.")

@bot.command()
async def shutdown(ctx):
    """Shuts down the bot."""
    await ctx.send("Shutting down bot...")
    await bot.close()  # This will stop the bot

bot.run(TOKEN)
