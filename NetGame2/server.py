#!/usr/bin/env python3
# coding:utf-8
import socket
import time
import json
from random import randint


HOST, PORT = '', 5056
DATA_WIND = 8192
WIDTH, HEIGHT = 800, 600
COUNT = 50


class Player:
    def __init__(self, pos=None, radius=1):
        if pos is None:
            pos = [200, 200]
        self._pos = pos
        self._radius = radius
        self._data = dict()
        self._step = 0
        self._color = (randint(100, 255), randint(100, 255), randint(100, 255))
        self._iter = 0
        self._wait = randint(3, 30)

    def prepare(self):
        # if not self._data:
        #     return
        cmd = self._data.get('key', [])
        if cmd:
            self._step = self._data.get('step', self._step)
            if 'left' in cmd:
                self._pos[0] -= self._step
            if 'right' in cmd:
                self._pos[0] += self._step
            if 'down' in cmd:
                self._pos[1] += self._step
            if 'up' in cmd:
                self._pos[1] -= self._step
        else:
            self._iter += 1
            if self._iter > self._wait:
                self._iter = 0
                self._pos[0] += randint(-1, 1)
                self._pos[1] += randint(-1, 1)
        self._data['key'] = None
        if self._data.get('d_rad'):
            self._radius += self._data.get('d_rad')
        self._data['key'] = None

    def set_data(self, data):
        self._data = data

    def get_data(self):
        return {'pos': self._pos, 'radius': self._radius, 'color': self._color}


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
    fps = 0.02
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as main_socket:
        main_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        main_socket.bind((HOST, PORT))
        main_socket.setblocking(False)
        main_socket.listen(1)

        player_sockets = []
        player_data = dict()
        for i in range(COUNT):
            pos = [randint(10, WIDTH - 10), randint(10, HEIGHT - 10)]
            radius = randint(5, 20)
            player_data[f"bot{i:03}"] = Player(pos=pos, radius=radius)

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

            # Передача данных игрокам
            data = dict()
            for addr, player in player_data.items():
                data[addr] = player.get_data()
            try:
                data = '#####' + json.dumps({'players': data}) + '%%%%%'
            except Exception as err:
                print('Error prepare to send:', err)
            for sock in player_sockets:
                if not send_data(sock, data):
                    player_sockets.remove(sock)
                    sock.close()
