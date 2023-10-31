import os
import data_functions as datafun
import scipy.stats as st
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

replay_location = r"C:/Users/Gebruiker/PycharmProjects/AoE_rec_analysis/replays"
os.chdir(replay_location)
replays = [f for f in os.listdir(replay_location)
           if os.path.isfile(os.path.join(replay_location, f)) and f.endswith(".aoe2record")]

all_actions = ['ORDER', 'DELETE', 'GATHER_POINT', 'BUY', 'WALL', 'STANCE', 'BUILD', 'MOVE',
               'RESEARCH', 'ATTACK_GROUND', 'STOP', 'GAME', 'FORMATION', 'BACK_TO_WORK', 'RESIGN', 'SPECIAL',
               'SELL', 'REPAIR', 'PATROL', 'UNGARRISON', 'DE_ATTACK_MOVE', 'DE_QUEUE']


def calculate_monk_data(data: pd.DataFrame):
    # MONK PER MATCH STATS
    monks_per_match_by_player = (data.groupby(["player", "match_id"], group_keys=False)["value"].
                                 apply(lambda unit: (unit == "Monk").sum())).reset_index()
    monks_per_match_by_player['value'].mean()
    monks_per_match_by_player['value'].var()

    fig_monks, axes_monks = plt.subplots(1, 1)
    kde_xs = np.linspace(0, max(monks_per_match_by_player['value']), 300)
    axes_monks.hist(monks_per_match_by_player['value'], bins=60, density=True, edgecolor="darkred", color="salmon")
    kde = st.gaussian_kde(monks_per_match_by_player['value'])
    axes_monks.plot(kde_xs, kde.pdf(kde_xs), label="PDF", color="saddlebrown")
    axes_monks.set_title("Monks Queued Per Game")
    axes_monks.set_xlabel("# Monks")
    axes_monks.set_ylabel("Fraction")
    plt.show()

    # MONKS PER MAP
    monks_per_map_by_player = datafun.calc_items_made_per_match("Monk", df)
    maps = monks_per_map_by_player["map"].unique()
    fig_monks_map, axes_monks_map, grid_size, max_rows = datafun.create_figure_grid_for_maps(maps)
    fig_monks_map.tight_layout()
    plt.subplots_adjust(left=0.1, bottom=0.07, top=0.90, hspace=0.4)

    max_monks_added = max(monks_per_map_by_player['value'])
    for index, location in enumerate(maps):
        column = index // grid_size
        row = index - (column * grid_size)
        tcs_added_on_map = monks_per_map_by_player[monks_per_map_by_player['map'] == location]["value"]
        axes_monks_map[row, column].hist(tcs_added_on_map, align="left",
                                         edgecolor="darkgoldenrod", color="gold",
                                         bins=np.arange(0, max_monks_added))
        axes_monks_map[row, column].set_title(location)
        axes_monks_map[row, column].set_xticks(np.arange(0, max_monks_added, 10))
        axes_monks_map[row, column].xaxis.set_minor_locator(MultipleLocator(5))
        if row == max_rows:
            axes_monks_map[row, column].set_xlabel("Queued Monks")
        if column == 0:
            axes_monks_map[row, column].set_ylabel("Frequency")
    fig_monks_map.suptitle("Monks Queued Per Map", fontsize="xx-large")
    [fig_monks_map.delaxes(ax) for ax in axes_monks_map.flatten() if not ax.has_data()]


def calculate_tc_data_by_map(data):
    # TODO: Check if axis align with value (appear to spread out from 0-7)
    data_by_map = datafun.calc_items_made_per_match("Town Center", data)
    maps = data_by_map["map"].unique()
    fig_tcs, axes_tcs, grid_size, max_rows = datafun.create_figure_grid_for_maps(maps)
    fig_tcs.tight_layout()
    plt.subplots_adjust(left=0.1, bottom=0.07, top=0.90, hspace=0.4)

    max_tcs_added = max(data_by_map['value'])

    for index, location in enumerate(maps):
        column = index // grid_size
        row = index - (column * grid_size)
        tcs_added_on_map = data_by_map[data_by_map['map'] == location]["value"]
        axes_tcs[row, column].hist(tcs_added_on_map, align="left",
                                   edgecolor="darkgreen", color="green",
                                   bins=np.arange(0, max_tcs_added))
        axes_tcs[row, column].set_title(location)
        axes_tcs[row, column].set_xticks(np.arange(0, max_tcs_added))
        if row == max_rows:
            axes_tcs[row, column].set_xlabel("Added TCs")
        if column == 0:
            axes_tcs[row, column].set_ylabel("Count")
    fig_tcs.suptitle("TCs Foundations Per Map", fontsize="xx-large")
    [fig_tcs.delaxes(ax) for ax in axes_tcs.flatten() if not ax.has_data()]


