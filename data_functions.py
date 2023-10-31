import matplotlib.pyplot as plt
import numpy as np
from mgz.model import parse_match, serialize
import pandas as pd
import datetime

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

    unique_match_id += 1
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

    time_columns = [c for c in data.columns if "time" in c]
    for col in time_columns:
        data[col] = data[col].astype('str').str.split(".").str[0]
        data[col] = pd.to_timedelta(data[col])
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

        df.loc[df['match_id'] == match_id, ['end_age']] = match_ends


def fetch_latest_time(df: pd.DataFrame, age: str):
    age_columns = [c for c in df.columns if age in c]
    max_time = df[age_columns].max(axis=1).max(axis=0)

    return max_time


def create_figure_grid_for_maps(maps: list) -> (plt.Figure, plt.Axes, int, int):
    grid_size = int(np.ceil(np.sqrt(len(maps))))

    if grid_size * (grid_size - 1) >= len(maps):
        fig, axes = plt.subplots(grid_size, grid_size - 1, figsize=(8, 8))
        max_rows = grid_size - 1
    else:
        fig, axes = plt.subplots(grid_size, grid_size, figsize=(8, 8))
        max_rows = grid_size
    return fig, axes, grid_size, max_rows


def calc_items_made_per_match(item: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates a dataframe with information on how many times each building has been made per map per player
    :param item:
    :param df:
    :return: dataframe
    """
    df_building = df[df["value"] == item]
    data_by_map = df_building.groupby(["map", "match_id", "player"])["value"].count().reset_index()

    entries_to_append = []

    for i in range(max(df['match_id']) + 1):
        entries = len(data_by_map[data_by_map['match_id'] == i])
        try:
            players = df[df['match_id'] == i].reset_index().iloc[0]['players']
        except IndexError:

            raise IndexError(df[df['match_id'] == i].reset_index(), i)
        if entries == len(players):
            continue
        else:
            worldmap = df[df['match_id'] == i].reset_index().iloc[0]['map']
            for player in players:
                if player not in data_by_map['player']:
                    entries_to_append.append({'map': worldmap,
                                              'match_id': i,
                                              'player': player,
                                              'value': 0})

    data_to_append = pd.DataFrame(entries_to_append)

    return pd.concat([data_by_map, data_to_append])


def make_minutes_out_of_time(times: list) -> list:
    new_times = []
    for index, time in enumerate(times):
        if isinstance(time, pd.Timestamp):
            new_times.append(time.minute + time.hour * 60 + time.second / 60)
        elif isinstance(time, datetime.timedelta):
            new_times.append(time.total_seconds()/60)
        elif isinstance(time, np.timedelta64):
            new_times.append(float((time / np.timedelta64(1, 's')) / 60))
        else:
            raise TypeError(f"Can't make time out of {time} with type {type(time)}")
    return new_times
