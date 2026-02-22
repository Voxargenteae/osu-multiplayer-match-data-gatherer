'''
Python/Ossapi owc score data scraper rewrite by Eduards "Voxargenteae" Zabarovskis
Version 0.1.1
Last updated 23.02.2026
'''
from ossapi import Ossapi
import csv
import requests
from datetime import datetime
from rosu_pp_py import BeatmapAttributesBuilder, Beatmap, Performance
import rosu_pp_py as rosu
from typing import Optional, Dict, Any
from functools import lru_cache
from requests.exceptions import HTTPError
from matchIDsList import matchIDs
from APIDetails import CLIENT_ID, CLIENT_SECRET

@lru_cache(maxsize=128)
def fetchOsuFile(map_id: int) -> str:
    
    #Cache .osu file downloads
    
    response = requests.get(f"https://catboy.best/osu/{map_id}")
    response.raise_for_status()
    return response.text

#logger func
def log_progress(message):
    timestamp_format = "%Y-%h-%d-%H:%M:%S"
    now = datetime.now()
    timestamp = now.strftime(timestamp_format)
    with open("./owc_data_project_log.txt", "a") as f:
        f.write(timestamp + " : " + message + "\n")

#gets the MatchGame events from the mp match
def get_map_rounds(match_id: int) -> list:
    firstEvent = api.match(matchID).first_event_id
    lastEvent = api.match(matchID).latest_event_id
    currentEvent = firstEvent
    response = api.match(matchID, after_id = currentEvent)
    matchEvents = response.events
    mapRounds = []
    while currentEvent < lastEvent:                                             # This loop circumvents the 100 game event limit
        response = api.match(matchID, after_id = currentEvent)
        matchEvents = response.events
        for matchEvent in matchEvents:                                          # filter out non-game events
            if matchEvent.game != None:
                mapRounds.append(matchEvent.game)
            currentEvent = matchEvent.id
    return mapRounds

#gets mods used in the score
def get_score_mods(map_score: Score) -> str:
    mapModsList = map_score.mods
    mapModsString = ""
    for mod in mapModsList:
        if mod.acronym != "NF":
            mapModsString += str(mod.acronym)
    if mapModsString == "":
        mapModsString = "NM"
    return mapModsString

#gets beatmap attributes for map difficulty stat calculation
def get_beatmap_attributes(map_score: Score, map_mods_list: list) -> Performance:
    osu_content = fetchOsuFile(mapScore.beatmap_id)
    beatmap = rosu.Beatmap(content=osu_content)
    perf = Performance(lazer = False)
    perf.set_mods(mods = [{"acronym": mod.acronym} for mod in mapModsList])
    mapAttr = BeatmapAttributesBuilder(mods = [{"acronym": mod.acronym} for mod in mapModsList])
    mapAttr.set_map(beatmap)
    attrs = mapAttr.build()
    calcResult = perf.calculate(beatmap)
    return calcResult

def main() -> None:
    client_id = CLIENT_ID
    client_secret = CLIENT_SECRET
    api = Ossapi(client_id, client_secret)
    
    scoreEntries = []
    totalMatchesProcessed = 0
    totalMapsProcessed = 0
    
    log_progress("Preliminaries complete. Initiating ETL process")
    
    for matchID in matchIDs[:1]:
        mapRounds = get_map_rounds(matchID)
        for mapRound in mapRounds:
            mapScores = mapRound.scores
            for mapScore in mapScores:
                mapScoreMods = get_score_mods(mapScore)
                
            
    

if __name__ == "__main__":
    main()