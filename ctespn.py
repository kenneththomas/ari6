import requests
import json
import time
import datetime

storage = {}
previous_payloads = []

class GameInfo:
    def __init__(self, id, team1, team2, last_play, team1_score, team2_score, time_qtr):
        self.id = id
        self.team1 = team1
        self.team2 = team2
        self.last_play = last_play
        self.team1_score = team1_score
        self.team2_score = team2_score
        self.time_qtr = time_qtr

def scoreboard_request():
    # Updated URL for NBA
    url = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
    else:
        print("Error: Unable to fetch data from the ESPN API")
        data = {}
    return data

def sb_parser(scoreboard_data):
    eventcount = len(scoreboard_data.get('events', []))
    for evc in range(eventcount):
        # Skip if the event is not live
        if scoreboard_data['events'][evc]['status']['type']['completed']:
            continue

        event = scoreboard_data['events'][evc]
        id = event['id']
        competition = event['competitions'][0]
        competitors = competition['competitors']
        team1 = competitors[0]['team']['location']
        team2 = competitors[1]['team']['location']
        sb_key = f'{id}_{team1}_{team2}'

        last_play = event.get('competitions')[0].get('situation', {}).get('lastPlay', {}).get('text', 'No last play available')
        team1_score = competitors[0]['score']
        team2_score = competitors[1]['score']
        time_qtr = event['status']['type']['detail']

        game_info = GameInfo(id, team1, team2, last_play, team1_score, team2_score, time_qtr)
        storage[sb_key] = game_info

def info_printer(gio):
    info = f'{gio.team1} {gio.team1_score} - {gio.team2} {gio.team2_score} | {gio.last_play}'
    if info in previous_payloads:
        return info

    print(f'''
    {gio.team1} {gio.team1_score} - {gio.team2} {gio.team2_score}
    {gio.time_qtr}
    {gio.last_play}
    ''')
    previous_payloads.append(info)
    return info