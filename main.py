'''
Python/Ossapi owc score data scraper rewrite by Eduards "Voxargenteae" Zabarovskis
Version 0.2.2
Last updated 27.02.2026
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
def log_progress(message) -> None:
    timestamp_format = "%Y-%h-%d-%H:%M:%S"
    now = datetime.now()
    timestamp = now.strftime(timestamp_format)
    with open("./owc_data_project_log.txt", "a") as f:
        f.write(timestamp + " : " + message + "\n")

#gets the MatchGame events from the mp match
def get_map_rounds(match_id: int, api) -> list:
    firstEvent = api.match(match_id).first_event_id
    lastEvent = api.match(match_id).latest_event_id
    currentEvent = firstEvent
    response = api.match(match_id, after_id = currentEvent)
    matchEvents = response.events
    mapRounds = []
    while currentEvent < lastEvent:                                             # This loop circumvents the 100 game event limit
        response = api.match(match_id, after_id = currentEvent)
        matchEvents = response.events
        for matchEvent in matchEvents:                                          # filter out non-game events
            if matchEvent.game != None:
                mapRounds.append(matchEvent.game)
            currentEvent = matchEvent.id
    return mapRounds

#gets mods used in the score
def get_score_mods(map_score) -> str:
    mapModsList = map_score.mods
    mapModsString = ""
    for mod in mapModsList:
        if mod.acronym != "NF":
            mapModsString += str(mod.acronym)
    if mapModsString == "":
        mapModsString = "NM"
    return mapModsString

#gets beatmap attributes for map difficulty stat calculation
def get_beatmap_attributes(map_score):
    mapModsList = map_score.mods
    osu_content = fetchOsuFile(map_score.beatmap_id)
    beatmap = rosu.Beatmap(content=osu_content)
    perf = Performance(lazer = False)
    perf.set_mods(mods = [{"acronym": mod.acronym} for mod in mapModsList])
    mapAttr = BeatmapAttributesBuilder(mods = [{"acronym": mod.acronym} for mod in mapModsList])
    mapAttr.set_map(beatmap)
    attrs = mapAttr.build()
    calcResult = perf.calculate(beatmap)
    return calcResult

def get_score_entry(mapModsString, mapScore, matchID, api) -> dict:
            try:
                beatmapAttribs = get_beatmap_attributes(mapScore)
                mapDrain = api.beatmap(beatmap_id = mapScore.beatmap_id).hit_length
                mapBPM = api.beatmap(beatmap_id = mapScore.beatmap_id).bpm
                mapCS = api.beatmap(beatmap_id = mapScore.beatmap_id).cs
                mapOD = api.beatmap(beatmap_id = mapScore.beatmap_id).accuracy
            
                if mapModsString.find("HR") != -1:
                    mapCS *= 1.3
                    mapOD *= 1.4
                    if mapCS > 10:
                        mapCS = 10
                    if mapOD > 10:
                        mapOD = 10
                if mapModsString.find("EZ") != -1:
                    mapCS *= 0.5
                    mapOD *= 0.5
                if mapModsString.find("DT") != -1 or mapModsString.find("NC") != -1:
                    mapDrain = int(mapDrain / 1.5)
                    mapBPM *= 1.5
                elif mapModsString.find("HT") != -1:
                    mapDrain = int(mapDrain / 0.75)
                    mapBPM *= 0.75
                try:
                    scoreEntry = {                                                      # entry dict
                "matchID": matchID,
                "beatmapID": mapScore.beatmap_id,
                "beatmapBPM": "{:.1f}".format(mapBPM),
                "beatmapCS": "{:.1f}".format(mapCS),
                "beatmapHP": "{:.1f}".format(beatmapAttribs.difficulty.hp),
                "beatmapOD": "{:.1f}".format(mapOD),
                "beatmapAR": "{:.1f}".format(beatmapAttribs.difficulty.ar),
                "beatmapSR": "{:.2f}".format(beatmapAttribs.difficulty.stars),
                "beatmapDrainTime": mapDrain,
                "beatmapMaxCombo": api.beatmap(beatmap_id = mapScore.beatmap_id).max_combo,
                "playerID": mapScore.user_id,
                "playerUsername": api.user(mapScore.user_id).username,
                "playerCountry": api.user(mapScore.user_id).country.name,
                "playerTeamColour": mapScore.match.team,
                "playerMods": mapModsString,
                "playerScore": mapScore.total_score,
                "playerAccuracy": "{:.2f}".format(mapScore.accuracy*100),
                "playerGrade": str(mapScore.rank).replace("Grade.", ""),
                "playerMaxCombo": mapScore.max_combo,
                "count100": mapScore.statistics.ok,
                "count50": mapScore.statistics.meh,
                "countMiss": mapScore.statistics.miss,
                "scoreDate": str(mapScore.ended_at).replace("+00:00", "")
                }
                except ValueError:
                    scoreEntry = {                                                      # entry dict if deleted user
                "matchID": matchID,
                "beatmapID": mapScore.beatmap_id,
                "beatmapBPM": "{:.1f}".format(mapBPM),
                "beatmapCS": "{:.1f}".format(mapCS),
                "beatmapHP": "{:.1f}".format(beatmapAttribs.difficulty.hp),
                "beatmapOD": "{:.1f}".format(mapOD),
                "beatmapAR": "{:.1f}".format(beatmapAttribs.difficulty.ar),
                "beatmapSR": "{:.2f}".format(beatmapAttribs.difficulty.stars),
                "beatmapDrainTime": mapDrain,
                "beatmapMaxCombo": api.beatmap(beatmap_id = mapScore.beatmap_id).max_combo,
                "playerID": "NULL",
                "playerUsername": "NULL",
                "playerCountry": "NULL",
                "playerTeamColour": mapScore.match.team,
                "playerMods": mapModsString,
                "playerScore": mapScore.total_score,
                "playerAccuracy": "{:.2f}".format(mapScore.accuracy*100),
                "playerGrade": str(mapScore.rank).replace("Grade.", ""),
                "playerMaxCombo": mapScore.max_combo,
                "count100": mapScore.statistics.ok,
                "count50": mapScore.statistics.meh,
                "countMiss": mapScore.statistics.miss,
                "scoreDate": str(mapScore.ended_at).replace("+00:00", "")
                }
            except (ValueError, HTTPError):
                beatmapAttribs = get_beatmap_attributes(mapScore)
                mapDrain = api.beatmap(beatmap_id = mapScore.beatmap_id).hit_length
                mapBPM = api.beatmap(beatmap_id = mapScore.beatmap_id).bpm
                mapCS = api.beatmap(beatmap_id = mapScore.beatmap_id).cs
                mapOD = api.beatmap(beatmap_id = mapScore.beatmap_id).accuracy
            
                if mapModsString.find("HR") != -1:
                    mapCS *= 1.3
                    mapOD *= 1.4
                    if mapCS > 10:
                        mapCS = 10
                    if mapOD > 10:
                        mapOD = 10
                if mapModsString.find("EZ") != -1:
                    mapCS *= 0.5
                    mapOD *= 0.5
                if mapModsString.find("DT") != -1 or mapModsString.find("NC") != -1:
                    mapDrain = int(mapDrain / 1.5)
                    mapBPM *= 1.5
                elif mapModsString.find("HT") != -1:
                    mapDrain = int(mapDrain / 0.75)
                    mapBPM *= 0.75
                try:
                    scoreEntry = {                                                      # entry dict if deleted map
                "matchID": matchID,
                "beatmapID": "NULL",
                "beatmapBPM": "NULL",
                "beatmapCS": "NULL",
                "beatmapHP": "NULL",
                "beatmapOD": "NULL",
                "beatmapAR": "NULL",
                "beatmapSR": "NULL",
                "beatmapDrainTime": "NULL",
                "beatmapMaxCombo": "NULL",
                "playerID": mapScore.user_id,
                "playerUsername": api.user(mapScore.user_id).username,
                "playerCountry": api.user(mapScore.user_id).country.name,
                "playerTeamColour": mapScore.match.team,
                "playerMods": mapModsString,
                "playerScore": mapScore.total_score,
                "playerAccuracy": "{:.2f}".format(mapScore.accuracy*100),
                "playerGrade": str(mapScore.rank).replace("Grade.", ""),
                "playerMaxCombo": mapScore.max_combo,
                "count100": mapScore.statistics.ok,
                "count50": mapScore.statistics.meh,
                "countMiss": mapScore.statistics.miss,
                "scoreDate": str(mapScore.ended_at).replace("+00:00", "")
                }
                except ValueError:
                    scoreEntry = {                                                      # entry dict if deleted user and map
                "matchID": matchID,
                "beatmapID": "NULL",
                "beatmapBPM": "NULL",
                "beatmapCS": "NULL",
                "beatmapHP": "NULL",
                "beatmapOD": "NULL",
                "beatmapAR": "NULL",
                "beatmapSR": "NULL",
                "beatmapDrainTime": "NULL",
                "beatmapMaxCombo": "NULL",
                "playerID": "NULL",
                "playerUsername": "NULL",
                "playerCountry": "NULL",
                "playerTeamColour": mapScore.match.team,
                "playerMods": mapModsString,
                "playerScore": mapScore.total_score,
                "playerAccuracy": "{:.2f}".format(mapScore.accuracy*100),
                "playerGrade": str(mapScore.rank).replace("Grade.", ""),
                "playerMaxCombo": mapScore.max_combo,
                "count100": mapScore.statistics.ok,
                "count50": mapScore.statistics.meh,
                "countMiss": mapScore.statistics.miss,
                "scoreDate": str(mapScore.ended_at).replace("+00:00", "")
                }
            except:
                scoreEntry = {}
            return scoreEntry

def write_to_csv(scoreEntries: dict) -> None:
    filename = "scoreTable.csv"
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["matchID",
                                                  "beatmapID",
                                                  "beatmapBPM",
                                                  "beatmapCS",
                                                  "beatmapHP",
                                                  "beatmapOD",
                                                  "beatmapAR",
                                                  "beatmapSR",
                                                  "beatmapDrainTime",
                                                  "beatmapMaxCombo",
                                                  "playerID",
                                                  "playerUsername",
                                                  "playerCountry",
                                                  "playerTeamColour",
                                                  "playerMods",
                                                  "playerScore",
                                                  "playerAccuracy",
                                                  "playerGrade",
                                                  "playerMaxCombo",
                                                  "count100",
                                                  "count50",
                                                  "countMiss",
                                                  "scoreDate"])
        writer.writeheader()
        for b in scoreEntries:
            writer.writerow(b)    

def main() -> None:
    client_id = CLIENT_ID
    client_secret = CLIENT_SECRET
    api = Ossapi(client_id, client_secret)
    
    scoreEntries = []
    totalMatchesProcessed = 0
    totalMapsProcessed = 0
    
    log_progress("Preliminaries complete. Initiating ETL process")
    
    for matchID in matchIDs:
        mapRounds = get_map_rounds(matchID, api)
        for mapRound in mapRounds:
            mapScores = mapRound.scores
            for mapScore in mapScores:
                mapScoreMods = get_score_mods(mapScore)
                mapScoreEntry = get_score_entry(mapScoreMods, mapScore, matchID, api)
                scoreEntries.append(mapScoreEntry)
            totalMapsProcessed += 1
            print("Total maps currently processed: ", totalMapsProcessed)
        log_progress(str("Match " + str(matchID) + " processed"))
        totalMatchesProcessed += 1
        print("Total matches currently processed: ", totalMatchesProcessed)
        
    
                
    log_progress("Data extraction complete. Initiating loading process")
    
    write_to_csv(scoreEntries)
    
    log_progress("Data saved to CSV file")
            
    

if __name__ == "__main__":
    main()