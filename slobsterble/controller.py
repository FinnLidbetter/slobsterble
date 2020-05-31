"""Controller for updating a game state."""

from collections import defaultdict

from slobsterble import db
from slobsterble.models import (
    Game,
    GamePlayer,
    User)


PLAYED_TILE_REQUIRED_FIELDS = [
    'row', 'column', 'letter', 'is_blank', 'is_exchange']
GAME_ROWS = 15
GAME_COLUMNS = 15
CENTER_ROW = GAME_ROWS // 2
CENTER_COLUMN = GAME_COLUMNS // 2
TILE_VALUE_MAX = 10


def _validate_bool(value, allow_none):
    """Validate that the given value is either 'True', or 'False', or None."""
    if allow_none and value is None:
        return True
    return value == 'True' or value == 'False'


def _validate_int(value, value_min, value_max, allow_none):
    """Validate that the given value is an int within the specified bounds."""
    if allow_none and value is None:
        return True
    try:
        cast_value = int(value)
        return value_min <= cast_value <= value_max
    except ValueError:
        return False


def _validate_alpha_character(value, require_lower=False,
                              require_upper=False, allow_none=False):
    """Validate that the given value is a single alphabetic character."""
    if allow_none and value is None:
        return True
    if not isinstance(value, str):
        return False
    if len(value) != 1:
        return False
    if not value.isalpha():
        return False
    if require_lower and value.lower() != value:
        return False
    if require_upper and value.upper() != value:
        return False
    return True


def _validate_played_tile(played_tile):
    """Validate that the tile data has the expected types and value ranges."""
    for field in PLAYED_TILE_REQUIRED_FIELDS:
        if field not in played_tile:
            return False
    if len(played_tile) > len(PLAYED_TILE_REQUIRED_FIELDS):
        return False
    if not _validate_int(played_tile['row'], 0, GAME_ROWS - 1, True):
        return False
    if not _validate_int(played_tile['column'], 0, GAME_COLUMNS - 1, True):
        return False
    if not _validate_int(played_tile['value'], 0, TILE_VALUE_MAX, False):
        return False
    if not _validate_alpha_character(played_tile['letter'], allow_none=True):
        return False
    if not _validate_bool(played_tile['is_blank'], False):
        return False
    if not _validate_bool(played_tile['is_exchange'], False):
        return False
    return True


def mutate_data(data):
    """
    Convert values to python types and standardise letters as uppercase.

    This function assumes that the data has been validated.
    """
    for played_tile in data['played_tiles']:
        played_tile['is_blank'] = played_tile['is_blank'] == 'True'
        played_tile['is_exchange'] = played_tile['is_exchange'] == 'True'
        played_tile['value'] = int(played_tile['value'])
        if played_tile['row'] is not None:
            played_tile['row'] = int(played_tile['row'])
        if played_tile['column'] is not None:
            played_tile['column'] = int(played_tile['column'])
        if played_tile['letter'] is not None:
            played_tile['letter'] = played_tile['letter'].upper()


def validate_play_data(data):
    """Validate that the play data is formatted as expected."""
    if 'played_tiles' not in data:
        return False
    data_played_tiles = data['played_tiles']
    if not isinstance(data_played_tiles, list):
        return False
    tiles_exchanged = 0
    for played_tile in data_played_tiles:
        if not _validate_played_tile(played_tile):
            return False
    return True


def validate_plausible_data(data):
    """
    Check that tiles are played on a single axis in distinct cells or exchanged.

    Assumes that data has been parsed to have the expected types.
    """
    row_set = set()
    column_set = set()
    exchanged_count = 0
    tiles_played = len(data['played_tiles'])
    for played_tile in data['played_tiles']:
        row_set.add(played_tile['row'])
        column_set.add(played_tile['column'])
        if played_tile['is_exchange']:
            exchanged_count += 1
        elif played_tile['letter'] is None:
            # Letter can only be None if it is a blank tile being exchanged.
            return False
    if exchanged_count > 0:
        return exchanged_count == len(data['played_tiles'])
    return (len(row_set) == 1 and len(column_set) == tiles_played) or (
        len(column_set) == 1 and len(row_set) == tiles_played)


def validate_user_turn(current_user, game_id):
    """Return true iff it is current_user's turn in the given game."""
    game_query = db.session.query(Game).filter(Game.id == game_id).options(
        joinedload(Game.game_player_to_play).joinedload(
        GamePlayer.player).joinedload(Player.user)).first()
    if game_query is None:
        # The queried game does not exist.
        return False
    return game_query.game_player_to_play.player.user.id == current_user.id


def _validate_player_has_tiles(game_query, data):
    """Validate that the player has the tiles played."""
    played_letter_counts = defaultdict(lambda: defaultdict(int))
    exchange_count = 0
    for played_tile in data['played_tiles']:
        letter = played_tile['letter']
        value = played_tile['value']
        if played_tile['is_blank']:
            letter = None
        else:
            letter = letter.upper()
        if played_tile['is_exchange']:
            exchange_count += 1
        played_letter_counts[letter][value] += 1
    rack = game_query.game_player_to_play.rack
    rack_tile_counts = defaultdict(lambda: defaultdict(int))
    for tile_count in rack:
        letter = tile_count.tile.letter
        if letter is not None:
            letter = letter.upper()
        value = tile_count.tile.value
        rack_letter_counts[letter][value] += tile_count.count
    for letter in player_letter_counts:
        for value in player_letter_counts[letter]:
            if letter not in rack_letter_counts:
                return False
            if value not in rack_letter_counts[letter]:
                return False
            if rack_letter_counts[letter][value] < \
                    player_letter_counts[letter][value]:
                return False
    return True


