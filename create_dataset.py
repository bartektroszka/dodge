import requests, random
import pandas as pd
import roleml
from csv import writer
from ratelimit import limits, sleep_and_retry

APIKey = "RGAPI-10d5222d-4653-4d28-bd8b-629515e09630"
region = "EUN1"
version = "11.4.1"
HEADERS = {
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://developer.riotgames.com",
    "X-Riot-Token": APIKey
}

@sleep_and_retry
@limits(calls=20, period=24)
def call_api(url, headers = None):
    response = requests.get(url = url, headers = headers)

    if response.status_code != 200:
        print(response.status_code)
        return None
    return response

def get_champion_from_id(champion_id):
    champion_id = str(champion_id)
    url = f"http://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json"
    response = call_api(url)
    if not response:
        return None
    champion_list = response.json()['data']
    champion_name = ""
    for champ in champion_list:
        if champion_list[champ]['key'] == champion_id:
            champion_name += champ
            break
    return champion_name

def request_players_ids(tier, division, max_num, chosen_num, queue = 'RANKED_SOLO_5x5'):
    left = max_num
    page_counter = 1
    all_ids = []
    while left > 0:
        URL = f'https://{region}.api.riotgames.com/lol/league/v4/entries/{queue}/{tier}/{division}?page={page_counter}'
        response = call_api(url=URL, headers = HEADERS)
        if not response:
            return None
        response = response.json()
        response_list = filter((lambda x: not x['inactive']), response)
        ids = [player['summonerId'] for player in response]
        all_ids += ids
        left -= len(response)
        page_counter += 1
    return random.sample(all_ids, chosen_num)

def request_match_history(player_id, chosen_num):   
    acc_URL = f'https://{region}.api.riotgames.com/lol/summoner/v4/summoners/{player_id}'
    acc_response = call_api(url=acc_URL, headers = HEADERS)
    if not acc_response:
        return None
    try:
        account_id = acc_response.json()['accountId']
        #420 because it is ranked SOLO 5v5
        URL = f'https://{region}.api.riotgames.com/lol/match/v4/matchlists/by-account/{account_id}?queue=420'
        response = call_api(url=URL, headers = HEADERS).json()
        if not response:
            return None, None
        try:
            match_list = response['matches'] # key error
        except KeyError:
            return None, None
        match_ids = [m['gameId'] for m in match_list]
        return random.sample(match_ids, chosen_num)
    except KeyError:
        return None, None

def request_match_data(match_id):
    URL_match = f'https://{region}.api.riotgames.com/lol/match/v4/matches/{match_id}'
    URL_timeline = f'https://{region}.api.riotgames.com/lol/match/v4/timelines/by-match/{match_id}'
    timeline_response = call_api(url=URL_timeline,headers = HEADERS)
    match_response = call_api(url=URL_match, headers = HEADERS)
    if not timeline_response or not match_response:
        return None
    try:
        match = match_response.json()
        timeline = timeline_response.json()
        accurateRoles = bool(timeline and match['gameDuration'] > 720)  ## Flagging if accurate roles are available
    except KeyError:
        accurateRoles = False

    if accurateRoles:
        participants_roles = roleml.predict(match, timeline)
        

    try:
        participants = match['participants'] # key error
        teams = match['teams']
        team_1 = []
        team_2 = []
        won = 0
        for player in participants:
            if player['teamId'] == 100:
                if accurateRoles:
                    team_1.append([get_champion_from_id(player['championId']), participants_roles[player['participantId']]])
                else:
                    team_1.append([get_champion_from_id(player['championId']), player['timeline']['lane']])
            elif player['teamId'] == 200:
                if accurateRoles:
                    team_2.append([get_champion_from_id(player['championId']), participants_roles[player['participantId']]])
                else:
                    team_2.append([get_champion_from_id(player['championId']), player['timeline']['lane']])

            if(teams[0]["teamId"]== 100):
                if(teams[0]['win']=='Win'):
                    won = 1
                else:
                    won = 2
            elif(teams[0]["teamId"]== 200):
                if(teams[0]['win']=='Win'):
                    won = 2
                else:
                    won = 1
        return [team_1, team_2, won]
    except KeyError:
        return None

def convert_data_to_csv(data): #data [[game], [game]] where game is [team1, team2, won]
    with open("data.csv", 'w+', newline='') as write_obj:
        csv_writer = writer(write_obj)
        csv_writer.writerow(['top1','jungle1', 'mid1', 'bot1', 'supp1', 'top2', 'jungle2', 'mid2', 'bot2', 'supp2', 'won'])
        for game in data:
            role_dict = {"top1" : 0,
            "jungle1": 0,
            "mid1": 0,
            "bot1": 0,
            "supp1": 0,
            "top2": 0,
            "jungle2": 0,
            "mid2": 0,
            "bot2": 0,
            "supp2":  0
            }
            # Create a writer object from csv module
            # Add contents of list as last row in the csv file
            team1 = game[0]
            team2 = game[1]
            won = game[2]
            for role in ['top', 'jungle', 'mid', 'bot', 'supp']:
                for player in team1:
                    if player[1] == role:
                        role_dict[role+"1"] = player[0]
                for player in team2:
                    if player[1] == role:
                        role_dict[role+"2"] = player[0]
            if not 0 in role_dict.values():
                csv_writer.writerow([role_dict["top1"], role_dict["jungle1"], role_dict["mid1"], role_dict["bot1"], role_dict["supp1"], role_dict["top2"], role_dict["jungle2"], role_dict["mid2"], role_dict["bot2"], role_dict["supp2"], won])


dataframe = []
player_ids = request_players_ids("GOLD", "III", 5000, 30, queue = 'RANKED_SOLO_5x5')
for player_id in player_ids:
    match_ids = request_match_history(player_id, 10)
    for match in match_ids:
        data = request_match_data(match)
        if(data):
            dataframe.append(data)

convert_data_to_csv(dataframe)