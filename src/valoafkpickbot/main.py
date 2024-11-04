# main.py
from discord.ext import commands
from discord.ui import Select, Button, View
import discord
import json
from valclient.client import Client
import asyncio
from dotenv import load_dotenv
import os
from valoafkpickbot.IngameValorant import Valorant

class ValoAfkPickBot(commands.Bot):
    def __init__(self, token, channel_id, region):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        self.token = token
        self.channel_id = channel_id
        self.region = region
        self.valorant_client = None
        self.agents_data = self.load_agents()

    def load_agents(self):
        with open('data.json', 'r') as f:
            return json.load(f)
    
    async def on_ready(self):
        await self.initialize_valorant_client()
    
    async def initialize_valorant_client(self):
        try:
            self.valorant_client = Client(region=self.region)
            self.valorant_client.activate()
            embed = discord.Embed(title="ValoAfkPickBot", description="Valorantクライアントが正常に起動しています", color=0x00ff00)
            embed_message = await self.get_channel(self.channel_id).send(embed=embed)
            if await self.wait_for_agent_select(embed_message):
                await self.display_agent_selection(embed_message)

        except Exception as e:
            error_embed = discord.Embed(title="Bot起動エラー", description=f"エラー: {e}", color=0xff0000)
            await self.get_channel(self.channel_id).send(embed=error_embed)
            await embed_message.delete()
            await self.close()
    
    async def wait_for_agent_select(self, embed_message):
        cnt = 10
        while True:
            try:
                if self.valorant_client.fetch_presence(self.valorant_client.puuid)['sessionLoopState'] == "PREGAME":
                    while cnt > 0 :
                        embed = discord.Embed(title="マッチ中", description=f"マッチが見つかりました。あと{cnt}秒後にエージェント選択画面に移動します。", color=0xffff00)
                        await embed_message.edit(embed=embed)
                        cnt -= 1
                        await asyncio.sleep(1)
                    return True
            except Exception as e:
                print(f"エラー: {e}")
                await embed_message.delete()
                await self.close()
            await asyncio.sleep(1)
    
    async def display_agent_selection(self, embed_message):
        valorant = Valorant(self.valorant_client, self.agents_data)
        select = Select(placeholder="エージェントを選択してください", options=[
            discord.SelectOption(label=name, value=name) for name in list(self.agents_data["agents"].keys())[:25]
        ])
        selected_agent = None

        async def select_callback(interaction):
            nonlocal selected_agent
            selected_agent = select.values[0]
            await interaction.response.defer()
            valorant.select_agent(selected_agent)
            select.options = [discord.SelectOption(label=name, value=name, default=(name == selected_agent)) 
                               for name in list(self.agents_data["agents"].keys())[:25]]
            
            await embed_message.edit(view=view)

        async def button_callback(interaction):
            await interaction.response.defer()
            valorant.pick_agent()
            await embed_message.delete()
            await self.close()

        button = Button(label="決定", style=discord.ButtonStyle.green)
        button.callback = button_callback
        select.callback = select_callback
        view = View()
        view.add_item(select)
        view.add_item(button)
        await embed_message.edit(embed=discord.Embed(title="エージェント選択", description="エージェントを選んで「決定」を押してください", color=0x00ff00), view=view)
        asyncio.create_task(self.update_player_info(embed_message, valorant))

    async def update_player_info(self, embed_message, valorant):
        map_name = valorant.get_map()
        while not self.is_closed():
            try:
                session_state = self.valorant_client.fetch_presence(self.valorant_client.puuid)['sessionLoopState']
                if session_state == "PREGAME":
                    players_info = valorant.get_player()
                    embed = discord.Embed(title=map_name, color=0x00ff00)
                    for player in players_info:
                        if len(player) == 2:
                            character_emoji, character_selection_state = player
                            if character_emoji is None:
                                character_emoji = ":question:"
                                character_selection_state = "none"
                            embed.add_field(name=f"{character_emoji}: {character_selection_state}", value="", inline=False)

                    await embed_message.edit(embed=embed)
                    await asyncio.sleep(1)
                else:
                    await embed_message.delete()
                    await self.close()
                    break
            except asyncio.CancelledError:
                break
            except RuntimeError as e:
                if "Session is closed" in str(e):
                    break
                else:
                    await embed_message.delete()
                    await self.close()
                    break
    
    def run_bot(self):
        self.run(self.token)

    def get_emoji(self):

        """
        get agent icon 
        "https://emoji.gg/pack/34229-valorant-agents"
        """
        for emoji in self.bot.emojis:
            print(f'<:{emoji.name}:{emoji.id}>')

if __name__ == "__main__":
    load_dotenv()

    TOKEN       = os.getenv("TOKEN")
    CHANNEL_ID  = os.getenv("CHANNEL_ID")
    REGION      = os.getenv("REGION") 
    bot = ValoAfkPickBot(token=TOKEN, channel_id=CHANNEL_ID, region=REGION)

    bot.run_bot()
