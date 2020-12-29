"""Models related to users."""

import random

from flask_login import UserMixin
from sqlalchemy.orm import backref, relation, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from slobsterble import db, login_manager
from slobsterble.constants import FRIEND_KEY_LENGTH, FRIEND_KEY_CHARACTERS
from slobsterble.models.mixins import MetadataMixin, ModelMixin, ModelSerializer


user_roles = db.Table(
    'user_roles',
    db.Column('user_id',
              db.Integer,
              db.ForeignKey('user.id'),
              primary_key=True),
    db.Column('role_id',
              db.Integer,
              db.ForeignKey('role.id'),
              primary_key=True))

friends = db.Table(
    'friends',
    db.Column('my_player_id',
              db.Integer,
              db.ForeignKey('player.id'),
              primary_key=True),
    db.Column('friend_player_id',
              db.Integer,
              db.ForeignKey('player.id'),
              primary_key=True))


# Allow flask_login to load users.
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(db.Model, UserMixin, ModelMixin, ModelSerializer):
    """A user model for authentication purposes."""
    # The player attribute is an excluded backref to avoid
    # circular serialization.
    serialize_exclude_fields = ['password_hash', 'player']

    activated = db.Column(db.Boolean(), nullable=False, default=False)
    username = db.Column(db.String(255, collation='NOCASE'),
                         unique=True,
                         nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    roles = db.relationship('Role', secondary=user_roles)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return self.username


class Role(db.Model, ModelMixin, ModelSerializer):
    """Model for authentication and restricting access."""
    name = db.Column(db.String(50), unique=True)


def random_friend_key():
    """Generate a 15 character string of numbers and uppercase letters."""
    return ''.join(random.choices(FRIEND_KEY_CHARACTERS, k=FRIEND_KEY_LENGTH))


class Player(db.Model, MetadataMixin, ModelSerializer):
    """Non-auth, non-game-specific information about users."""
    __tablename__ = "player"
    serialize_exclude_fields = ['game_players', 'friends']

    id = db.Column(db.Integer,
                   primary_key=True,
                   autoincrement=True,
                   doc='Integer ID for the model instance.')

    display_name = db.Column(db.String(15), nullable=False)
    wins = db.Column(db.Integer, nullable=False, default=0)
    ties = db.Column(db.Integer, nullable=False, default=0)
    losses = db.Column(db.Integer, nullable=False, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = relationship('User', backref=db.backref('player', uselist=False))
    highest_individual_score = db.Column(db.Integer, nullable=False, default=0)
    highest_combined_score = db.Column(db.Integer, nullable=False, default=0)
    best_word_score = db.Column(db.Integer, nullable=False, default=0)
    friend_key = db.Column(db.String(FRIEND_KEY_LENGTH), default=random_friend_key)
    friends = relation(
        'Player',
        secondary=friends,
        primaryjoin=friends.c.my_player_id==id,
        secondaryjoin=friends.c.friend_player_id==id,
        backref=backref('friend_of'),
        lazy='subquery',
        doc='The set of players that a player can challenge to a game.')

    def __repr__(self):
        return self.display_name
