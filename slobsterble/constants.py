"""Constants for the slobsterble game."""

ACTIVE_GAME_LIMIT = 20
BINGO_BONUS = 50
GAME_ROWS_MIN = 11
GAME_ROWS_MAX = 21
GAME_COLUMNS_MIN = 11
GAME_COLUMNS_MAX = 21
TILES_ON_RACK_MAX = 7
WORD_LENGTH_MAX = 21

CLASSIC_WORD_MULTIPLIERS = [
    [3, 1, 1, 1, 1, 1, 1, 3, 1, 1, 1, 1, 1, 1, 3],
    [1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1],
    [1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1],
    [1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1],
    [1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [3, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 3],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1],
    [1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1],
    [1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1],
    [1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1],
    [3, 1, 1, 1, 1, 1, 1, 3, 1, 1, 1, 1, 1, 1, 3],
]

CLASSIC_LETTER_MULTIPLIERS = [
    [1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1],
    [1, 1, 1, 1, 1, 3, 1, 1, 1, 3, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 2, 1, 2, 1, 1, 1, 1, 1, 1],
    [2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 3, 1, 1, 1, 3, 1, 1, 1, 3, 1, 1, 1, 3, 1],
    [1, 1, 2, 1, 1, 1, 2, 1, 2, 1, 1, 1, 2, 1, 1],
    [1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1],
    [1, 1, 2, 1, 1, 1, 2, 1, 2, 1, 1, 1, 2, 1, 1],
    [1, 3, 1, 1, 1, 3, 1, 1, 1, 3, 1, 1, 1, 3, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2],
    [1, 1, 1, 1, 1, 1, 2, 1, 2, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 3, 1, 1, 1, 3, 1, 1, 1, 1, 1],
    [1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1],
]

CLASSIC_DISTRIBUTION = {
    ("A", 1): 9,
    ("B", 3): 2,
    ("C", 3): 2,
    ("D", 2): 4,
    ("E", 1): 12,
    ("F", 4): 2,
    ("G", 2): 3,
    ("H", 4): 2,
    ("I", 1): 9,
    ("J", 8): 1,
    ("K", 5): 1,
    ("L", 1): 4,
    ("M", 3): 2,
    ("N", 1): 6,
    ("O", 1): 8,
    ("P", 3): 2,
    ("Q", 10): 1,
    ("R", 1): 6,
    ("S", 1): 4,
    ("T", 1): 6,
    ("U", 1): 4,
    ("V", 4): 2,
    ("W", 4): 2,
    ("X", 8): 1,
    ("Y", 4): 2,
    ("Z", 10): 1,
    (None, 0): 2,
}

MULTIPLIER_MIN = 1
MULTIPLIER_MAX = 4

TILE_VALUE_MAX = 10
TILE_COUNT_MAX = 25
SPACES_TILES_RATIO_MIN = 2

UDID_MAX_LENGTH = 64

DISPLAY_NAME_LENGTH_MAX = 15
FRIEND_KEY_CHARACTERS = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
FRIEND_KEY_LENGTH = 7

GAME_PLAYERS_MAX = 4

REGISTRATION_VERIFICATION_SECONDS = 86400
PASSWORD_RESET_VERIFICATION_SECONDS = 900
