import discord
from discord.ext import commands, tasks
import time
import asyncio
import os
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True  # Enable Message Content Intent
intents.voice_states = True
intents.members = True

# Load environment variables from .env file
load_dotenv()

# Get the token from environment variables
TOKEN = os.getenv('DISCORD_TOKEN')

if not TOKEN:
    raise ValueError(
        "No token provided. Please set the DISCORD_TOKEN environment variable."
    )

# Create the bot with the necessary intents
bot = commands.Bot(command_prefix='!', intents=intents)

GUILD_ID = 1338043993103142912  # Your server ID
AFK_CHANNEL_ID = 1338046891577049099  # AFK channel ID
AUDIO_FILE = "you digging in me Sound effect.mp3"
AFK_TIME_LIMIT = 420 * 60  # 1 minute (set to 1 minute for testing)
AUDIO_PLAY_TIME = 5 * 60  # 5 minutes in seconds

# Store the last active timestamp for users
user_activity = {}

# Define the authorized user IDs for the shutdown command
AUTHORIZED_USERS = [393950237279911936]  # Replace with your user ID


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    check_afk_users.start()  # Start the AFK check loop

    # Check all members in voice channels when bot starts
    guild = bot.get_guild(GUILD_ID)
    if guild:
        for member in guild.members:
            if member.voice and member.voice.channel:  # If the member is in a voice channel
                user_activity[
                    member.id] = time.time()  # Update last active time
                print(
                    f"Initial check: {member.name} is in {member.voice.channel.name}"
                )

        @bot.event
        async def on_voice_state_update(member, before, after):
            """ Updates the last active time when a user speaks or joins a channel. """
            if after.channel:  # User joins a voice channel or starts speaking
                user_activity[member.id] = time.time()
                print(
                    f"{member.name} has joined {after.channel.name} or started speaking."
                )

            elif before.channel and not after.channel:  # User leaves a voice channel
                print(
                    f"{member.name} has left {before.channel.name} or stopped speaking."
                )

            # If the member switches channels (e.g., changes channels within the voice chat)
            elif before.channel != after.channel:
                user_activity[member.id] = time.time()
                print(
                    f"{member.name} has moved from {before.channel.name} to {after.channel.name}."
                )


@tasks.loop(seconds=5)  # Run every minute
async def check_afk_users():
    """ Checks for users who have been inactive for the specified time limit. """
    print("Checking for AFK users...")
    guild = bot.get_guild(GUILD_ID)

    if guild is None:
        print(
            f"Failed to fetch guild with ID: {GUILD_ID}. The bot might not be connected properly."
        )
        return

    for member in guild.members:
        if member.voice and member.voice.channel:  # User must be in a voice channel
            last_active = user_activity.get(member.id, time.time())
            time_diff = time.time() - last_active
            print(
                f"Time since last activity for {member.name}: {time_diff:.2f} seconds"
            )

            if time_diff > AFK_TIME_LIMIT:  # AFK for the specified time
                print(f"Moving {member.name} to AFK channel")
                await move_to_afk(member)


async def move_to_afk(member):
    """ Moves a user to the AFK channel, plays an MP3 for the specified duration, then disconnects them. """
    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        print(
            f"Failed to fetch guild with ID: {GUILD_ID} when moving {member.name} to AFK channel."
        )
        return

    afk_channel = guild.get_channel(AFK_CHANNEL_ID)

    if afk_channel is None:
        print(
            f"Failed to fetch AFK channel with ID: {AFK_CHANNEL_ID}. Make sure the channel exists."
        )
        return

    if isinstance(afk_channel, discord.VoiceChannel):
        print(f"Moving {member.name} to AFK channel {afk_channel.name}...")
        await member.move_to(afk_channel)  # Move to AFK channel
        print(f"{member.name} moved to AFK channel. Playing audio...")

        voice_client = await afk_channel.connect()
        print("Connected to the AFK channel.")
        voice_client.play(discord.FFmpegPCMAudio(AUDIO_FILE))

        await asyncio.sleep(AUDIO_PLAY_TIME)  # Wait for audio to play

        await voice_client.disconnect()  # Disconnect bot
        if member.voice and member.voice.channel == afk_channel:
            await member.move_to(None)  # Forcefully disconnect the user
            print(f"{member.name} has been disconnected after AFK.")
    else:
        print(f"AFK channel is not a voice channel or could not be found.")


# Run the bot using the token from the environment variable
bot.run(TOKEN)
