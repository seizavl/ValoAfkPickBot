# IngameValorant.py
import requests

class Valorant:
    def __init__(self,client,agents_data):
        self.client = client
        self.client.activate()
        self.agents_data = agents_data
        self.now_select_agent = None  
        
    def select_agent(self, select_agent):
        self.client.pregame_select_character(self.agents_data["agents"].get(select_agent, {}).get("id"))
        self.now_select_agent = select_agent

    def pick_agent(self):
        if self.now_select_agent is not None:
            self.client.pregame_lock_character(self.agents_data["agents"].get(self.now_select_agent, {}).get("id"))

    def get_player(self):
        data = self.client.pregame_fetch_match()
        players_info = []
        
        for team in data.get("Teams", []):
            for player in team.get("Players", []):
                character_id = player.get("CharacterID", "")
                character_selection_state = player.get("CharacterSelectionState", "")
                character_name = next((name for name, info in self.agents_data["agents"].items() if info["id"] == character_id), None)
                character_emoji = self.agents_data["agents"].get(character_name, {}).get("emoji")

                players_info.append([character_emoji,character_selection_state])

        return players_info
    
    def get_map(self):
        data = self.client.pregame_fetch_match()
        MapID = data.get("MapID", "")

        url = 'https://valorant-api.com/v1/maps'
        response = requests.get(url)
        mapdata = response.json()
        display_name = None
        
        for map_info in mapdata['data']:
            if map_info['mapUrl'] == MapID:
                display_name = map_info['displayName']
                return display_name