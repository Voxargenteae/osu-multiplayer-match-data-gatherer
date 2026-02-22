'''
Python/Ossapi owc score data scraper rewrite by Eduards "Voxargenteae" Zabarovskis
Version 0.1.0
Last updated 19.02.2026
'''
from ossapi import Ossapi
import csv
import requests
from rosu_pp_py import BeatmapAttributesBuilder, Beatmap, Performance
import rosu_pp_py as rosu
from typing import Optional, Dict, Any
from functools import lru_cache
from requests.exceptions import HTTPError
from matchIDsList import matchIDs

@lru_cache(maxsize=128)
def fetchOsuFile(map_id: int) -> str:
    
    #Cache .osu file downloads
    
    response = requests.get(f"https://catboy.best/osu/{map_id}")
    response.raise_for_status()
    return response.text

def main() -> None:
    client_id = CLIENT_ID
    client_secret = CLIENT_SECRET
    api = Ossapi(client_id, client_secret)
    
    scoreEntries = []
    totalMatchesProcessed = 0
    totalMapsProcessed = 0
    
    for matchID in matchIDs:
        firstEvent = api.match(matchID).first_event_id
        lastEvent = api.match(matchID).latest_event_id        
    

if __name__ == "__main__":
    main()