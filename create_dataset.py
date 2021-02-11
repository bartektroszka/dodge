import requests, random

APIKey = "RGAPI-83541200-22a7-4baf-9469-c90dc1667f41"
region = "EUN1"
HEADERS = {
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://developer.riotgames.com",
    "X-Riot-Token": APIKey
}

def get_champion_from_id(champion_id):
    pass
def request_players_ids(tier, division, max_num, chosen_num, queue = 'RANKED_SOLO_5x5'):
    left = max_num
    page_counter = 1
    ids = []
    while left > 0:
        URL = f'https://{region}.api.riotgames.com/lol/league/v4/entries/{queue}/{tier}/{division}?page={page_counter}'
        response = requests.get(url=URL, headers = HEADERS)
        if response is None:
            return None
        response = response.json()
        response_list = filter((lambda x: not x['inactive']), response)
        ids = [player['summonerId'] for player in response]
        left -= len(response)
        page_counter += 1
    return random.sample(ids, chosen_num)

def request_match_history(player_id, chosen_num):   
    acc_URL = f'https://{region}.api.riotgames.com/lol/summoner/v4/summoners/{player_id}'
    acc_response = requests.get(url=acc_URL, headers = HEADERS)
    if acc_response is None:
        return None
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

def request_match_champions(match_id):
    URL = f'https://{region}.api.riotgames.com/lol/match/v4/matches/{match_id}'
    response = requests.get(url=URL, headers = HEADERS).json()
    for player in response['participants']:
        print(player['timeline']['lane'])
        print(player['championId'])
        print(player['teamId'])
        print()

request_match_champions("2698988077")