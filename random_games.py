from discord.ui import View, Button
from discord import app_commands 
from discord.ext import commands
import discord
import random 
import asyncio 

answers = {
    0: "0️⃣",
    1: "1️⃣",
    2: "2️⃣",
    3: "3️⃣",
    4: "4️⃣",
    5: "5️⃣",
    6: "6️⃣",
    7: "7️⃣",
    8: "8️⃣",
    9: "9️⃣"
    }

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Random_Cog(bot))

class Random_Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    coinflip_description = "Flip a coin: heades or tails?"
    @app_commands.command(name = "coinflip", description = coinflip_description) 
    async def coinflip(self, interaction: discord.Interaction):
        class Window(View):
            def __init__(self):
                super().__init__()
                self.username = interaction.user.name
            
            @discord.ui.button(label = "Heads", style = discord.ButtonStyle.blurple)
            async def heads(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.edit_message(content = "Flipping the coin...")
                answer = random.randint(0, 1)
                await asyncio.sleep(0.5)
                if answer == 0:
                    await interaction.edit_original_response(content = f"It was tails... Maybe another time you will be luckier?")
                else:
                    await interaction.edit_original_response(content = f"Congratulations {self.username} it was heads indeed!")
            
            @discord.ui.button(label = "Tails", style = discord.ButtonStyle.blurple)
            async def tails(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.edit_message(content = "Flipping the coin...")
                answer = random.randint(0, 1)
                await asyncio.sleep(0.5)
                if answer == 0:
                    await interaction.edit_original_response(content = f"Congratulations {self.username} it was tails indeed!")
                else:
                    await interaction.edit_original_response(content = f"It was tails... Maybe another time you will be luckier?")
            
            @discord.ui.button(label = "Quit", style = discord.ButtonStyle.red)
            async def coinflip_quit(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.stop()
                await interaction.response.edit_message(content = "It's the end for now...")
                await asyncio.sleep(0.5)
                await interaction.delete_original_response()
        window = Window()
        await interaction.response.send_message("Welcome to Coinflip: Heads or Tails?", view = window)
    
    
    
    dice_description = "Roll the dice"
    @app_commands.command(name = "diceroll", description = dice_description) 
    async def diceroll(self, interaction: discord.Interaction):
        class Window(View):
            def __init__(self):
                super().__init__()
            
            @discord.ui.button(label = "Roll", style = discord.ButtonStyle.blurple)
            async def roll(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.edit_message(content = "Rolling the dice...")
                answer = random.randint(1, 6)
                if button.label == "Roll":
                    button.label = "Re-roll"
                await asyncio.sleep(0.5)
                await interaction.edit_original_response(content = f"It's {answers[answer]}. Wanna re-roll?", view = window)

            @discord.ui.button(label = "Quit", style = discord.ButtonStyle.red)
            async def dice_quit(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.stop()
                await interaction.response.edit_message(content = "It's the end for now...")
                await asyncio.sleep(0.5)
                await interaction.delete_original_response()
        window = Window()
        await interaction.response.send_message("Welcome to Dice Roll! Roll the dice to get a number between 1 and 6.", view = window)  
        
    
    
    random_roll_description = "Roll a number between 1 and 100"
    @app_commands.command(name = "randomroll", description = random_roll_description) 
    async def randomroll(self, interaction: discord.Interaction):
        class Window(View):
            def __init__(self):
                super().__init__()
        
            @discord.ui.button(label = "Roll", style = discord.ButtonStyle.blurple)
            async def roll(self, interaction: discord.Interaction, button: discord.ui.Button):
                answer = random.randint(1, 100)
                stranswer = str(answer)
                await interaction.response.edit_message(content = "Rolling a random number...")
                if button.label == "Roll":
                    button.label = "Re-roll"
                await asyncio.sleep(0.5)
                if len(stranswer) == 1:
                    await interaction.edit_original_response(content = f"It's {answers[answer]}. Wanna re-roll?", view = window)
                elif len(stranswer) == 2:
                    result = f"{answers[int(stranswer[0])]}{answers[int(stranswer[1])]}"
                    await interaction.edit_original_response(content = f"It's {result}. Wanna re-roll?", view = window)
                else:
                    await interaction.edit_original_response(content = "It's 1️⃣0️⃣0️⃣. Wanna re-roll?", view = window)
        
            @discord.ui.button(label = "Quit", style = discord.ButtonStyle.red)
            async def random_quit(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.stop()
                await interaction.response.edit_message(content = "It's the end for now...")
                await asyncio.sleep(0.5)
                await interaction.delete_original_response()
        
        window = Window()
        await interaction.response.send_message("Welcome to Random Roll! Roll a number between 1 and 100.", view = window)

    
    
    roulette_description = "Play Russian Roulette alone or with friends"
    @app_commands.command(name = "russian_roulette", description = roulette_description) 
    async def roulette(self, interaction: discord.Interaction):
        class Window(View):
            def __init__(self):
                super().__init__()  
                self.gun = ["empty", "empty", "bullet", "empty", "empty", "empty"]
                random.shuffle(self.gun)
                self.gun_copy = self.gun.copy()
                self.bullets_left = 6
                self.progress_log = ""
                self.quit_permissions = []
                self.game_end = False
            
            '''if self.game_end == True:
               @discord.ui.button(label = "Play again", style = discord.ButtonStyle.green)
               async def roulette_again(self, interaction: discord.Interaction, button: discord.ui.Button):
                   pass'''

            @discord.ui.button(label = "Take a shot", style = discord.ButtonStyle.blurple)
            async def shoot(self, interaction: discord.Interaction, button: discord.ui.Button):
                username = interaction.user.name
                if username not in self.quit_permissions:
                    self.quit_permissions.append(username)
                if self.gun_copy[0] != "bullet":
                    self.bullets_left -= 1
                    self.gun_copy.pop(0)
                    self.progress_log += f"That wasn't a bullet! Shots left: {self.bullets_left}\n"
                    await interaction.response.edit_message(content = self.progress_log, view = window)
                else:
                    button.disabled = True
                    self.progress_log += f"{username} shot themselves"
                    await interaction.response.edit_message(content = self.progress_log, view = window)
                    self.game_end = True 
            
            @discord.ui.button(label = "Quit", style = discord.ButtonStyle.red)
            async def roulette_quit(self, interaction: discord.Interaction, button: discord.ui.Button):
                username = interaction.user.name
                if username not in self.quit_permissions:
                    await interaction.response.defer()
                    await interaction.followup.send("To quit the game you need to be its participant!", ephemeral = True)
                else:
                    self.stop()
                    await interaction.response.edit_message(content = "It's the end for now...")
                    await asyncio.sleep(0.5)
                    await interaction.delete_original_response()
            
        window = Window()
        await interaction.response.send_message("Welcome to Russian Roulette! Take a shot.", view = window)            


    

        
        
            