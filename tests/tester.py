import requests

host = "http://localhost:5000/"

def register_players():
    players = [
        {"name": "Egor Lunev", "tg_id": 12309214, "tg_tag": "@egorshuk1"},
        {"name": "Тишка", "tg_id": 1355214, "tg_tag": "@egorshuk2"},
        {"name": "Коля", "tg_id": 1230, "tg_tag": "@egorshuk2"},
        {"name": "Кочерга", "tg_id": 7848614, "tg_tag": "@egorshuk3"},
        {"name": "Катя", "tg_id": 195312245, "tg_tag": "@asfa"},
        {"name": "Кирюха", "tg_id": 124605312, "tg_tag": "@shadex"},
        {"name": "Админ", "tg_id": 43215097, "tg_tag": "@eblan"},
        {"name": "Вовочка", "tg_id": 823326234, "tg_tag": "@eda"},
        {"name": "Кусок говна", "tg_id": 12309, "tg_tag": "@daun"},
    ]
    for player in players:
        r = requests.post(host+"players/",params=player)
        if r.status_code != 200:
            print("Crashed on",player)
        print(r.text)

register_players()