from discord.ui import View, Button
from discord import app_commands 
from discord.ext import commands
import discord
from sympy import sympify
import asyncio 


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Calculator_Cog(bot))

class Calculator_Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    calculator_description = "Calculate whatever needs to be calculated"
    @app_commands.command(name = "calculate", description = calculator_description) 
    async def calculate(self, interaction: discord.Interaction):
        user_input = ""
        window = View()
        bracket_count = 0

        # Number button control 
        class NumberButton(Button):
            def __init__(self, label, value, row, style = discord.ButtonStyle.gray):
                super().__init__(style = style)
                self.label, self.value, self.row = label, value, row
                window.add_item(self)
            
            async def callback(self, interaction):
                nonlocal user_input
                if user_input == "" or user_input[-1] in "(.0123456789" or user_input[:-2] == "(-" or user_input[:-2] == "(+":
                    user_input += self.value
                    await interaction.response.edit_message(content = user_input)
                elif user_input[-1] == ")":
                    user_input += " " + "* " + self.value
                    await interaction.response.edit_message(content = user_input)
                else:
                    user_input += " " + self.value
                    await interaction.response.edit_message(content = user_input)
        
        # Action button control
        class OperationButton(Button):
            def __init__(self, label, value, row, style = discord.ButtonStyle.blurple):
                super().__init__(style = style)
                self.label, self.value, self.row = label, value, row
                window.add_item(self)

            async def callback(self, interaction):
                nonlocal user_input
                nonlocal bracket_count
                self.disabled = False
                if self.value in "+-*/":
                    if user_input[-1] in "0123456789).":
                        user_input += " " + self.value
                        await interaction.response.edit_message(content = user_input)
                    elif user_input[-1] in "(" and self.value in "+-":
                        user_input += self.value
                        await interaction.response.edit_message(content = user_input)
                    else:
                        self.disabled = True 
                        await interaction.response.defer()
                
                elif self.value == ".":
                    if user_input == "":
                        user_input += "0."
                        await interaction.response.edit_message(content = user_input)
                    elif user_input[-1] in "0123456789":
                        user_input += "."
                        await interaction.response.edit_message(content = user_input)
                    elif user_input[-1] in "+-*/":
                        user_input += " " + "0."
                        await interaction.response.edit_message(content = user_input)
                    elif user_input[-1] == ")":
                        user_input += " " + "* 0."
                        await interaction.response.edit_message(content = user_input)
                
                elif self.label == "+/-":
                    if len(user_input) == 1 and user_input[0] in "(0123456789":
                        user_input = f"-({user_input}"
                        bracket_count += 1
                        await interaction.response.edit_message(content = user_input)
                    elif user_input[-1] in "0123456789":
                        second_piece = ""
                        for index, digit in enumerate(user_input[::-1]):
                            if digit not in ".0123456789":
                                first_piece = user_input[:-index]
                                second_piece = user_input[len(user_input) - 1 - index:]
                                user_input = first_piece + f"(-{second_piece}"
                                break
                        if not second_piece:
                            user_input = f"(-{user_input}" 
                        bracket_count += 1
                        await interaction.response.edit_message(content = user_input)
                    elif user_input[-1] == ")":
                        user_input += " " + "* (-"
                        bracket_count += 1
                        await interaction.response.edit_message(content = user_input)
                
                elif self.label == "( )":
                    if user_input[-1] in ".0123456789)" and bracket_count == 0:
                        user_input += " " + "* ("
                        bracket_count += 1
                        await interaction.response.edit_message(content = user_input)
                    elif user_input[-1] in "(+-*/":
                        user_input += "("
                        bracket_count += 1
                        await interaction.response.edit_message(content = user_input)
                    else:
                        user_input += ")"
                        bracket_count -= 1
                        await interaction.response.edit_message(content = user_input)

        class SpecialButton(Button):
            def __init__(self, label, value, row, style = discord.ButtonStyle.green):
                super().__init__(style = style)
                self.label, self.value, self.row = label, value, row
                window.add_item(self)
        
            async def callback(self, interaction):
                nonlocal user_input
                nonlocal bracket_count
                self.disabled = False
                if self.value == "❌":
                    user_input = user_input[:-1]
                    bracket_count = 0
                    await interaction.response.edit_message(content = user_input) 
                
                elif self.value == "🗑️":
                    user_input = ""
                    await interaction.response.edit_message(content = user_input) 
                
                elif self.value == "=":
                    print(user_input)
                    outcome = 0 
                    self.disabled = False 
                    
                    if "/ 0" in user_input:
                        self.disabled = True
                        await interaction.response.edit_message(content = "Can't divide by zero")
                        await asyncio.sleep(1)
                        await interaction.followup.edit_message(content = user_input)
                    
                    elif user_input[-1] in "(+-*/":
                        self.disabled = True
                        await interaction.response.defer() 
                    
                    if bracket_count != 0:
                        user_input += ")" * bracket_count
                        bracket_count = 0
                    
                    if len(user_input) > 0 and outcome % 2 == 0:
                        outcome = int(sympify(user_input))
                        await interaction.response.edit_message(content = outcome)
                    
                    else:
                        outcome = float(sympify(user_input))
                        await interaction.response.edit_message(content = outcome)
                    
                
                    
                    if len(user_input) == 1 or user_input[-1] in ".0123456789":
                        outcome = sympify(user_input)
                    
                    if user_input[-1] in "(+-*/":
                        self.disabled = True
                        await interaction.response.defer() 
                    print(f"outcome: {outcome}")
                    
                    
                    

            
        SpecialButton(label = "🗑️", value = "🗑️", row = 0)
        OperationButton(label = "( )", value = "(", row = 0)
        SpecialButton(label = "❌", value = "❌", row = 0)
        OperationButton(label = "/", value = "/", row = 0)

        NumberButton(label = "7", value = "7", row = 1)
        NumberButton(label = "8", value = "8", row = 1)
        NumberButton(label = "9", value = "9", row = 1)
        OperationButton(label = "x", value = "*", row = 1)
        
        NumberButton(label = "4", value = "4", row = 2)
        NumberButton(label = "5", value = "5", row = 2)
        NumberButton(label = "6", value = "6", row = 2)
        OperationButton(label = "-", value = "-", row = 2)
        
        NumberButton(label = "1", value = "1", row = 3)
        NumberButton(label = "2", value = "2", row = 3)
        NumberButton(label = "3", value = "3", row = 3)
        OperationButton(label = "+", value = "+", row = 3)
        
        OperationButton(label = "+/-", value = "-{}", row = 4)
        NumberButton(label = "0", value = "0", row = 4)
        OperationButton(label = ".", value = ".", row = 4)
        SpecialButton(label = "=", value = "=", row = 4)

        await interaction.response.send_message(content = "Welcome to calculator", ephemeral = True, view = window)

