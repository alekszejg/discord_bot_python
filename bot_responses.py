import os 
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks
from discord import app_commands 
from discord.ui import Button, View
import datetime
from random import randint 
import requests 
import json 

load_dotenv()

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Responses_Cog(bot))

class Responses_Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return 
        if message.content.startswith(greetings):
            await message.channel.send("Hey!")

    # daily facts
    @tasks.loop(hours = 1.0)
    async def daily_fact(self):
        print("\nhere")  
        date_now = datetime.datetime.now()  
        if date_now.hour == 21: 
            limit = 1
            api_url = f"https://api.api-ninjas.com/v1/facts?limit={limit}"
            api_response = requests.get(api_url, headers = {"X-Api-Key": f"{os.getenv("ninja_api_key")}"})
            if api_response.status_code == requests.codes.ok:
                api_answer = json.loads(api_response.text)[0]["fact"]
                channels = self.bot.get_all_channels()
                for channel in channels:
                    if str(channel.type) == "text":
                        await channel.send(f"Today's fact:\n{api_answer}")
                
    # jokes
    joke_description = "Bot will tell a random joke, not necessarily a good one"
    @app_commands.command(name = "say_joke", description = joke_description)         
    async def tell_joke(self, interaction: discord.Interaction):
        limit = 1
        api_url = f"https://api.api-ninjas.com/v1/jokes?limit={limit}"
        api_response = requests.get(api_url, headers = {"X-Api-Key": f"{os.getenv("ninja_api_key")}"}) 
        if api_response.status_code == requests.codes.ok:
            api_answer = json.loads(api_response.text)[0]["joke"]
            await interaction.response.send_message(f"Here's a joke:\n{api_answer}")
        
    # phylosophical quotes
    quote_description = "Bot will tell a random quote about various topics"
    @app_commands.command(name = "say_quote", description = quote_description)         
    async def tell_quote(self, interaction: discord.Interaction):
        category = ("success", "money", "life", "love", "leadership", "knowledge", "intelligence", "inspirational"
                    "future", "friendship", "forgiveness", "anger", "communication", "change", "fear", "learning")
        randomize = randint(0, len(category) - 1)
        api_url = f"https://api.api-ninjas.com/v1/quotes?category={category[randomize]}"
        api_response = requests.get(api_url, headers = {"X-Api-Key": f"{os.getenv("ninja_api_key")}"}) 
        if api_response.status_code == requests.codes.ok:
            api_answer = json.loads(api_response.text)[0]
            await interaction.response.send_message(f"Here's a phylosophical quote:\n\"{api_answer['quote']}\"\nby {api_answer['author']}")

       

        
# Reactions
greetings = ("Hey", "Hello", "Hi", "Greetings", "Hey there", "Yo")



