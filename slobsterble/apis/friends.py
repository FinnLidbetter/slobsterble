"""API view for getting and adding friends."""

from flask import Response, jsonify, request
from flask_jwt_extended import current_user, jwt_required
from flask_restful import Resource
from jsonschema import ValidationError
from jsonschema import validate as schema_validate
from slobsterble.app import db
from slobsterble.constants import FRIEND_KEY_CHARACTERS, FRIEND_KEY_LENGTH
from slobsterble.models import Player
from sqlalchemy.orm import subqueryload

ADD_FRIEND_SCHEMA = {
    "type": "object",
    "required": ["friend_key"],
    "properties": {
        "friend_key": {
            "type": "string",
            "minLength": FRIEND_KEY_LENGTH,
            "maxLength": FRIEND_KEY_LENGTH,
            "pattern": "[" + FRIEND_KEY_CHARACTERS + "]*",
        }
    },
}


class FriendsView(Resource):
    @staticmethod
    @jwt_required()
    def get():
        """Get the current user's friend key and their friends."""
        current_player = (
            db.session.query(Player)
            .filter_by(user_id=current_user.id)
            .options(subqueryload(Player.friends))
            .one()
        )
        data = {
            "friends": [
                {"player_id": player.id, "display_name": player.display_name}
                for player in current_player.friends
            ],
            "friend_key": current_player.friend_key,
        }
        data["friends"].sort(key=lambda player: player["display_name"])
        return jsonify(data)

    @staticmethod
    @jwt_required()
    def post():
        data = request.get_json()
        try:
            schema_validate(data, ADD_FRIEND_SCHEMA)
        except ValidationError:
            return Response("Data does not conform to the schema.", status=400)
        current_player = (
            db.session.query(Player)
            .filter_by(user_id=current_user.id)
            .options(subqueryload(Player.friends))
            .one()
        )
        friend_player = (
            db.session.query(Player)
            .filter_by(friend_key=data["friend_key"])
            .options(subqueryload(Player.friends))
            .one_or_none()
        )
        if friend_player is None:
            return Response(
                "No player has friend key %s." % data["friend_key"], status=400
            )
        if current_player.id == friend_player.id:
            return Response("You cannot add yourself as a friend.", status=400)
        already_friends = True
        if current_player not in friend_player.friends:
            friend_player.friends.append(current_player)
            already_friends = False
        if friend_player not in current_player.friends:
            current_player.friends.append(friend_player)
            already_friends = False
        if already_friends:
            return Response(
                "You are already friends with %s." % friend_player.display_name,
                status=400,
            )
        db.session.commit()
        return Response("Success.", status=200)
