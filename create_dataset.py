import requests, random
import pandas as pd
import roleml

APIKey = "RGAPI-c34aadca-9d3a-40f8-bbb4-115c2b3de82f"
region = "EUN1"
version = "11.4.1"
HEADERS = {
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://developer.riotgames.com",
    "X-Riot-Token": APIKey
}


def get_champion_from_id(champion_id):
    champion_id = str(champion_id)
    url = f"http://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json"
    response = requests.get(url)
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
        response = requests.get(url=URL, headers = HEADERS)
        if response is None:
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
    acc_response = requests.get(url=acc_URL, headers = HEADERS)
    if acc_response is None:
        return None
    try:
        account_id = acc_response.json()['accountId']
        #420 because it is ranked SOLO 5v5
        URL = f'https://{region}.api.riotgames.com/lol/match/v4/matchlists/by-account/{account_id}?queue=420'
        response = requests.get(url=URL, headers = HEADERS).json()
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

    timeline = requests.get(url=URL_timeline,headers = HEADERS).json()
    match = requests.get(url=URL_match, headers = HEADERS).json()
    try:
        accurateRoles = bool(timeline and match['gameDuration'] > 720) ## Flagging if accurate roles are available
    except KeyError:
            print(":(")
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
                    team_2.append(
                        [get_champion_from_id(player['championId']), player['timeline']['lane']])

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

dataframe = []
player_ids = request_players_ids("GOLD", "III", 2000, 15, queue = 'RANKED_SOLO_5x5')
for player_id in player_ids:
    match_ids = request_match_history(player_id, 8)
    for match in match_ids:
        data = request_match_data(match)
        if(data):
            dataframe.append(data)
print(dataframe)