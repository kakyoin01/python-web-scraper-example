class GenTable:
    """
    GenTable class - Data structure container for holding game-location pairs for printing.
    Also contains a special formatted printout function for displaying data pleasantly.
    """
    def __init__(self, generation):
        self._generation = generation
        self._game_loc_pairs = []

    def add_game_loc_pair(self, game_names, game_locs):
        self._game_loc_pairs.append(GameLocPair(game_names, game_locs))

    def print_table(self):
        print(self._generation)
        print("-" * len(self._generation))
        for game_loc_pair in self._game_loc_pairs:
            print(game_loc_pair)


class GameLocPair:
    """
    GameLocPair class - Data structure container for holding a pair of games with their
    respective locations.
    """
    def __init__(self, game_names, game_locs):
        self._game_names = game_names
        self._game_locs = game_locs

    def __str__(self):
        return "/".join(self._game_names) + ": " + ", ".join(self._game_locs)
