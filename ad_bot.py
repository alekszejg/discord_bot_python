import discord
from discord.ext import commands
from discord import Interaction
from discord import app_commands
import sqlite3

# Database setup
db_connection = sqlite3.connect("local_database.db")
cursor = db_connection.cursor()

user_table = """CREATE TABLE IF NOT EXISTS
allowed_usernames(user_key INTEGER PRIMARY KEY, username TEXT)"""
cursor.execute(user_table)

ad_channel_table = """CREATE TABLE IF NOT EXISTS
allowed_ad_channels(channel_key INTEGER PRIMARY KEY, allowed_channel TEXT, channel_id INTEGER, guild_id INTEGER)"""
cursor.execute(ad_channel_table)
db_connection.commit()

# Inserting owner into db
owner_name = "AlexeyRussian??#4175"
owner_check = "SELECT COUNT (username) FROM allowed_usernames WHERE username = ?"
cursor.execute(owner_check, (owner_name,))
result = cursor.fetchone()[0]
if result == 0:
    add_command = "INSERT INTO allowed_usernames (username) VALUES (\""
    db_owner = "INSERT INTO allowed_usernames (username) VALUES (\""
    add_owner = f"{add_command}{owner_name}\")"
    cursor.execute(add_owner)
    db_connection.commit()    

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Ads_Cog(bot))

