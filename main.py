import os
import data_functions as datafun
import scipy.stats as st
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

replay_location = r"C:/Users/Gebruiker/PycharmProjects/AoE_rec_analysis/replays"
os.chdir(replay_location)
replays = [f for f in os.listdir(replay_location)
           if os.path.isfile(os.path.join(replay_location, f)) and f.endswith(".aoe2record")]

all_actions = ['ORDER', 'DELETE', 'GATHER_POINT', 'BUY', 'WALL', 'STANCE', 'BUILD', 'MOVE',
               'RESEARCH', 'ATTACK_GROUND', 'STOP', 'GAME', 'FORMATION', 'BACK_TO_WORK', 'RESIGN', 'SPECIAL',
               'SELL', 'REPAIR', 'PATROL', 'UNGARRISON', 'DE_ATTACK_MOVE', 'DE_QUEUE']

if __name__ == '__main__':
    # df = datafun.make_data_from_replays(replays, ["DE_QUEUE"])
    df = datafun.make_data_from_replays(replays, all_actions)

    # MONK PER MATCH STATS
    # TODO: Subtract unqueued monks
    monks_per_match_by_player = (df.groupby(["player", "match_id"], group_keys=False)["value"].
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

    # STATS ON TCs ADDED PER MAP
    df_tcs = df[df["value"] == "Town Center"]
    data_by_map = df_tcs.groupby(["map", "match_id", "player"])["value"].count().reset_index()
    maps = data_by_map["map"].unique()
    grid_size = int(np.ceil(np.sqrt(len(maps))))

    if grid_size * grid_size - 1 >= len(maps):
        fig_tcs, axes_tcs = plt.subplots(grid_size, grid_size - 1, figsize=(8, 8))
        max_rows = grid_size - 1
    else:
        fig_tcs, axes_tcs = plt.subplots(grid_size, grid_size, figsize=(8, 8))
        max_rows = grid_size

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
    fig_tcs.suptitle("TCs Added Per Map", fontsize="xx-large")
    [fig_tcs.delaxes(ax) for ax in axes_tcs.flatten() if not ax.has_data()]

    # UPTIMES PER MAP
    # Uses maps, and grid size from above
    data_by_map = df.groupby(["match_id"], group_keys=False).first()
    maps = data_by_map["map"].unique()
    grid_size = int(np.ceil(np.sqrt(len(maps))))

    if grid_size * grid_size - 1 >= len(maps):
        fig_tcs, axes_tcs = plt.subplots(grid_size, grid_size - 1, figsize=(8, 8))
        max_rows = grid_size - 1
    else:
        fig_tcs, axes_tcs = plt.subplots(grid_size, grid_size, figsize=(8, 8))
        max_rows = grid_size

    fig_tcs.tight_layout()
    plt.subplots_adjust(left=0.1, bottom=0.07, top=0.90, hspace=0.4)

    feudal_age_colour = "firebrick"
    castle_age_colour = "darkorchid"
    imp_age_colour = "gold"

    if grid_size * grid_size - 1 >= len(maps):
        fig_upt, axes_upt = plt.subplots(grid_size, grid_size - 1, figsize=(8, 8))
        max_rows = grid_size - 1
    else:
        fig_upt, axes_upt = plt.subplots(grid_size, grid_size, figsize=(8, 8))
        max_rows = grid_size

    for index, location in enumerate(data_by_map["map"].unique()):
        map_df = data_by_map[data_by_map["map"] == location]
        latest_imp = datafun.fetch_latest_time(map_df, "imp")
        latest_castle = datafun.fetch_latest_time(map_df, "castle")
        latest_feudal = datafun.fetch_latest_time(map_df, "feudal")
        latest_age = max(latest_feudal, latest_castle, latest_imp)

        column = index // grid_size
        row = index - (column * grid_size)

        feudal_age_times = map_df[[col for col in map_df.columns if "feudal" in col]].values
        castle_age_times = map_df[[col for col in map_df.columns if "castle" in col]].values
        imp_age_times = map_df[[col for col in map_df.columns if "imp" in col]].values

        axes_upt[row, column].hist(feudal_age_times.flatten(), color=feudal_age_colour, label="Feudal")
        axes_upt[row, column].hist(castle_age_times.flatten(), color=castle_age_colour, label="Castle")
        axes_upt[row, column].hist(imp_age_times.flatten(), color=imp_age_colour, label="Imperial")
        axes_upt[row, column].set_title(location)

        axes_upt[row, column].xaxis.set_major_formatter(mdates.DateFormatter('%M'))

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

    # kde_xs = np.linspace(0, max(data_by_map['timestamp']), 300)
    # axes_monks.hist(monks_per_match_by_player['value'], bins=60, density=True, edgecolor="darkred", color="salmon")
    # kde = st.gaussian_kde(monks_per_match_by_player['value'])

    # TODO: Stats on deleted castles
    # TODO: Analyze openings