def calculate_uptimes_by_map(data):
    data_by_map = data.groupby(["match_id"], group_keys=False).first()
    maps = data_by_map["map"].unique()
    fig_tcs, axes_tcs, grid_size, max_rows = datafun.create_figure_grid_for_maps(maps)
    fig_tcs.tight_layout()
    plt.subplots_adjust(left=0.1, bottom=0.07, top=0.90, hspace=0.4)

    feudal_age_colour = "firebrick"
    castle_age_colour = "darkorchid"
    imp_age_colour = "gold"

    if grid_size * (grid_size - 1) >= len(maps):
        fig_upt, axes_upt = plt.subplots(grid_size, grid_size - 1, figsize=(8, 8))
        max_rows = grid_size - 1
    else:
        fig_upt, axes_upt = plt.subplots(grid_size, grid_size, figsize=(8, 8))
        max_rows = grid_size

    latest_imp = datafun.fetch_latest_time(data_by_map, "imp")
    latest_castle = datafun.fetch_latest_time(data_by_map, "castle")
    latest_feudal = datafun.fetch_latest_time(data_by_map, "feudal")
    latest_age = max(latest_feudal, latest_castle, latest_imp)

    for index, location in enumerate(data_by_map["map"].unique()):
        map_df = data_by_map[data_by_map["map"] == location]

        column = index // grid_size
        row = index - (column * grid_size)

        feudal_age_times = map_df[[col for col in map_df.columns if "feudal" in col]].values.flatten()
        castle_age_times = map_df[[col for col in map_df.columns if "castle" in col]].values.flatten()
        imp_age_times = map_df[[col for col in map_df.columns if "imp" in col]].values.flatten()

        feudal_age_times = feudal_age_times[~np.isnat(feudal_age_times)]
        castle_age_times = castle_age_times[~np.isnat(castle_age_times)]
        imp_age_times = imp_age_times[~np.isnat(imp_age_times)]

        feudal_age_times = datafun.make_minutes_out_of_time(feudal_age_times)
        castle_age_times = datafun.make_minutes_out_of_time(castle_age_times)
        imp_age_times = datafun.make_minutes_out_of_time(imp_age_times)

        if not len(feudal_age_times) == 0:
            axes_upt[row, column].hist(feudal_age_times, color=feudal_age_colour, label="Feudal")
        if not len(castle_age_times) == 0:
            axes_upt[row, column].hist(castle_age_times, color=castle_age_colour, label="Castle")
        if not len(imp_age_times) == 0:
            axes_upt[row, column].hist(imp_age_times, color=imp_age_colour, label="Imperial")

        axes_upt[row, column].set_title(location)

        # axes_upt[row, column].xaxis.set_major_formatter(mdates.DateFormatter('%M'))
        # axes_upt[row, column].xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
        axes_upt[row, column].xaxis.set_ticks(np.arange(0, datafun.make_minutes_out_of_time([latest_age])[0], 10))
        axes_upt[row, column].set_xlim(right=datafun.make_minutes_out_of_time([latest_age])[0])

        if row == max_rows:
            axes_tcs[row, column].set_xlabel("Added TCs")
        if column == 0:
            axes_tcs[row, column].set_ylabel("Count")

    axes_upt[int(grid_size / 2), 0].legend(loc="center left",
                                           title="Age",
                                           bbox_to_anchor=(-1, 0.5))
    fig_upt.tight_layout()
    plt.subplots_adjust(left=0.2, bottom=0.07, top=0.90, hspace=0.4)
    fig_upt.suptitle("Age Up Time", fontsize="xx-large")
    [fig_upt.delaxes(ax) for ax in axes_upt.flatten() if not ax.has_data()]
    fig_upt.show()


if __name__ == '__main__':
    df = datafun.make_data_from_replays(replays, all_actions)

    calculate_monk_data(df)
    calculate_tc_data_by_map(df)
    calculate_uptimes_by_map(df)
    # TODO: Stats on deleted castles
    # TODO: Analyze openings