def _get_game_grid(game_query):
    """Get the current board state as a 2-D array."""
    grid = [[None for _ in range(GAME_COLUMNS)] for _ in range(GAME_ROWS)]
    for played_tile in game_query.board_state:
        grid[played_tile.row][played_tile.column] = played_tile.letter
    return grid


def _validate_cells_available(grid, data):
    """Validate that the cells that the tiles are played in are empty."""
    for played_tile in data['played_tiles']:
        if grid[played_tile['row']][played_tile['column']] is not None:
            return False
    return True

def _validate_continuous(grid, data):
    """
    Validate that the tiles played form a continous sequence of tiles.

    Assumes that the played tiles are along a single axis in distinct
    empty cells.
    """
    row_set = set()
    column_set = set()
    for played_tile in data['played_tiles']:
        row_set.add(played_tile['row'])
        column_set.add(played_tile['column'])
    if len(row_set) == 1:
        played_column_min = min(column_set)
        played_column_max = max(column_set)
        row = row_set.pop()
        for column in range(played_column_min, played_column_max + 1):
            if not column in column_set and grid[row][column] is None:
                return False
        return True
    played_row_min = min(row_set)
    played_row_max = max(row_set)
    column = column_set.pop()
    for row in range(played_row_min, played_row_max + 1):
        if not row in row_set and grid[row][column] is None:
            return False
    return True


def _is_first_turn(data):
    """Return True iff the played tiles go through the center cell."""
    for played_tile in data['played_tiles']:
        if played_tile['row'] == CENTER_ROW and \
                played_tile['column'] == CENTER_COLUMN:
            return True
    return False


def _validate_connects(grid, data):
    """Return True iff a played tile is adjacent to a tile on the board."""
    row_offsets = [0, 0, 1, -1]
    column_offset = [1, -1, 0, 0]
    for played_tile in data['played_tiles']:
        row = played_tile['row']
        column = played_tile['column']
        for d_row, d_column in zip(row_offsets, column_offsets):
            adjacent_row = row + d_row
            adjacent_column = column + d_column
            if 0 <= adjacent_row < GAME_ROWS and \
                    0 <= adjacent_column < GAME_COLUMNS:
                if grid[adjacent_row][adjacent_column] is not None:
                    return True
    return False


def _get_words(grid, data):
    """Get a set of the new words created by the played tiles."""
    if len(data['played_tiles']) == 0 or data['played_tiles'][0]['is_exchange']:
        # Either the turn was passed or tiles were exchanged.
        return set()
    if len(data['played_tiles']) == 1:
        # Special case where a single letter word is played on the first turn.
        row = data['played_tiles'][0]['row']
        column = data['played_tiles'][0]['column']
        if row == CENTER_ROW and column == CENTER_COLUMN:
            return {data['played_tiles'][0]['letter']}
    row_set = set()
    column_set = set()
    played_tile_map = defaultdict(dict)
    for played_tile in data['played_tiles']:
        row = played_tile['row']
        column = played_tile['column']
        row_set.add(row)
        column_set.add(column)
        played_tile_map[row][column] = played_tile['letter']
    word_set = set()
    for played_tile in data['played_tiles']:
        word = played_tile['letter']
        base_row = played_tile['row']
        base_column = played_tile['column']
        row = base_row - 1
        while row >= 0:
            if row in row_set:
                word = played_tile_map[row][base_column] + word
            elif grid[row][base_column] is not None:
                word = grid[row][base_column] + word
            else:
                break
            row -= 1
        row = base_row + 1
        while row < GAME_ROWS:
            if row in row_set:
                word += played_tile_map[row][base_column]
            elif grid[row][base_column] is not None:
                word += grid[row][base_column]
            else:
                break
            row += 1
        if len(word) > 1:
            word_set.add(word)
        word = played_tile['letter']
        column = base_column - 1
        while column >= 0:
            if column in column_set:
                word = played_tile_map[base_row][column] + word
            elif grid[base_row][column] is not None:
                word = grid[base_row][column] + word
            else:
                break
            column -= 1
        column = base_column + 1
        while column < GAME_COLUMNS:
            if column in column_set:
                word += played_tile_map[base_row][column]
            elif grid[base_row][column] is not None:
                word += grid[base_row][column]
            else:
                break
            column += 1
        if len(word) > 1:
            word_set.add(word)
    return word_set


def validate_play(game_id, data):
    """
    Return true iff the play is a legal use of the player's tiles.

    Assumes:
    - The data has been validated and mutated as expected.
    - It is the current_user's turn.
    """
    game_query = db.session.query(Game).filter(Game.id == game_id).join(
        Game.game_player_to_play).join(GamePlayer.player).join(
        Player.user).join(GamePlayer.rack).join(
        TileCount.tile).join(Game.board_state).join(PlayedTile.tile).join(
        Game.dictionary).join(Dictionary.entries).options(
        joinedload(Game.game_player_to_play).subqueryload(
        GamePlayer.rack).joinedload(TileCount.tile)).options(
        subqueryload(Game.board_state).joinedload(PlayedTile.tile)).options(
        joinedload(Game.dictionary).subqueryload(Dictionary.entries)).first()
    if not _validate_player_has_tiles(game_query, data):
        return False
    game_grid = _get_game_grid(game_query)
    if not _validate_cells_available(grid, data):
        return False
    if not _validate_continuous(grid, data):
        return False
    if not _is_first_turn(data) and not _validate_connects(grid, data):
        return False
    words_created = _get_words(grid, data)
