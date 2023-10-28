import os
import data_functions as datafun
import scipy.stats as st
import numpy as np
import math

import matplotlib.pyplot as plt

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
    data_by_map = (df.groupby(["map", "match_id"], group_keys=False)["value"].
                   apply(lambda building: (building == "Town Center").sum() / 2)).reset_index()
    maps = data_by_map["map"].unique()
    grid_size = int(np.ceil(math.sqrt(len(maps))))

    if grid_size * grid_size - 1 >= len(maps):
        fig_tcs, axes_tcs = plt.subplots(grid_size, grid_size - 1, figsize=(8, 8))
        max_rows = grid_size - 1
    else:
        fig_tcs, axes_tcs = plt.subplots(grid_size, grid_size, figsize=(8, 8))
        max_rows = grid_size

    fig_tcs.tight_layout()
    plt.subplots_adjust(left=0.1, bottom=0.07, top=0.90, hspace=0.4)

    for index, location in enumerate(maps):
        column = index // grid_size
        row = index - (column*grid_size)
        tcs_added_on_map = data_by_map[data_by_map['map'] == location]["value"]
        axes_tcs[row, column].hist(tcs_added_on_map, density=True, align="left",
                                   edgecolor="darkgreen", color="green",
                                   bins=np.arange(0, int(np.ceil(max(tcs_added_on_map)))))
        axes_tcs[row, column].set_title(location)
        axes_tcs[row, column].set_xticks(np.arange(0, int(np.ceil(max(tcs_added_on_map)))))
        if row == max_rows:
            axes_tcs[row, column].set_xlabel("Added TCs")
        if column == 0:
            axes_tcs[row, column].set_ylabel("Fraction")
    fig_tcs.suptitle("TCs Added Per Map", fontsize="xx-large")
    [fig_tcs.delaxes(ax) for ax in axes_tcs.flatten() if not ax.has_data()]

    # UPTIMES PER MAP
    # Uses data_by_map, maps, and grid size from above

    if grid_size * grid_size - 1 >= len(maps):
        fig_tcs, axes_tcs = plt.subplots(grid_size, grid_size - 1, figsize=(8, 8))
        max_rows = grid_size - 1
    else:
        fig_tcs, axes_tcs = plt.subplots(grid_size, grid_size, figsize=(8, 8))
        max_rows = grid_size

    fig_tcs.tight_layout()
    plt.subplots_adjust(left=0.1, bottom=0.07, top=0.90, hspace=0.4)





