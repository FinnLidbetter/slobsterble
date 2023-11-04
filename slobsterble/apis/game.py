"""Views related to game play."""

import sqlalchemy.orm.exc
from flask import Response, request, jsonify
from flask_restful import Resource
from flask_jwt_extended import jwt_required, current_user

import slobsterble.api_exceptions
from slobsterble.app import db
from slobsterble.game_play_controller import (
    StatelessValidator,
    StatefulValidator,
    StateUpdater,
    WordBuilder,
    WordValidator,
    fetch_game_state,
    get_game_player,
)
from slobsterble.models import Move, PlayedTile
from slobsterble.models.lock import acquire_lock, AcquireLockException
from slobsterble.notifications.notify import notify_next_player


class GameView(Resource):
    @jwt_required()
    def get(self, game_id):
        if request.headers.get("Accept-version") == "v2":
            return self._versioned_get(game_id, 2)
        else:
            return self._versioned_get(game_id, 1)

    @staticmethod
    def _versioned_get(game_id, version):
        """
        Get the current state of the game.

        This includes:
        - The played tiles.
        - The names and scores of the other players.
        - The logged in user's rack tiles.
        - The number of tiles remaining.
        - Whose turn it is.
        """
        try:
            game_state = fetch_game_state(game_id)
        except sqlalchemy.orm.exc.NoResultFound:
            return Response("Game with id %s not found." % str(game_id), status=404)
        if not any(
            game_player.player.user_id == current_user.id
            for game_player in game_state.game_players
        ):
            return Response("User is not authorized to access this game.", status=401)

        def _game_player_sort(game_player):
            return game_player["turn_order"]

        serialized_game_state = game_state.serialize(
            override_mask={
                "Game": [
                    "board_state",
                    "game_players",
                    "turn_number",
                    "whose_turn_name",
                    "num_tiles_remaining",
                    "board_layout",
                ],
                "GamePlayer": ["score", "player", "turn_order", "num_tiles_remaining"],
                "Player": ["id", "display_name"],
                "PlayedTile": ["tile", "row", "column"],
                "Tile": ["letter", "is_blank", "value"],
                "BoardLayout": ["rows", "columns", "modifiers"],
                "PositionedModifier": ["row", "column", "modifier"],
                "Modifier": ["letter_multiplier", "word_multiplier"],
            },
            sort_keys={"GamePlayer": _game_player_sort},
        )
        current_game_player = None
        for game_player in game_state.game_players:
            if game_player.player.user_id == current_user.id:
                current_game_player = game_player
                break
        serialized_user_rack = current_game_player.serialize(
            override_mask={
                "GamePlayer": ["rack"],
                "TileCount": ["tile", "count"],
                "Tile": ["letter", "is_blank", "value"],
            }
        )
        if game_state.turn_number > 0:
            prev_turn_order = (game_state.turn_number - 1) % len(
                game_state.game_players
            )
            prev_play_player = game_state.game_players[0]
            for game_player in game_state.game_players:
                if game_player.turn_order == prev_turn_order:
                    prev_play_player = game_player
                    break
            prev_move = (
                db.session.query(Move)
                .filter(
                    Move.game_player_id == prev_play_player.id,
                    Move.turn_number == game_state.turn_number - 1,
                )
                .one()
            )
            exchanged_count = sum(
                tile_count.count for tile_count in prev_move.exchanged_tiles
            )
            serialized_prev_move = {
                "word": prev_move.primary_word,
                "score": prev_move.score,
                "player_id": prev_play_player.player_id,
                "display_name": prev_play_player.player.display_name,
                "exchanged_count": exchanged_count,
            }
            if version == 2:
                prev_move_played_tiles = prev_move.played_tiles
                serialized_prev_move_tiles = PlayedTile.serialize_list(
                    prev_move_played_tiles
                )
                serialized_prev_move["played_tiles"] = serialized_prev_move_tiles
            serialized_game_state["prev_move"] = serialized_prev_move
        else:
            serialized_game_state["prev_move"] = None
        serialized_game_state["rack"] = serialized_user_rack["rack"]
        serialized_game_state["fetcher_player_id"] = current_game_player.player_id
        return jsonify(serialized_game_state)

    @staticmethod
    @jwt_required()
    def post(game_id):
        """API to play a turn of the game."""
        lock_expiry_seconds = 60
        try:
            with acquire_lock(f"game:{game_id}", expire_seconds=lock_expiry_seconds):
                data = request.get_json()
                try:
                    stateless_validator = StatelessValidator(data)
                    stateless_validator.validate()
                    try:
                        game_state = fetch_game_state(game_id)
                    except sqlalchemy.orm.exc.NoResultFound:
                        return Response("Game does not exist.", status=400)
                    game_player = get_game_player(game_state)
                    stateful_validator = StatefulValidator(
                        data, game_state, game_player
                    )
                    stateful_validator.validate()
                    game_board = stateful_validator.game_board
                    word_builder = WordBuilder(data, game_board)
                    primary_word, secondary_words = word_builder.get_played_words()
                    turn_score = word_builder.compute_score()
                    if primary_word is not None:
                        word_validator = WordValidator(
                            [primary_word] + secondary_words, game_state.dictionary_id
                        )
                        word_validator.validate()
                    state_updater = StateUpdater(
                        data=data,
                        game_state=game_state,
                        game_player=game_player,
                        turn_score=turn_score,
                        primary_word=primary_word,
                        secondary_words=secondary_words,
                    )
                    game_over = state_updater.update_state()
                    if not game_over:
                        notify_next_player(game_id)
                    return Response("Turn played successfully.", status=200)
                except slobsterble.api_exceptions.BaseApiException as play_error:
                    return Response(str(play_error), status=play_error.status_code)
        except AcquireLockException:
            return Response(
                "Server error. Encountered a lock on this game. Please try again "
                f"after at least {lock_expiry_seconds} seconds.",
                status=500,
            )
