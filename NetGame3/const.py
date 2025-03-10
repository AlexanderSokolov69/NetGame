import json
from random import randint


class Const:
    VERSION = 'v2.5.2'
    restart = 1
    WIDTH = 3000  # Кратно STEP
    HEIGHT = 3000  # Кратно STEP
    STEP = 10
    RADIUS = 10
    COUNT = 2
    SIZE_MUL = 3
    MIN_SAFE_LENGTH = 30
    START_LIFE = 10
    EAT_LIFE = 300
    S_FPS = 40
    EAT_COUNT = 10
    data = dict()
    data['HOST'] = ''
    data['PORT'] = 5885
    data['GAME_TIMER'] = 120
    data['BOTS_COUNTER'] = 30
    data['DATA_WIND'] = 8192
    data['CHAOS'] = True

    def __init__(self):
        with open('srv_config.json') as f:
            data = json.load(f)
            print(data)
            s_port = data.get('PORT')
            s_host = data.get('HOST')
            if s_port:
                Const.data['PORT'] = int(s_port)
            if s_host:
                Const.data['HOST'] = s_host
            Const.data['GAME_TIMER'] = int(data.get('GAME_TIMER', Const.data['GAME_TIMER']))
            Const.data['BOTS_COUNTER'] = int(data.get('BOTS_COUNTER', Const.data['BOTS_COUNTER']))
            # Const.data['DATA_WIND'] = int(data.get('DATA_WIND', Const.data['DATA_WIND']))
            Const.data['CHAOS'] = int(data.get('CHAOS', Const.data['CHAOS']))
            Const.S_FPS = int(data.get('S_FPS', 3))
            Const.EAT_COUNT = int(data.get('EAT_COUNT', 10))
            Const.EAT_LIFE = int(data.get('EAT_LIFE', 300))
            Const.MIN_SAFE_LENGTH = int(data.get('MIN_SAFE_LENGTH', 30))
            Const.START_LIFE = int(data.get('START_LIFE', 10))
            Const.WIDTH = Const.STEP * (int(data.get('WIDTH', 3000)) // Const.STEP)
            Const.HEIGHT = Const.STEP * (int(data.get('HEIGHT', 3000)) // Const.STEP)


rnd = ['left', 'right', 'up', 'down', 'stop', 'freeze']


def random_coord():
    x = 5 * Const.STEP * (randint(1, Const.WIDTH // Const.STEP // 5 - 1))
    y = 5 * Const.STEP * (randint(1, Const.HEIGHT // Const.STEP // 5 - 1))
    return [x, y]

