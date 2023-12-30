import sqlalchemy.exc
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import uuid
import random
from datetime import datetime

#gunicorn --bind 0.0.0.0:5000 wsgi:app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='postgresql://killer-admin:secretkey@postgres:5432/killer-database'
CORS(app)
db = SQLAlchemy(app)
gameStarted = False


class Player(db.Model):
    __tablename__ = 'players'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True)
    tg_id = db.Column(db.Integer, unique=True)
    tg_tag = db.Column(db.Text, unique=True)
    qr_code = db.Column(db.String)
    kills_count = db.Column(db.Integer, default=0)
    killer_name = db.Column(db.String, default="none")
    victim_name = db.Column(db.String, default="none")
    is_alive = db.Column(db.Boolean, default=True)
    is_excomunnicado = db.Column(db.Boolean, default=False)
    is_hunter = db.Column(db.Boolean, default=False)

    def __repr__(self) -> str:
        return f'<Player {self.tg_id}>'

def write_killfeed(data:str):
    with open("history.txt",'a+') as f:
        f.write(data+"\n")

def read_killfeed():
    data = ""
    with open("history.txt",'w') as f:
        data = f.read().encode()
    return data

@app.errorhandler(404)
def not_found_error(e):
    return jsonify(message="not found"), 404


@app.route('/players/', methods=["GET"])
def get_all_players():
    players = Player.query.all()
    response = []
    for player in players:
        tmp = dict()
        tmp['id'] = player.id
        tmp['name'] = player.name
        tmp['tg_id'] = player.tg_id
        tmp['tg_tag'] = player.tg_tag
        tmp['killer_name'] = player.killer_name
        tmp['victim_name'] = player.victim_name
        tmp['is_alive'] = player.is_alive
        response.append(tmp)
    return response


@app.get("/players/<tg_id>/")
def get_player_by_tg_id(tg_id):
    player = Player.query.filter(Player.tg_id == tg_id).first()
    if not player:
        return jsonify(message='player not found'), 404
    resp = dict()
    resp['id'] = player.id
    resp['name'] = player.name
    resp['tg_tag'] = player.tg_tag
    resp['tg_id'] = player.tg_id
    resp['is_alive'] = player.is_alive
    resp['is_hunter'] = player.is_hunter
    resp['is_excomunnicado'] = player.is_excomunnicado
    resp['kills'] = player.kills_count
    resp['victim'] = player.victim_name
    resp['qr_code'] = player.qr_code
    resp['killer'] = player.killer_name
    return resp


@app.route("/players/", methods=['POST'])
def register_player():
    if gameStarted:
        return jsonify(message='forbidden'), 403
    try:
        name = request.args.get("name")
        tg_id = request.args.get("tg_id")
        tg_tag = request.args.get("tg_tag")
        if not name or not tg_tag or not tg_id:
            return jsonify(message='not all data was provided'), 400
        player = Player(name=name,tg_tag=tg_tag,tg_id=tg_id,qr_code=str(uuid.uuid4()))
        db.session.add(player)
        db.session.commit()
        return jsonify(message='success')
    except sqlalchemy.exc.IntegrityError as e:
        print(e)
        return jsonify(message="player already exists"), 400
    except Exception as e:
        print(e)
        return jsonify(message='internal error'), 500


@app.route("/game/status/")
def get_game_status():
    return jsonify(status=gameStarted)


@app.route("/game/start/")
def start_game():
    global gameStarted
    players:list[Player] = Player.query.filter(Player.is_alive == True).all()
    random.shuffle(players)
    for i in range(len(players)):
        players[i].victim_name = players[(i+1)%len(players)].name
        players[(i+1)%len(players)].killer_name = players[i].name
    db.session.commit()
    gameStarted = True
    return jsonify(status=gameStarted)


@app.route("/game/stop/")
def stop_game():
    global gameStarted
    gameStarted = False
    return jsonify(status=gameStarted)