class Ads_Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    '''verify_user = str(interaction.user)
        verification = "SELECT COUNT (username) FROM allowed_usernames WHERE username = ?"
        cursor.execute(verification, (verify_user,))
        result = cursor.fetchone()[0]
        if result > 0:'''
    
    '''else:
            private_message = "You have no rights to use this command."
            await interaction.response.send_message(private_message, ephemeral = True)'''
    
    advertise_description = "Bot sends the URL to specified text channels"
    @app_commands.command(name = "advertise", description = advertise_description)
    @app_commands.describe(url = "Insert the URL to share with others")
    @app_commands.describe(optional_title = "An optional title that appears before the shared URL. Useful when separating a title from an optional description")
    @app_commands.describe(optional_description = "An optional description to appear before the shared URL")
    @app_commands.describe(send_as = "Send the URL as a preview visible only to you, or send the URL to public")
    @app_commands.choices(send_as = [
        discord.app_commands.Choice(name = "Send as a preview", value = "preview"),
        discord.app_commands.Choice(name = "Send as a public message", value = "public")
    ])
    @app_commands.describe(send_to = "Which text channels shall receieve the message containing the URL")
    @app_commands.choices(send_to = [
        discord.app_commands.Choice(name = "Send it to the current text channel", value = "current"),
        discord.app_commands.Choice(name = "Send it to all text channels in the current server", value = "local"),
        discord.app_commands.Choice(name = "Send it to all text channels in all servers available to the bot", value = "global"),
        discord.app_commands.Choice(name = "Send it to all text channels that were selected previously", value = "selective")
    ])
    
    async def advertise(self, interaction: discord.Interaction, url: str, send_as: discord.app_commands.Choice[str], 
                        send_to: discord.app_commands.Choice[str], optional_title: str = None, optional_description: str = None): 
        await interaction.response.defer()
        
        message_content = ""
        if optional_title is not None and optional_description is not None:
            message_content = optional_title + "\n\n" + optional_description
        
        elif optional_title is not None:
            message_content = optional_title
        
        elif optional_description is not None:
            message_content = optional_description
        
        
        if send_to.value == "current":
            
            if send_as.value == "public":
                private_message = "Your URL was sent to the current text channel"
                await interaction.followup.send(content = message_content)
                await interaction.followup.send(content = private_message, ephemeral = True)
            
            else:
                private_message = "Here is the content preview with your URL"
                await interaction.followup.send(content = message_content, ephemeral = True)
                await interaction.followup.send(content = private_message, ephemeral = True)
    
        elif send_to.value == "local":
            
            if send_as.value == "public":
                server_channels = interaction.guild.text_channels
                for text_channel in server_channels:
                    await text_channel.send(content = message_content)
                private_message = "Your URL was sent to all text channels on this server."
                await interaction.followup.send(content = private_message, ephemeral = True)
            
            else:
                private_message = "Here is the content preview. It was only sent to this channel."
                await interaction.followup.send(content = message_content, ephemeral = True)
                await interaction.followup.send(content = private_message, ephemeral = True)

        elif send_to.value == "global":
            
            if send_as.value == "public":
                all_guilds = self.bot.guilds
                for guild in all_guilds:
                    for channel in guild.channels:
                        if str(channel.type) == "text":
                            await channel.send(content = message_content)
                private_message = "Your URL was sent to all text channels on all servers that the bot had access to."
                await interaction.followup.send(content = private_message, ephemeral = True)
           
            else:
                private_message = "Here is the content preview. It was only sent to this channel."
                await interaction.followup.send(content = message_content, ephemeral = True)
                await interaction.followup.send(content = private_message, ephemeral = True)

        else:
            
            if send_as.value == "public":
                pass
            
            else:
                private_message = "Here is the content preview. It was only sent to this channel."
                await interaction.followup.send(content = message_content, ephemeral = True)
                await interaction.followup.send(content = private_message, ephemeral = True)
    
    def channel_scanner(self, text_channels, input_channel, guild_id):
        channel_match = None
        permission = False 
        already_added = False
        duplicate = False 
        
        for channel in text_channels:
            
            if channel.name == input_channel and channel_match is None:
                channel_id = channel.id 
                id_request = "SELECT COUNT (channel_id) FROM allowed_ad_channels WHERE guild_id = ? AND channel_id = ?"
                allowed_channel_id = cursor.execute(id_request, (guild_id, channel_id)).fetchone()[0]
                
                if channel.permissions_for(channel.guild.me).send_messages and allowed_channel_id == 0:
                    channel_match = True
                    permission = True
                
                elif channel.permissions_for(channel.guild.me).send_messages and allowed_channel_id > 1:
                    channel_match = True
                    permission = True
                    already_added = True
               
                elif channel.permissions_for(channel.guild.me).send_messages is False and allowed_channel_id == 0:
                    channel_match = True
                    permission = False

                elif channel.permissions_for(channel.guild.me).send_messages is False and allowed_channel_id > 1:
                    channel_match = True
                    permission = False
                    already_added = True
            
            elif channel.name == input_channel and channel_match is not None:
                duplicate = True
            
        return {'match': channel_match, 'permission': permission, 'already added': already_added, 'duplicate': duplicate}
    
    
    add_ad_channel_description = "Adds a channel on this server to which the bot can send the URLs"
    @app_commands.command(name = "add_add_channel", description = add_ad_channel_description)
    @app_commands.describe(add_channel = "A text channel on this server that you wish to add")
    async def add_file_channel(self, interaction: discord.Interaction, add_channel: str):
        await interaction.response.defer()
        text_channels = interaction.guild.text_channels
        guild_id = interaction.guild_id
        results = Ads_Cog.channel_scanner(text_channels, add_channel.lower(), guild_id)

        if results["match"] is not None:
            
            if results["duplicate"] is True:
                private_message = f"I couldn't add the channel '{results['match'].name}' since it appears that the other channel(s) share the same "
                private_message += "name with it. Please make the channel names unique to avoid the confusion afterwards and try again."
            
            elif results["already_added"] is True and results["permission"] is True:
                private_message = f"The channel '{results['match'].name}' appears to be already added to the selection. "
                private_message += "Please add another channel."
                await interaction.followup.send(private_message, ephemeral = True)
            
            elif results["already_added"] is True and results["permission"] is False:
                private_message = f"The channel {results['match'].name} appears to be already added, "
                private_message += "yet I don't have the permission to send messages there. Please enable the permission or "
                private_message += "remove the channel from the list of text channels that I may send the URLs to."
                await interaction.followup.send(private_message, ephemeral = True)

            elif results["already_added"] is False and results["permission"] is True:
                add_request = "INSERT INTO allowed_ad_channels (allowed_channel, channel_id, guild_id) VALUES (?, ?, ?)"
                cursor.execute(add_request, (results["match"].name, results["match"].id, guild_id))
                db_connection.commit()
                private_message = f"I added the channel '{results['match'].name}' to the list of text channels where URLs can be sent."
                await interaction.followup.send(content = private_message, ephemeral = True)

            elif results["already_added"] is False and results["permission"] is False:
                private_message = f"I don't have the permission to send text messages to the channel '{results['match'].name}'. "
                private_message += "Please enable the permission and try adding the channel again, or add another text channel."
                await interaction.followup.send(private_message, ephemeral = True)

        else:
            private_message = f"I couldn't find the channel '{add_channel}' on this server. Please double check its spelling and existence."
            await interaction.followup.send(content = private_message, ephemeral = True)
    
    
    remove_ad_channel_description = "Remove a channel on this server to which the bot can send the URLs"
    @app_commands.command(name = "remove_ad_channel", description = remove_ad_channel_description)
    @app_commands.describe(remove_channel = "A text channel on this server that you wish to remove")
    async def remove_file_channel(self, interaction: discord.Interaction, remove_channel: str):
        await interaction.response.defer()
        text_channels = interaction.guild.text_channels
        guild_id = interaction.guild_id
        results = Ads_Cog.channel_scanner(text_channels, remove_channel.lower(), guild_id)
          
        if results["match"] is not None:
            
            if results["duplicate"] is True:
                private_message = f"I couldn't remove the channel '{results['match'].name}' since it appears that the other channel(s) share the same "
                private_message += "name with it. Please make the channel names unique to avoid the confusion afterwards and try again."

            elif results["already added"] is True:
                cursor.execute("DELETE FROM allowed_ad_channels WHERE channel_id = ?", (results["match"].id,))
                db_connection.commit()
                private_message = f"I removed the channel '{results['match'].name}' from the selection of text channels on this server."
                await interaction.followup.send(content = private_message, ephemeral = True)

            elif results["already added"] is False:
                private_message = f"The channel '{results['match'].name}' was never added to the selection, therefore I couldn't remove it."
                await interaction.followup.send(private_message, ephemeral = True)
        
        else:
            private_message = f"I couldn't find the channel '{remove_channel}' on this server. Please double check its spelling and existence."
            await interaction.followup.send(content = private_message, ephemeral = True)
    
    
    view_channels_description = "Bot shows selected channels to which it can send the URLs"
    @app_commands.command(name = "view_ad_channels", description = view_channels_description)
    async def view_ad_channels(self, interaction: discord.Interaction):
        await interaction.response.defer()
        text_channels = interaction.guild.text_channels
        guild_id = interaction.guild_id
    
        already_added = "Channels that were added to the selection:"
        recommendations = "\n\nChannels that you could add to the selection:"
        
        for channel in text_channels:
            
            if channel.permissions_for(channel.guild.me).send_messages:
                channel_id = channel.id
                id_request = "SELECT COUNT (channel_id) FROM allowed_ad_channels WHERE guild_id = ? AND channel_id = ?"
                allowed_channel_id = cursor.execute(id_request, (guild_id, channel_id)).fetchone()[0]
                
                if allowed_channel_id > 0:
                    already_added += f"\n{channel.name}"
                
                else:
                    recommendations += f"\n{channel.name}"
        
        private_message = f"{already_added}{recommendations}"
        await interaction.followup.send(private_message, ephemeral = True)
    
    