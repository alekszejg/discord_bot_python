import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord import Interaction, app_commands

load_dotenv()

intents = discord.Intents.all()
intents.message_content = True
intents.members = True 
intents.voice_states = True

class MainBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix = "/", intents=intents)
    
    async def setup_hook(self):
        print("Loading advertisement features...")
        await self.load_extension("ad_bot")
        print("Loaded advertisement features.")
        print("Loading file sharing features...")
        await self.load_extension("file_bot")
        print("Loaded file sharing features.")
        print("Loading bot's responses...")
        await self.load_extension("bot_responses")
        print("Loaded bot's responses.")
        print("Loading reaction role features...")
        await self.load_extension("bot_reaction_roles")
        print("Loaded reaction role features.")
        print("Loading a calculator...")
        await self.load_extension("calculator_bot")
        print("Loaded a calculator.")
        print("Loading random games...")
        await self.load_extension("random_games")
        print("Loaded random games.")
        print("Loading a Youtube music bot...")
        await self.load_extension("music_bot")
        print("Loaded a Youtube music bot.")
        print("Loading feedback form...")
        await self.load_extension("feedback")
        print("Loaded the feedback form.")
        
    async def on_ready(self):
        try:
            await self.tree.sync()
            print("All of my commands have loaded.")
            print("I'm online!") 

            if self.get_cog("Responses_Cog") is not None:
                responses_cog = self.get_cog("Responses_Cog")
                responses_cog.daily_fact.start()
        
        except Exception as error:
            print(f"{error} has occured")

bot = MainBot()
bot.run(os.getenv("bot_token"))









