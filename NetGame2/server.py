#!/usr/bin/env python3
# coding:utf-8
import colorsys
import random
import socket
import time
import json
from random import randint


HOST, PORT = '', 5058  # address & port
DATA_WIND = 8192  # размер пакета данных
FPS = 0.05  # частота цикла
STEP_WAIT = 0
WIDTH, HEIGHT = 1400, 800
STEP = 8
RADIUS = 6
COUNT = 50
EAT_COUNT = 10
SIZE_MUL = 2


def random_coord():
    x = STEP * ((randint(5, WIDTH - 5)) // STEP)
    y = STEP * ((randint(5, HEIGHT - 5)) // STEP)
    return [x, y]


class Eat:
    def __init__(self):
        self._pos = [0, 0]
        self._body = [random_coord()]
        self._radius = 8
        self._figure = 0
        self._color = (10, 255, 10)
        self._life = ''

    def get_data(self):
        return {'body': self._body, 'radius': self._radius, 'color': self._color,
                'figure': self._figure, 'length': '', 'life': self._life}

    def get_head(self):
        return self._body[0]


class Player:
    def __init__(self, pos=None, radius=RADIUS):
        if pos is None:
            pos = random_coord()
        self._pos = [0, 0]
        self._body = [pos]
        self._inc = 0
        self._radius = radius
        self._data = dict()
        self._step = STEP
        h, s, l = random.choice([ii / 10 for ii in range(1, 11)]), 0.5 + random.random() / 2.0, 0.2 + random.random() / 5.0
        r, g, b = [int(256 * i) for i in colorsys.hls_to_rgb(h, l, s)]
        self._color = (r, g, b)
        #    (randint(100, 200), randint(100, 200), randint(10, 100))
        self._iter = 0
        self._wait = STEP_WAIT
        self._figure = 0
        self._break = 0
        self._life = 1

    def prepare(self):
        # if not self._data:
        #     return
        if self._break == 0:
            cmd = self._data.get('key', [])
            if cmd:
                # self._step = self._data.get('step', self._step)
                if 'left' in cmd:
                    self._pos[0] = -self._step
                    self._pos[1] = 0
                if 'right' in cmd:
                    self._pos[0] = self._step
                    self._pos[1] = 0
                if 'down' in cmd:
                    self._pos[1] = self._step
                    self._pos[0] = 0
                if 'up' in cmd:
                    self._pos[1] = -self._step
                    self._pos[0] = 0
        else:
            self._break -= 1
        # else:
        #     self._iter += 1
        #     if self._iter > self._wait:
        #         self._iter = 0
        #         self._pos[0] += randint(-1, 1)
        #         self._pos[1] += randint(-1, 1)
        if self._data.get('d_rad'):
            self._inc = self._data.get('d_rad')
        self._data['key'] = None
        self._iter += 1
        if self._iter > self._wait:
            self._iter = 0
            self.move()

    def move(self):
        for i in range(len(self._body)):
            if i == 0:
                segment = self._body[i].copy()
                self._body[i] = [(self._body[i][0] + self._pos[0]) % WIDTH,
                                 (self._body[i][1] + self._pos[1]) % HEIGHT]
            else:
                segment, self._body[i] = self._body[i], segment
        self.add_segment(count=self._inc)
        # if self._inc > 0:
        #     for _ in range(self._inc):
        #         self._body.append(segment)
        self._inc = 0
        # print(self._body)

    def add_segment(self, count=1, life=0):
        self._life += life
        segment = self._body[-1]
        for _ in range(count):
            self._body.append(segment)

    def del_segment(self, count=1):
        for _ in range(count):
            self._body.pop()
        if self._life > 0:
            self._life -= 1

    def set_data(self, data):
        self._data = data

    def get_data(self):
        return {'body': self._body, 'radius': self._radius, 'color': self._color,
                'figure': self._figure, 'length': self.get_length(), 'life': self._life}

    def get_head(self):
        return self._body[0]

    def get_length(self):
        return len(self._body)

    def is_in_head(self, pos):
        px, py = self._body[0]
        h_size = self.get_length() // SIZE_MUL + RADIUS
        return abs(pos[0] - px) < h_size and abs(pos[1] - py) < h_size

    def is_head_to_head(self, player):
        pos = player.get_head()
        size = player.get_length() // SIZE_MUL + self.get_length() // SIZE_MUL + 2 * RADIUS
        delta_x = abs(self._body[0][0] - pos[0]) - size
        delta_y = abs(self._body[0][1] - pos[1]) - size
        return delta_x < 0 and delta_y < 0

    def breake(self):
        self._pos = [self._pos[0] * -1, self._pos[1] * -1]
        self._break = min(20, len(self._body)) + RADIUS

    def is_body_atak(self, player):
        x, y = player.get_head()
        size = player.get_length() // SIZE_MUL + RADIUS
        for i in range(1, self.get_length()):
            sx, sy = self._body[i]
            # print(sx, sy)
            if abs(x - sx) - size < 0 and abs(y - sy) - size < 0:
                cut = self.get_length() - i
                if cut <= player.get_length():
                    self.del_segment(cut)
                    # print(cut)
                    return cut
                else:
                    return -1
        return 0


def handle(sock: socket.socket) -> any:
    data = None
    try:
        data = sock.recv(DATA_WIND).decode()  # Should be ready
    except ConnectionError:
        print(f"Client suddenly closed while receiving {sock}")
        return None
    except BlockingIOError:
        pass
    except Exception as e:
        print('Receive error:', e)
    return data


def send_data(sock, data):
    try:
        sock.sendall(data.encode())  # Hope it won't block
    except ConnectionError:
        print(f"Client suddenly closed, cannot send")
        return False
    except BlockingIOError:
        pass
    return True


if __name__ == "__main__":
    fps = FPS
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as main_socket:
        main_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        main_socket.bind((HOST, PORT))
        main_socket.setblocking(False)
        main_socket.listen(1)

        player_sockets = []
        player_data = dict()
        player_data['123'] = Player()
        player_data['123'].add_segment(10)
        player_data['123'].set_data({'key': 'left'})
        # player_data['124'] = Player()
        eat_data = []
        # for i in range(COUNT):
        #     pos = [randint(10, WIDTH - 10), randint(10, HEIGHT - 10)]
        #     radius = randint(5, 20)
        #     player_data[f"bot{i:03}"] = Player(pos=pos, radius=radius)

        print('Server started at:', HOST, PORT)
        # Игровой цикл
        clock = time.time()
        while True:
            time_pause = fps - (time.time() - clock)
            if time_pause > 0:
                time.sleep(time_pause)
            clock = time.time()
            try:
                new_socket, addr = main_socket.accept()
                addr = addr[0]
                main_socket.setblocking(False)
                player_sockets.append(new_socket)
                player_data[addr] = player_data.get(addr, Player())
                print('Connection from:', addr)
            except BlockingIOError:
                pass

            # Получаем данные от игроков
            # player_data.clear()
            addr = ''
            for sock in player_sockets.copy():
                if 'raddr' not in sock.__repr__():
                    continue
                addr = sock.getpeername()
                addr = addr[0]
                data = handle(sock)
                if data:
                    try:
                        data = json.loads(data)
                        # print('Received from:', addr, data)
                    except json.JSONDecodeError:
                        data = dict()
                    player_data[addr].set_data(data)

                # Обработка активности

            # Игровая механика
            for addr, player in player_data.items():
                player.prepare()
                for addr2, player2 in player_data.items():
                    if addr2 == addr:
                        continue
                    if player.is_head_to_head(player2):
                        player.breake()
                        continue
                    count = player.is_body_atak(player2)
                    if count > 0:
                        player2.add_segment(count, 1)
                    elif count < 0:
                        player2.breake()
                        continue

            # Проверка поедания корма
            for eat in eat_data.copy():
                for addr, player in player_data.items():
                    if player.is_in_head(eat.get_head()):
                        # print(eat.get_head(), player.get_head(), player.get_length())
                        player.add_segment()
                        eat_data.remove(eat)
                        break

            if len(eat_data) < EAT_COUNT:
                eat_data.append(Eat())

            # Передача данных игрокам
            data = dict()
            for addr, player in player_data.items():
                data[addr] = player.get_data()
            for i, eat in enumerate(eat_data):
                data[f'eat{i:03}'] = eat.get_data()
            try:
                data = '#####' + json.dumps({'players': data}) + '%%%%%'
            except Exception as err:
                print('Error prepare to send:', err)
            for sock in player_sockets:
                if not send_data(sock, data):
                    player_sockets.remove(sock)
                    sock.close()
