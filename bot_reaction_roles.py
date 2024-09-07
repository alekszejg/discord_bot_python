import discord 
from emoji import demojize, emojize, is_emoji
from discord.ext import commands
from discord import app_commands
import sqlite3

# Database setup
db_connection = sqlite3.connect("local_database.db")
cursor = db_connection.cursor()
role_table = """CREATE TABLE IF NOT EXISTS
reaction_roles(role_key INTEGER PRIMARY KEY, guild TEXT, role TEXT, emoji TEXT)"""
cursor.execute(role_table)
personal_table = """CREATE TABLE IF NOT EXISTS 
important_data(key INTEGER PRIMARY KEY, guild TEXT, guild_id INTEGER, channel_id INTEGER, message_id INTEGER)"""
cursor.execute(personal_table)
db_connection.commit()

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Reactions_Cog(bot))

class Reactions_Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot_name = str(self.bot.user)
        self.bot_role = self.bot_name[:len(self.bot_name) - 5]
        self.bot_id = self.bot.application_id
    
    # Guild role listeners 
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        guild_name = role.guild.name
        count_query = "SELECT COUNT (role) FROM reaction_roles WHERE role = ? AND guild = ?"
        count_result = cursor.execute(count_query, (role.name, guild_name)).fetchone()[0]
        if count_result > 0:
            delete_query = "DELETE FROM reaction_roles WHERE role = ? AND guild = ?"
            cursor.execute(delete_query, (role.name, guild_name))
            db_connection.commit()
            
    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        guild_name = before.guild.name
        count_query = "SELECT COUNT (role) FROM reaction_roles WHERE role = ? AND guild = ?"
        count_result = cursor.execute(count_query, (before.name, guild_name)).fetchone()[0]
        if count_result > 0:
            update_request = "UPDATE reaction_roles SET role = ? WHERE role = ? AND guild = ?"
            cursor.execute(update_request, (after.name, before.name, guild_name))
            db_connection.commit()

    # Reaction listeners 
    @commands.Cog.listener()         
    async def on_raw_reaction_add(self, payload):
        reaction_member = payload.member 
        user_id = payload.user_id
        reaction_emoji = demojize(str(payload.emoji))
        guild_id = payload.guild_id
        message_id = payload.message_id
        check_message = cursor.execute("SELECT guild, message_id FROM important_data WHERE guild_id = ?", (guild_id,)).fetchone()
        if check_message is not None and check_message[1] == message_id and user_id != self.bot_id:
            guild_name = check_message[0]
            role_request = cursor.execute("SELECT role FROM reaction_roles WHERE guild = ? and emoji = ?", (guild_name, reaction_emoji)).fetchone()
            if role_request is not None:
                guild = discord.utils.find(lambda g: g.id == guild_id, self.bot.guilds)
                role = discord.utils.get(guild.roles, name = role_request[0])
                await reaction_member.add_roles(role) 
                
    @commands.Cog.listener()  
    async def on_raw_reaction_remove(self, payload):
        user_id = payload.user_id
        reaction_emoji = demojize(str(payload.emoji))
        guild_id = payload.guild_id
        message_id = payload.message_id
        check_message = cursor.execute("SELECT guild, message_id FROM important_data WHERE guild_id = ?", (guild_id,)).fetchone()
        if check_message is not None and check_message[1] == message_id and user_id != self.bot_id:
            guild_name = check_message[0]
            role_request = cursor.execute("SELECT role FROM reaction_roles WHERE guild = ? and emoji = ?", (guild_name, reaction_emoji)).fetchone()
            if role_request is not None:
                guild = discord.utils.find(lambda g: g.id == guild_id, self.bot.guilds)
                role = discord.utils.get(guild.roles, name = role_request[0])
                member = discord.utils.find(lambda m: m.id == user_id, guild.members)
                await member.remove_roles(role)
                
                    
    # Reaction message 
    launch_reaction_description = "Launch 1st reaction message to get started with reaction roles"
    @app_commands.command(name = "launch_reaction_roles", description = launch_reaction_description)
    async def launch_reaction(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral = False) 
        guild_name = interaction.guild.name
        guild_id = interaction.guild.id
        channel_id = interaction.channel_id
        check_message = cursor.execute("SELECT COUNT (message_id) FROM important_data WHERE guild = ?", (guild_name,)).fetchone()[0]
        if check_message > 0:
            private_message = "Reaction message already exists on this server"
            await interaction.followup.send(private_message, ephemeral = False)
        else:
            view_request = cursor.execute("SELECT role, emoji FROM reaction_roles WHERE guild = ?", (guild_name,)).fetchall()
            public_message = "Please pick your roles:\n\n"
            emojis = []
            for role in view_request:
                emoji = emojize(role[1])
                emojis.append(emoji)
                public_message += f"{emoji} '{role[0]}'\n" 
            message = await interaction.followup.send(public_message)
            for emoji in emojis:
                await message.add_reaction(emoji)
            message_id = message.id
            add_message_id_request = "INSERT INTO important_data (guild, guild_id, channel_id, message_id) VALUES (?, ?, ?, ?)"
            cursor.execute(add_message_id_request, (guild_name, guild_id, channel_id, message_id))
            db_connection.commit()
             
    # Add reaction roles
    add_description = "Add a role and an emoji associated with it to available reaction roles"
    @app_commands.command(name = "add_reaction_role", description = add_description)
    @app_commands.describe(role = "Add a role which hasn't been added before to link it to an emoji")
    @app_commands.describe(emoji = "Paste an emoji to be associated with added role")
    async def add_role(self, interaction: discord.Interaction, role: str, emoji: str):
        await interaction.response.defer(ephemeral = True)
        guild_name = interaction.guild.name
        guild_id = interaction.guild_id
        clean_role = role.strip()
        roles = interaction.guild.roles
        role_result = ""
        for each_role in roles:
            if str(each_role) != self.bot_role and str(each_role) != "@everyone" and str(each_role) == clean_role:
                role_result = clean_role
        role_exists = cursor.execute("SELECT COUNT (role) FROM reaction_roles WHERE role = ? AND guild = ?", (role_result, guild_name)).fetchone()[0]
  
        def emoji_validator(emoji):
            str_emoji = demojize(emoji)
            if str_emoji.startswith(":") and str_emoji.endswith(":") and is_emoji(emoji):
                return (str_emoji, "standard emoji")
            elif str_emoji.startswith("<") and str_emoji.endswith(">"): 
                for custom_emoji in interaction.guild.emojis:
                    if custom_emoji.name in str_emoji:
                        return (str_emoji, "custom emoji")
            else:
                return ("invalid",)
        emoji_type = emoji_validator(emoji)

        if role_result == "" and emoji_type[0] == "invalid":
            private_message = f"I couldn't find the role '{clean_role}' and couldn't detect the emoji '{emoji}' on this server, "
            private_message += "therefore I couldn't add the reaction role. Please double check role's and emoji's spelling (I accept a single standard or custom emoji) "
            private_message += "and their presence on the server."
            await interaction.followup.send(private_message, ephemeral = True)
        elif role_result == "" or emoji_type[0] == "invalid":
            if role_result == "":
                private_message = f"I couldn't find the role '{role}' on this server, therefore I couldn't add it to reaction roles. " 
                private_message += "Please double check its spelling and its presence on the server."
                await interaction.followup.send(private_message, ephemeral = True)
            else:
                private_message = f"I couldn't detect the emoji '{emoji}', therefore I couldn't add the reaction role. "
                private_message += "Please double check its spelling (I accept a single standard or custom emoji) and its presence on the server."
                await interaction.followup.send(private_message, ephemeral = True)
        
        elif role_result != "" and role_exists == 0 and emoji_type[0] != "invalid":
            add_role = cursor.execute("INSERT INTO reaction_roles (guild, role, emoji) VALUES (?, ?, ?)", (guild_name, role_result, emoji_type[0]))
            db_connection.commit()
            private_message = f"I added a new reaction role {emoji} '{role_result}' ({emoji_type[1]})"
            await interaction.followup.send(private_message, ephemeral = True)
            check_message = cursor.execute("SELECT channel_id, message_id FROM important_data WHERE guild_id = ?", (guild_id,)).fetchone()
            if check_message is not None:
                reaction_channel = interaction.guild.get_channel(check_message[0])
                reaction_message = await reaction_channel.fetch_message(check_message[1])
                new_content = f"{reaction_message.content}\n{emojize(emoji_type[0])} '{role_result}'\n"
                await reaction_message.edit(content = new_content)
                await reaction_message.add_reaction(emojize(emoji_type[0]))
        elif role_result != "" and role_exists > 0 and emoji_type[0] != "invalid":
            old_request = cursor.execute("SELECT emoji FROM reaction_roles WHERE role = ? AND guild = ?", (role_result, guild_name)).fetchone()[0]
            update_request = "UPDATE reaction_roles SET emoji = ? WHERE role = ? AND guild = ?"
            cursor.execute(update_request, (emoji_type[0], role_result, guild_name))
            db_connection.commit()
            private_message = f"I updated the reaction role {emoji} '{role_result}' ({emoji_type[1]}) "
            await interaction.followup.send(private_message, ephemeral = True)
            check_message = cursor.execute("SELECT channel_id, message_id FROM important_data WHERE guild_id = ?", (guild_id,)).fetchone()
            if check_message is not None:
                reaction_channel = interaction.guild.get_channel(check_message[0])
                reaction_message = await reaction_channel.fetch_message(check_message[1])
                role_request = cursor.execute("SELECT role, emoji FROM reaction_roles").fetchall()
                public_message = "Please pick your roles:\n\n"
                for role, emoji in role_request:
                    public_message += f"{emojize(emoji)} '{role}\n"
                bot_member = interaction.guild.get_member(self.bot_id)
                await reaction_message.remove_reaction(emojize(old_request), bot_member)
                await reaction_message.edit(content = public_message)
                await reaction_message.add_reaction(emojize(emoji_type[0]))

    # Delete reaction roles 
    remove_description = "Remove a role and an emoji associated with it from available reaction roles"
    @app_commands.command(name = "remove_reaction_role", description = remove_description)
    @app_commands.describe(role = "A role to be removed from available reaction roles")
    async def remove_role(self, interaction: discord.Interaction, role: str):
        await interaction.response.defer(ephemeral = True)
        guild_name = interaction.guild.name 
        guild_id = interaction.guild_id
        guild_roles = interaction.guild.roles
        clean_role = role.strip()
        role_result = ""
        for role in guild_roles:
            if str(role) != self.bot_role and str(role) != "@everyone" and str(role) == clean_role:
                role_result = clean_role
        role_exists = cursor.execute("SELECT COUNT (role) FROM reaction_roles WHERE role = ? AND guild = ?", (role_result, guild_name)).fetchone()[0]
        if role_result == "" or (role_result != "" and role_exists == 0):
            if role_result == "":
                private_message = f"I couldn't find the reaction role '{clean_role}' on this server, therefore I couldn't remove it. "
                private_message += "Please double check its spelling and its presence on the server."
                await interaction.followup.send(private_message, ephemeral = True)
            else:
                private_message = f"Role '{clean_role}' wasn't a part of reaction roles"
                await interaction.followup.send(private_message, ephemeral = True)
        elif role_result != "" and role_exists > 0:
            emoji_request = "SELECT emoji FROM reaction_roles WHERE role = ? AND guild = ?"
            deleted_emoji = emojize(cursor.execute(emoji_request, (role_result, guild_name)).fetchone()[0])
            cursor.execute("DELETE FROM reaction_roles WHERE role = ? AND guild = ?", (role_result, guild_name)) 
            db_connection.commit()
            private_message = f"I removed the reaction role {deleted_emoji} '{clean_role}' from available reaction roles"
            await interaction.followup.send(private_message, ephemeral = True)
            check_message = cursor.execute("SELECT channel_id, message_id FROM important_data WHERE guild_id = ?", (guild_id,)).fetchone()
            if check_message is not None:
                reaction_channel = interaction.guild.get_channel(check_message[0])
                reaction_message = await reaction_channel.fetch_message(check_message[1])
                role_request = cursor.execute("SELECT role, emoji FROM reaction_roles WHERE guild_id = ?", (guild_id,)).fetchall()
                public_message = "Please pick your roles:\n\n"
                for role, emoji in role_request:
                    public_message += f"{emojize(emoji)} '{role}\n"
                await reaction_message.edit(content = public_message)
                await reaction_message.remove_reaction(emoji)
           
    # view reaction roles
    view_reaction_description = "View all available reaction roles and emojis associated with them"
    @app_commands.command(name = "view_reaction_roles", description = view_reaction_description)
    async def view_roles(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral = True)
        guild_name = interaction.guild.name 
        guild_roles = interaction.guild.roles
        all_reaction_roles = cursor.execute("SELECT role, emoji FROM reaction_roles WHERE guild = ?", (guild_name,)).fetchall()
        private_message = "Here's the list of currently available reaction roles:\n" 
        reaction_roles = []
        for role in all_reaction_roles:
            private_message += f"{emojize(role[1])} '{role[0]}'\n"
            reaction_roles.append(role[0])
        other_roles = [str(role) for role in guild_roles if str(role) != self.bot_role and str(role) != "@everyone" and str(role) not in reaction_roles]
        private_message += "\nHere's the list of roles which haven't yet been added to reaction roles yet\n"
        counter = 1
        for role in other_roles:
            private_message += f"{counter}) '{role}'\n"
            counter += 1
        await interaction.followup.send(private_message, ephemeral = True)




