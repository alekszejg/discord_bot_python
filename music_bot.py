import json
import ffmpeg
import yt_dlp
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, TextInput



ffmpeg_options ={"before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", "options": "-vn"}
ydl_opts = {
    "format": "m4a/bestaudio/best",
    "skip_download": "True",
    "noplaylist": "True",
    "postprocessors": [{  
        "key": "FFmpegExtractAudio",
        "preferredcodec": "m4a",
    }]
}


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Music_Cog(bot))

class Music_Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot_id = self.bot.application_id
    all_players = {}
    
    @classmethod
    def embed_editor(cls, interface, full_song_info):
        queue_entry = f"Title: {full_song_info['title']} {full_song_info['duration']}\n"
        total_length = len(interface.player) + len(queue_entry) 
        
        if interface.all_songs == []:
            interface.all_songs.append(full_song_info)
            interface.player.add_field(name = "Currently playing", value = full_song_info["info"], inline = False)
            interface.player.set_footer(text = "Use /search_youtube again to add more songs to queue")
            return True
        
        elif len(interface.all_songs) == 1:
            interface.all_songs.append(full_song_info)
            interface.player.add_field(name = "Songs in queue", value = queue_entry, inline = False)
            return True
        
        elif total_length <= 6000:
            interface.all_songs.append(full_song_info)
            current_field = interface.player.fields[-1]
            if len(current_field.name + current_field.value) + len(queue_entry) <= 1024:
                new_content = current_field.value + queue_entry
                interface.player.set_field_at(-1, name = current_field.name, value = new_content, inline = False)
                return True
            else :
                interface.player.add_field(name = "", value = queue_entry)
                return True
                
        else:
            return False
    
    @classmethod
    def edit_currently_playing(cls, interface, move_direction):
        current_song_info = interface.all_songs[interface.travel_index]["info"]
        interface.player.set_field_at(0, name = "Currently playing", value = current_song_info, inline = False)
        all_fields = interface.player.fields
        
        if move_direction == "prev":
            song_after = interface.all_songs[interface.travel_index + 1]
            content_after = f"{song_after['title']} {song_after['duration']}\n"
            new_content = content_after + all_fields[1].value
            interface.player.set_field_at(1, name = "Songs in queue", value = new_content, inline = False)
            
        elif move_direction == "next":
            next_limit = all_fields[1].value.find("\n")
            new_content = all_fields[1].value[next_limit + 1:]

            for index in range(1, len(all_fields)):
                
                if index + 1 != len(all_fields):
                    field_value_length = len(new_content) 
                    next_field_splited = all_fields[index + 1].value.split("\n")
                    predicted_length = len(field_value_length) + len(next_field_splited[0])
                    
                    if predicted_length <= 1024:
                        new_content += next_field_splited[0]
                        next_field_splited.pop(0)
                        interface.player.set_field_at(index, name = all_fields[index].name, value = new_content, inline = False)
                    
                    else:
                        interface.player.set_field_at(index, name = all_fields[index].name, value = new_content, inline = False)
                
                else:
                    interface.player.set_field_at(index, name = all_fields[index].name, value = new_content, inline = False)
    
    
    @classmethod
    def play_previous(cls, interface, voice_connection, all_songs):
        if interface.travel_index - 1 >= 0:
            interface.travel_index -= 1
            voice_connection.pause()
            voice_connection.play(all_songs[interface.travel_index]["music file"], after = lambda e: cls.play_next(interface, voice_connection, all_songs))
            cls.edit_currently_playing(interface, "prev")
            return True 
        else:
            return False
    
    @classmethod
    def play(cls, interface, voice_connection, all_songs):
        specific_song = all_songs[interface.travel_index]
        voice_connection.play(specific_song["music file"], after = lambda e: cls.play_next(interface, voice_connection, all_songs))
        cls.embed_editor(interface, specific_song)
    

    @classmethod
    def play_next(cls, interface, voice_connection, all_songs):
        if interface.travel_index + 1 <= len(interface.all_songs) - 1:
            interface.travel_index += 1
            voice_connection.pause()
            voice_connection.play(all_songs[interface.travel_index]["music file"], after = lambda e: cls.play_next(interface, voice_connection, all_songs))
            cls.edit_currently_playing(interface, "next")
            return True
        else:
            return False 
    

    class YoutubeInterface(View):
        def __init__(self):
            super().__init__()
            self.logo = discord.File("Music Player logos/youtube.png", filename = "youtube.png")
            self.player = discord.Embed(title = "Youtube Music Player", color = discord.Colour.red())
            self.player.set_thumbnail(url="attachment://youtube.png")
            self.all_songs = []
            self.travel_index = 0
            self.pause_button = ""

        @discord.ui.button(label = "⏮️ Previous", style = discord.ButtonStyle.grey)
        async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
            button.disabled = False
            guild_id = interaction.guild_id
            interface = Music_Cog.all_players[guild_id]["interface"]
            voice_connection = Music_Cog.all_players[guild_id]["voice connection"]
            song_info = interface.all_songs
            request = Music_Cog.play_previous(interface, voice_connection, song_info)
            if request is False:
                button.disabled = True 
                await interaction.response.defer()
            else: 
                self.children[1].label = "⏸️ Pause"
                await interaction.message.edit(embed = interface.player, view = interface)
                await interaction.response.defer()
       
    
        @discord.ui.button(label = "⏸️ Pause", style = discord.ButtonStyle.blurple)
        async def play_pause(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.pause_button = button
            voice_channel = interaction.user.voice.channel
            if voice_channel is not None:
                await interaction.response.defer()
                guild_id = voice_channel.guild.id
                voice_id = voice_channel.id
                if voice_id == Music_Cog.all_players[guild_id]["channel id"] and Music_Cog.all_players[guild_id]["voice connection"].is_playing():
                    Music_Cog.all_players[guild_id]["voice connection"].pause()
                    button.label = "▶️ Play"
                    await interaction.message.edit(embed = self.player, view = self)
                elif voice_id == Music_Cog.all_players[guild_id]["channel id"] and Music_Cog.all_players[guild_id]["voice connection"].is_paused():
                    Music_Cog.all_players[guild_id]["voice connection"].resume()
                    button.label = "⏸️ Pause"
                    await interaction.message.edit(embed = self.player, view = self)
                else:
                    private_message = "You have to be in the same channel with music bot to use this interface"
                    interaction.followup.send(content = private_message, ephemeral = True)
            else: 
                private_message = "You have to first join the same channel with music bot to use this interface"
                interaction.followup.send(content = private_message, ephemeral = True)

        
        @discord.ui.button(label = "⏭️ Next", style = discord.ButtonStyle.grey)
        async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
            button.disabled = False
            guild_id = interaction.guild_id
            interface = Music_Cog.all_players[guild_id]["interface"]
            voice_connection = Music_Cog.all_players[guild_id]["voice connection"]
            song_info = interface.all_songs
            
            request = Music_Cog.play_next(interface, voice_connection, song_info)
            if request is False:
                button.disabled = True 
                await interaction.response.defer()
            else:
                self.children[1].label = "⏸️ Pause"
                await interaction.message.edit(embed = interface.player, view = interface)
                await interaction.response.defer()

        
        @discord.ui.button(label = "🚫 Close", style = discord.ButtonStyle.red)
        async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
            voice_channel = interaction.user.voice.channel
            if voice_channel is not None:
                await interaction.response.defer()
                guild_id = voice_channel.guild.id
                voice_id = voice_channel.id
                
                if voice_id == Music_Cog.all_players[guild_id]["channel id"]:
                    Music_Cog.all_players[guild_id]["voice connection"].stop()
                    await interaction.message.delete()
                    await Music_Cog.all_players[guild_id]["voice connection"].disconnect()
                    del Music_Cog.all_players[guild_id]
                
                else:
                    private_message = "You have to be in the same channel with music bot to use this interface"
                    interaction.followup.send(content = private_message, ephemeral = True)
            
            else: 
                private_message = "You have to first join the same channel with music bot to use this interface"
                interaction.followup.send(content = private_message, ephemeral = True)

    
    def youtube_extractor(self, song_url):
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.sanitize_info(ydl.extract_info(song_url, download = False))
            url = info["url"]
            music_file = discord.FFmpegPCMAudio(url, executable = "ffmpeg/bin/ffmpeg.exe", **ffmpeg_options)
            title = info.get("fulltitle")
            channel = info.get("uploader")
            duration = info.get("duration_string")
            entry = f"Title: {title}\nChannel: {channel}\nDuration: {duration}\nURL: {song_url}\n\n"
            return {"music file": music_file, "title": title, "duration": duration, "info": entry}
        

    youtube_search_description = "Look for a song on Youtube for the bot to play"
    @app_commands.command(name = "search_youtube", description = youtube_search_description)
    @app_commands.describe(song_url = "Which song to play?")
    async def ytsearch(self, interaction: discord.Interaction, song_url: str):
        voice_channel = interaction.user.voice.channel
        voice_check = discord.utils.get(self.bot.voice_clients, guild = interaction.guild)
        guild_id = interaction.guild_id
        
        if voice_channel is not None and voice_check is None:
            await interaction.response.defer()
            local_interface = self.YoutubeInterface() 
            full_song_info = self.youtube_extractor(song_url)
            
            channel_id = voice_channel.id
            Music_Cog.all_players[guild_id] = {}
            Music_Cog.all_players[guild_id]["interface"] = local_interface
            Music_Cog.all_players[guild_id]["channel id"] = channel_id

            connection = await voice_channel.connect()
            connection.play(full_song_info["music file"])
            Music_Cog.all_players[guild_id]["voice connection"] = connection
            
            Music_Cog.embed_editor(local_interface, full_song_info)
            message = await interaction.followup.send(embed = local_interface.player, view = local_interface, file = local_interface.logo, wait = True)
            Music_Cog.all_players[guild_id]["message"] = message
        
        elif Music_Cog.all_players.get(guild_id, None) is not None and voice_channel.id == Music_Cog.all_players[guild_id]["channel id"]:
            full_song_info = self.youtube_extractor(song_url)
            local_interface = Music_Cog.all_players[guild_id]["interface"]
            
            
            edit_result = Music_Cog.embed_editor(local_interface, full_song_info)
            
            if edit_result is False:
                private_message = f"Couldn't add the song '{full_song_info['title']}' to the queue, since music player exceeds total character limit. "
                private_message += "Please wait a bit before adding a new song or restart the music player"
                await interaction.response.send_message(content = private_message, ephemeral = True, delete_after = 5)
            
            else:
                message = Music_Cog.all_players[guild_id]["message"]
                await message.edit(embed = local_interface.player, view = local_interface)
                private_message = f"Added the song '{full_song_info['title']}' to the queue"
                await interaction.response.send_message(content = private_message, ephemeral = True, delete_after = 2)
           
        else:
            private_message = "To use this command you have to be inside of a voice channel"
            await interaction.followup.send(content = private_message, ephemeral = True)

    



            