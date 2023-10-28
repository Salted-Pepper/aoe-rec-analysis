from mgz.model import parse_match, serialize
import copy
import pandas as pd
from players import Player

unique_match_id = 0


def load_replay_data(replay_path: str) -> dict:
    with open(replay_path, 'rb') as m:
        match = parse_match(m)
        return serialize(match)


def extract_data(match_data: dict, list_of_actions: list) -> list:
    """
    :param match_data: dict containing parsed match data
    :param list_of_actions: list of actions that need to be saved
    :return:
    """
    global unique_match_id
    unique_match_id += 1
    print(f"\n\nExtracting data from match {unique_match_id}.")

    players = []

    map_name = match_data['map']['name']
    duration = match_data['duration']

    for player in match_data['players']:
        try:
            players.append(Player(name=player['name'], civ=player['civilization'], colour=player['number']))
        except TypeError as e:
            print(f"player dict is {player} \n")
            print(f"Skipping incorrect replay -- {e}")
            return []
    actions = match_data['actions']
    action_data = []

    for action in actions:

        get_age_up_time(action, players)

        if action['type'] not in list_of_actions:
            continue
        action['map'] = map_name
        action['duration'] = duration
        action['match_id'] = unique_match_id
        action['players'] = [p.name for p in players]
        action['civs'] = [p.civ for p in players]
        action['action'] = action['type']
        action['player'] = players[action['player'] - 1].name

        if action['type'] in list_of_actions:
            if action['type'] == "DE_QUEUE":
                try:
                    action['value'] = action["payload"]["unit"]
                except KeyError:
                    action['value'] = None
            elif action['type'] == "RESEARCH":
                try:
                    action['value'] = action['payload']['technology']
                except KeyError:
                    # print("RESEARCH contains no key 'technology', keys: ", action['payload'].keys())
                    pass
            elif action['type'] == "SPECIAL":
                try:
                    action['value'] = action['payload']['order']
                except KeyError:
                    # print("SPECIAL contains no key 'order', keys: ", action['payload'].keys())
                    pass
            elif action['type'] == "BUILD":
                action['value'] = action['payload']['building']
            elif action['type'] == "FORMATION":
                action['value'] = action['payload']['formation']
        action_data.append(action)

    for action in action_data:
        for index, player in enumerate(players):
            action[f'p_{index+1}_feudal_time'] = player.feudal_time
            action[f'p_{index+1}_castle_time'] = player.castle_time
            action[f'p_{index+1}_imp_time'] = player.imp_time

    return action_data


def make_data_from_replays(replays: list, list_of_actions: list) -> pd.DataFrame:
    """
    :replays: List of names (strings) of replay files
    :action: List of actions (strings)
    Possible actions: ['ORDER', 'DELETE', 'GATHER_POINT', 'BUY', 'WALL', 'STANCE', 'BUILD', 'MOVE',
    'RESEARCH', 'ATTACK_GROUND', 'STOP', 'GAME', 'FORMATION', 'BACK_TO_WORK', 'RESIGN', 'SPECIAL',
    'SELL', 'REPAIR', 'PATROL', 'UNGARRISON', 'DE_ATTACK_MOVE', 'DE_QUEUE']
    """
    dict_list = []
    for replay in replays:
        dict_list.extend(extract_data(match_data=load_replay_data(replay), list_of_actions=list_of_actions))
    data = pd.DataFrame.from_dict(dict_list)
    set_end_age(data)
    return data


def get_age_up_time(action, players) -> None:
    # Get age uptime
    if action['type'] == 'RESEARCH':
        try:
            tech = action['payload']['technology']
        except KeyError:
            return
        if tech == "Feudal Age":
            player = players[action['player']-1]
            player.feudal_time = action['timestamp']
        elif tech == "Castle Age":
            player = players[action['player'] - 1]
            player.castle_time = action['timestamp']
        elif tech == "Imperial Age":
            player = players[action['player'] - 1]
            player.imp_time = action['timestamp']


def set_end_age(df):
    df['end_age'] = None

    for match_id in df['match_id'].unique():
        row = df[df['match_id'] == match_id].iloc[0]
        imp_times = [c for c in df.columns if "imp" in c]
        castle_times = [c for c in df.columns if "castle" in c]
        feudal_times = [c for c in df.columns if "feudal" in c]

        if any(time is not None for time in row[imp_times]):
            match_ends = "imperial"
        elif any(time is not None for time in row[castle_times]):
            match_ends = "castle"
        elif any(time is not None for time in row[feudal_times]):
            match_ends = "feudal"
        else:
            match_ends = "dark"

        df.loc[df["match_id"] == match_id, ['end_age']] = match_ends
