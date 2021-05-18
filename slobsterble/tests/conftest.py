"""Setup pytest fixtures."""

import pytest
from flask_jwt_extended import create_access_token

from slobsterble.app import db as database, create_app
from slobsterble.models import (
    BoardLayout,
    Dictionary,
    Distribution,
    Game,
    GamePlayer,
    Player,
    User,
)


@pytest.fixture(scope='session', autouse=True)
def app_fixture():
    slobsterble_app = create_app()
    return slobsterble_app


@pytest.fixture
def client(app_fixture):
    with app_fixture.test_client() as test_client:
        yield test_client


@pytest.fixture(scope='session', autouse=True)
def db(app_fixture):
    with app_fixture.app_context():
        yield database


def _build_user(name):
    user = User(username=name)
    user.set_password(name)
    return user


def _build_player(user, db):
    default_dictionary = db.session.query(Dictionary).filter_by(id=1).first()
    default_board_layout = db.session.query(BoardLayout).filter_by(
        name='Classic').first()
    default_distribution = db.session.query(Distribution).filter_by(
        name='Classic').first()
    player = Player(user=user, display_name=user.username,
                    dictionary=default_dictionary,
                    board_layout=default_board_layout,
                    distribution=default_distribution)
    return player


@pytest.fixture(scope='session', autouse=True)
def alice(db):
    user = _build_user('Alice')
    player = _build_player(user, db)
    db.session.add(user)
    db.session.add(player)
    db.session.commit()
    yield user
    db.session.delete(player)
    db.session.delete(user)
    db.session.commit()


@pytest.fixture(scope='session', autouse=True)
def bob(db):
    user = _build_user('Bob')
    player = _build_player(user, db)
    db.session.add(user)
    db.session.add(player)
    db.session.commit()
    yield user
    db.session.delete(player)
    db.session.delete(user)
    db.session.commit()


@pytest.fixture(scope='session', autouse=True)
def carol(db):
    user = _build_user('Carol')
    player = _build_player(user, db)
    db.session.add(user)
    db.session.add(player)
    db.session.commit()
    yield user
    db.session.delete(player)
    db.session.delete(user)
    db.session.commit()


@pytest.fixture(scope='session', autouse=True)
def alice_headers(alice):
    access_token = create_access_token(alice)
    headers = {'Authorization': 'Bearer {}'.format(access_token)}
    return headers


@pytest.fixture(scope='session', autouse=True)
def bob_headers(bob):
    access_token = create_access_token(bob)
    headers = {'Authorization': 'Bearer {}'.format(access_token)}
    return headers


@pytest.fixture(scope='session', autouse=True)
def carol_headers(carol):
    access_token = create_access_token(carol)
    headers = {'Authorization': 'Bearer {}'.format(access_token)}
    return headers


@pytest.fixture
def alice_bob_game(alice, bob, db):
    game = Game(dictionary_id=1, board_layout_id=1, initial_distribution_id=1)
    alice_game_player = GamePlayer(player=alice.player, game=game, turn_order=0)
    bob_game_player = GamePlayer(player=bob.player, game=game, turn_order=1)
    game.game_player_to_play = alice_game_player
    db.session.add(game)
    db.session.add(alice_game_player)
    db.session.add(bob_game_player)
    db.session.commit()
    yield game, alice_game_player, bob_game_player
    db.session.delete(bob_game_player)
    db.session.delete(alice_game_player)
    db.session.delete(game)
    db.session.commit()


@pytest.fixture
def alice_bob_carol_game(alice, bob, carol, db):
    game = Game(dictionary_id=1, board_layout_id=1, initial_distribution_id=1)
    alice_game_player = GamePlayer(player=alice.player, game=game, turn_order=0)
    bob_game_player = GamePlayer(player=bob.player, game=game, turn_order=1)
    carol_game_player = GamePlayer(player=carol.player, game=game, turn_order=2)
    game.game_player_to_play = alice_game_player
    db.session.add(game)
    db.session.add(alice_game_player)
    db.session.add(bob_game_player)
    db.session.add(carol_game_player)
    db.session.commit()
    yield game, alice_game_player, bob_game_player, carol_game_player
    db.session.delete(bob_game_player)
    db.session.delete(alice_game_player)
    db.session.delete(carol_game_player)
    db.session.delete(game)
    db.session.commit()