@app.route("/game/reset/contracts/")
def reset_contracts():
    players:list[Player] = Player.query.all()
    for pl in players:
        pl.victim_name = "none"
        pl.killer_name = "none"
    db.session.commit()
    return jsonify(message='success')


@app.route("/game/reset/stats/")
def reset_stats():
    players:list[Player] = Player.query.all()
    for pl in players:
        pl.kills_count = 0
    db.session.commit()
    return jsonify(message='success')


@app.route("/game/reset/revive_all/")
def revive_all_players():
    players:list[Player] = Player.query.all()
    for pl in players:
        pl.is_alive = True
    db.session.commit()
    return jsonify(message='success')


@app.route('/game/resume/')
def resume_game():
    global gameStarted
    gameStarted = True
    return jsonify(status=gameStarted)

@app.get("/game/killfeed/")
def get_killfeed():
    return read_killfeed()


@app.route("/game/kill/<killer_tg_id>/<victim_qr_code>/")
def kill_player(killer_tg_id,victim_qr_code):
    global gameStarted
    if not gameStarted:
        return jsonify(message='game not started'), 403
    killer:Player = Player.query.filter(Player.tg_id == killer_tg_id).first()
    victim:Player = Player.query.filter(Player.qr_code == victim_qr_code).first()
    print(victim,killer)
    if not killer:
        return jsonify(message='killer not found')
    if not victim:
        return jsonify(message='victim not found')
    victim_of_victim = Player.query.filter(Player.name == victim.victim_name).first()
    if killer.is_hunter:
        print("Kill as hunter")
        write_killfeed(f"[{datetime.now()}] {victim.name} was killed by {killer.name}")
        killer.kills_count += 1
        victim.is_alive = False
        killer_of_victim = Player.query.filter(Player.name == victim.killer_name).first()
        killer_of_victim.victim_name = victim.victim_name
        victim_of_victim.killer_name = killer_of_victim.name
        victim.victim_name = "none"
        victim.killer_name = "none"
        db.session.commit()
        return jsonify(message='success')
    elif victim.is_excomunnicado:
        print("Kill excomunnicado")
        write_killfeed(f"[{datetime.now()}] {victim.name} was killed by {killer.name}")
        killer.kills_count += 1
        killer.is_excomunnicado = True
        victim.is_alive = False
        killer_of_victim = Player.query.filter(Player.name == victim.killer_name).first()
        killer_of_victim.victim_name = victim.victim_name
        victim_of_victim.killer_name = killer_of_victim.name
        victim.victim_name = "none"
        victim.killer_name = "none"
        db.session.commit()
        return jsonify(message='success')
    elif killer.victim_name == victim.name:
        print("Default kill")
        write_killfeed(f"[{datetime.now()}] {victim.name} was killed by {killer.name}")
        killer.kills_count += 1
        killer.victim_name = victim.victim_name
        victim.is_alive = False
        victim_of_victim.killer_name = killer.name
        victim.victim_name = "none"
        victim.killer_name = "none"
        db.session.commit()

        return jsonify(message='success')
    return jsonify(message='maybe its not your target')


@app.get("/game/set_excomunnicado/<player_id>/<state>/")
def set_excomunnicado(player_id,state):
    if state == "yes":
        state = True
    else:
        state = False
    player = Player.query.filter(Player.id == player_id).first()
    if not player:
        return jsonify(message='player not found'), 404

    player.is_excomunnicado = state
    db.session.commit()
    return jsonify(message='success')


@app.get("/game/set_hunter/<player_id>/<state>/")
def set_hunter(player_id, state):
    if state == "yes":
        state = True
    else:
        state = False
    player = Player.query.filter(Player.id == player_id).first()
    if not player:
        return jsonify(message='player not found'), 404

    player.is_hunter = state
    db.session.commit()
    return jsonify(message='success')


with app.app_context():
     db.create_all()

if __name__ == '__main__':
    app.run()
