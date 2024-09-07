import discord
from discord.ext import commands
from discord import app_commands
from discord import ui
from discord.ui import View, Button

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Feedback_Cog(bot))

class Feedback_Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    class Feedback(ui.Modal, title="Feedback Form"):
        def __init__(self, privacy):
            super().__init__()
            self.privacy = privacy.value
        subject = ui.TextInput(label='Subject:', style=discord.TextStyle.short)
        content = ui.TextInput(label='Please share your feedback with us:', style=discord.TextStyle.paragraph)

        async def on_submit(self, interaction: discord.Interaction):

            if self.privacy == "public":
                server_owner = interaction.guild.owner
                
                if interaction.user.nick is not None:
                    dm_message = f"The user '{interaction.user.name}' with a nickname '{interaction.user.nick}' from your server "
                    dm_message += f"'{interaction.guild.name}' has sent you the feedback form \n\n"
                    dm_message+= f"Subject:\n{self.subject}\n\nFeedback Message:\n{self.content}"
                    await server_owner.send(dm_message)
                    await interaction.response.send_message("Your feedback was sent to the owner of this server", ephemeral = True)
                
                else:
                    dm_message = f"The user '{interaction.user.name}' from your server '{interaction.guild.name}' "
                    dm_message += f"has sent you the feedback form \n\nSubject:\n{self.subject}\n\nFeedback Message:\n{self.content}"
                    await server_owner.send(dm_message)
                    await interaction.response.send_message("Your feedback was sent to the owner of this server", ephemeral = True)
            
            else:
                server_owner = interaction.guild.owner
                dm_message = f"A user from your server '{interaction.guild.name}' who preferred to stay anonymous "
                dm_message += f"has sent you the feedback form \n\nSubject:\n{self.subject}\n\nFeedback Message: {self.content}"
                await server_owner.send(dm_message)
                await interaction.response.send_message("Your feedback was sent anonymously to the owner of this server", ephemeral = True)
        

    feedback_description = "Fill out an anonymous (or not) feedback form to be sent to the server's owner"
    @app_commands.command(name = "feedback_form", description = feedback_description)
    @app_commands.describe(privacy = "Whether your username will be shown to the receiver of the feedback form")
    @app_commands.choices(privacy = [
        discord.app_commands.Choice(name = "Send the feedback form anonymously", value = "private"),
        discord.app_commands.Choice(name = "Send the feedback form with your username visible", value = "public")
    ]) 
    
    async def feedback(self, interaction: discord.Interaction, privacy: discord.app_commands.Choice[str]):
        await interaction.response.send_modal(Feedback_Cog.Feedback(privacy))
    

    class Report(ui.Modal, title="Report Form"):
        def __init__(self, privacy, username):
            super().__init__()
            self.privacy = privacy.value
            self.username = username 
        subject = ui.TextInput(label='Brief reason for your report:', style=discord.TextStyle.short)
        description = ui.TextInput(label='Please provide more info:', style=discord.TextStyle.paragraph)
    
    report_description = "Select a specific user to report anonymously (or not)"
    @app_commands.command(name = "report_form", description = report_description)
    @app_commands.describe(privacy = "Whether your username will be shown to the receiver of the report form")
    @app_commands.choices(privacy = [
        discord.app_commands.Choice(name = "Send the report form anonymously", value = "private"),
        discord.app_commands.Choice(name = "Send the report form with your username visible", value = "public")
    ])
    @app_commands.describe(report_user = "The username you wish to report")
    
    async def report(self, interaction: discord.Interaction, privacy: discord.app_commands.Choice[str], report_user: str):
        await interaction.response.defer(ephemeral = True)
        
        search_status = None
        for member in interaction.guild.members:
            
            if report_user.strip() == member.name:
                
                if interaction.guild.owner.name == member.name:
                    private_message = "You aren't allowed to report the owner of this server."
                    search_status = True
                    await interaction.followup.send(content = private_message, ephemeral = True)
                    break

                elif interaction.guild.me.name == member.name:
                    private_message = "You aren't allowed to report me or other bots."
                    await interaction.followup.send(content = private_message, ephemeral = True)
                    search_status = True
                    break

                else:
                    await interaction.response.send_modal(Feedback_Cog.Report(privacy, report_user))
                    search_status = True
                    break


        if search_status is None:
            private_message = f"I couldn't find the user named '{report_user.strip()}' in this guild. Please double check "
            private_message += "the spelling of their username and its existance."
            await interaction.followup.send(content = private_message, ephemeral = True)

