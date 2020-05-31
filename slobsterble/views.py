"""API views."""

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import func
from sqlalchemy.orm import joinedload, subqueryload

from slobsterble import db
from slobsterble.controller import (
    mutate_data,
    validate_play_data,
    validate_user_turn
)
from slobsterble.models import (
    Dictionary,
    Entry,
    Game,
    GamePlayer,
    Move,
    PlayedTile,
    Player,
    Role,
    Tile,
    TileCount,
    User,
)

ACTIVE_GAME_LIMIT = 10
RACK_TILES_MAX = 7

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route('/active-games', methods=['GET'])
@login_required
def get_active_games():
    """Get in progress games."""
    user_active_players = db.session.query(GamePlayer).join(
        GamePlayer.player).join(Player.user).filter(
        User.id == current_user.id).join(GamePlayer.game).order_by(
        Game.started.desc()).limit(ACTIVE_GAME_LIMIT).subquery()
    user_active_games = db.session.query(Game).join(
        user_active_players, Game.id == user_active_players.c.game_id).join(
        Game.game_players).join(GamePlayer.player).options(
        subqueryload(Game.game_players).joinedload(GamePlayer.player))
    serialized_games = Game.serialize_list(
        user_active_games.all(),
        override_mask={Game: ['started', 'whose_turn_name', 'game_players', 'id'],
                       GamePlayer: ['score', 'player'],
                       Player: ['display_name']})
    return jsonify(games=serialized_games)


@bp.route('/game/<int:game_id>', methods=['GET'])
@login_required
def get_game(game_id):
    """
    Get the current state of the game.

    This includes:
    - The played tiles.
    - The names and scores of the other players.
    - The logged in user's rack tiles.
    - The number of tiles remaining.
    - Whose turn it is.
    """
    game_query = db.session.query(Game).filter(Game.id == game_id).join(
        Game.game_players).join(GamePlayer.player).join(Player.user).join(
        Game.board_state).options(subqueryload(Game.board_state).joinedload(
        PlayedTile.tile)).options(subqueryload(Game.game_players).joinedload(
        GamePlayer.player).joinedload(Player.user))
    if game_query.count() == 0:
        # The game does not exist.
        # TODO: return HTTP status code.
        print('Game does not exist')
        return {}
    if game_query.filter(User.id == current_user.id).count() == 0:
        # The user is not part of this game.
        # TODO: return HTTP status code.
        print('User is not authorized')
        return {}
    serialized_game_state = game_query.first().serialize(
        override_mask={Game: ['board_state', 'game_players',
                              'whose_turn_name', 'num_tiles_remaining'],
                       GamePlayer: ['score', 'player'],
                       Player: ['display_name'],
                       PlayedTile: ['tile', 'row', 'column'],
                       Tile: ['letter', 'is_blank', 'value']})
    user_rack = db.session.query(GamePlayer).filter(
        GamePlayer.game_id == game_id).join(GamePlayer.player).join(
        Player.user).filter(Player.user_id == current_user.id).join(
        GamePlayer.rack).join(TileCount.tile).options(
        subqueryload(GamePlayer.rack).joinedload(TileCount.tile)).first()
    serialized_user_rack = user_rack.serialize(
        override_mask={GamePlayer: ['rack'],
                       TileCount: ['tile', 'count'],
                       Tile: ['letter', 'is_blank', 'value']})
    serialized_game_state['rack'] = serialized_user_rack['rack']
    return jsonify(game_state=serialized_game_state)


@bp.route('/game/<int:game_id>/verify-word/<string:word>', methods=['GET'])
@login_required
def verify_word(game_id, word):
    game_query = db.session.query(Game).filter(Game.id == game_id).join(
        Game.game_players).join(GamePlayer.player).join(Player.user)
    if game_query.count() == 0:
        # The game does not exist.
        # TODO: return HTTP status code.
        print('Game does not exist')
        return {}
    if game_query.filter(User.id == current_user.id).count() == 0:
        # The user is not part of this game.
        # TODO: return HTTP status code.
        print('User is not authorized')
        return {}
    word_lookup = db.session.query(Game).join(Game.dictionary).join(
        Dictionary.entries).filter(
        func.lower(Entry.word) == func.lower(word)).options(
        joinedload(Game.dictionary).subqueryload(Dictionary.entries)).first()
    if word_lookup is None:
        return {}
    return jsonify(entry=word_lookup.dictionary.entries[0].serialize())


@bp.route('/game/<int:game_id>/play', methods=['POST'])
@login_required
def play(game_id):
    data = request.json
    is_valid_data = validate_play_data(data)
    mutate_data(data)
    is_current_user_turn = validate_user_turn(current_user, game_id)
    # Validate that the play is valid.
    # Calculate the score of the play.
    # Update the player's score.
    # Update the player's rack with new tiles from the bag.
    # Update the board state.
    # Update whose turn it is or complete the game.
