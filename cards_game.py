# coding=utf-8
import time
from random import shuffle, sample

from flask import Flask, render_template, redirect, url_for, request, session, jsonify
from db import db
from bson import ObjectId
import bcrypt

import card as Card


app = Flask(__name__)


@app.route('/')
def index():
    if 'username' in session:
        current_user = session['username']
        is_gaming = db.games.find_one({'current_turn': current_user})
        if is_gaming:
            return redirect(url_for('game'))

        cant_play_against = [current_user, ]
        players_in_game = [game.players for game in db.games.find({'in_progress': True})]
        for players in players_in_game:
            for player_id in players.keys():
                cant_play_against.push(player_id)
        users = db.users.find({'username': {'$not': {'$in': cant_play_against}}})
        return render_template('index.html', users=users)

    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        login_user = db.users.find_one({'username': request.form.get('username')})
        if login_user:
            if bcrypt.hashpw(request.form.get('password').encode('utf-8'), login_user['password'].encode('utf-8')) == login_user['password'].encode('utf-8'):
                session['username'] = request.form.get('username')
                return redirect(url_for('index'))
    return 'Invalid username/password combanition'


@app.route('/logout')
def logout():
    if 'username' in session:
        session.pop('username')
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        existing_user = db.users.find_one({'username': request.form.get('username')})
        if existing_user:
            return 'The user name has been registered'
        hashpass = bcrypt.hashpw(request.form.get('password').encode('utf-8'), bcrypt.gensalt())
        db.users.insert({
            'username': request.form.get('username'),
            'password': hashpass,
            'deck': [
                'Fry', 'Fry',
                'Dr.Zoidberg',
                'Art',
                'Toy',
                'Money',
                'Music',
                'Weapon'
            ]
        })
        session['username'] = request.form.get('username')
        return redirect(url_for('index'))
    return render_template('register.html')


@app.route('/gameWith/<another_user>')
def create_game(another_user):
    current_user = session['username']
    players = {}
    for username in [current_user, another_user]:
        deck = [Card.init(c) for c in db.users.find_one({'username': username})['deck']]
        shuffle(deck)
        hand = [deck.pop(0) for _ in range(5)]
        players[username] = {
            'deck': deck,
            'hand': hand,
            'table': [],
            'hp': 20,
        }

    game = {
        'players': players,
        'current_turn': [current_user, another_user],
        'in_process': True,
        'started': time.time()
    }

    game_id = db.games.insert(game)

    return redirect(url_for('game'))


@app.route('/game')
def game():
    current_user = session['username']
    game = db.games.find_one({'current_turn': current_user})
    if not game:
        return redirect(url_for('index'))        
    return render_template('play.html', game=game)


@app.route('/takeTurn', methods=['POST'])
def take_turn():
    current_user = session['username']
    card = request.json
    game = db.games.find_one({'current_turn': current_user})
    if game['current_turn'][0] == current_user:
        opponent_user = game['current_turn'][1]
    else:
        opponent_user = game['current_turn'][0]
    hand = game['players'][current_user]['hand']

    if game['current_turn'][0] != current_user or not card in hand:
        return 'Never Cheat'
    
    # put card to table
    table = game['players'][current_user]['table']
    table.append(hand.pop(hand.index(card)))
    deck = game['players'][current_user]['deck']
    if deck:
        hand.append(deck.pop(0))


    # attack
    opponent_table = game['players'][opponent_user]['table']
    for i, _ in enumerate(table):
        if len(opponent_table) >= i+1:
            table[i], opponent_table[i], game['players'][opponent_user] = Card.attack_card(table[i], opponent_table[i], game['players'][opponent_user])
            if table[i]['hp'] < 0:
                table.pop(i)
            if opponent_table[i]['hp'] < 0:
                opponent_table.pop(i)
        else:
            table[i], game['players'][opponent_user] = Card.attack_boss(table[i], game['players'][opponent_user])

    # update gamedata
    game['players'][current_user]['deck'] = deck
    game['players'][current_user]['hand'] = hand
    game['players'][current_user]['table'] = table
    game['players'][opponent_user]['table'] = opponent_table
    game['current_turn'] = game['current_turn'][::-1]

    db.games.update({'_id': game['_id']}, game)

    return redirect(url_for('game'))


@app.route('/getGameData')
def get_game_data():
    current_user = session['username']
    game = db.games.find_one({'current_turn': current_user})
    if not game:
        return 'error'
    game.pop('_id')
    return jsonify(game)


if __name__ == '__main__':
    app.debug = True
    app.threaded = True
    app.secret_key = 'mysecret'
    app.run(host='0.0.0.0', debug=True)