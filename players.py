import numpy as np


class Player:
    def __init__(self, name, civ, colour):
        self.name = name
        self.civ = civ
        self.colour = colour

        self.feudal_time = np.nan
        self.castle_time = np.nan
        self.imp_time = np.nan
