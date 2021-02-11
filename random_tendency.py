import requests, random

APIKey = "RGAPI-83541200-22a7-4baf-9469-c90dc1667f41"
region = "EUN1"
summonerName = "Siwuuuuus"
HEADERS = {
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://developer.riotgames.com",
    "X-Riot-Token": APIKey
}


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

print(request_players_ids('PLATINUM', 'II', 10000, 3))
