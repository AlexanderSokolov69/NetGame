#!/usr/bin/env python3
# coding:utf-8
import socket
import time
import json


HOST, PORT = '', 5056
DATA_WIND = 1024

class Player:
    def __init__(self):
        self._pos = [200, 200]
        self._radius = 1
        self._data = None
        self._step = 0

    def prepare(self):
        cmd = self._data.get('key')
        self._step = self._data.get('step', self._step)
        if 'left' in cmd:
            self._pos[0] -= self._step
        if 'right' in cmd:
            self._pos[0] += self._step
        if 'down' in cmd:
            self._pos[1] += self._step
        if 'up' in cmd:
            self._pos[1] -= self._step
        self._data['key'] = None
        if self._data.get('d_rad'):
            self._radius += self._data.get('d_rad')
        self._data['key'] = None

    def set_data(self, data):
        self._data = data

    def get_data(self):
        return {'pos': self._pos, 'radius': self._radius}


def handle(sock: socket.socket) -> any:
    data = None
    addr = ('', 0)
    try:
        data = sock.recv(DATA_WIND).decode()  # Should be ready
        addr = sock.getpeername()
    except ConnectionError:
        print(f"Client suddenly closed while receiving {addr}")
        return None
    except BlockingIOError:
        pass
    except Exception as e:
        print('Error:', e)
    if not data:
        print("Disconnected by", addr)
        return None
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
    fps = 0.01
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as main_socket:
        main_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        main_socket.bind((HOST, PORT))
        main_socket.setblocking(False)
        main_socket.listen(1)

        player_sockets = []
        player_data = dict()
        print('Server started at:', HOST, PORT)
        # Игровой цикл
        clock = time.time()
        while True:
            time_pause = fps - (time.time() - clock)
            if time_pause > 0:
                time.sleep(time_pause)
            else:
                print(time_pause, fps)
            clock = time.time()
            try:
                new_socket, addr = main_socket.accept()
                main_socket.setblocking(False)
                player_sockets.append(new_socket)
                player_data[addr[0]] = player_data.get(addr[0], Player())
                print('Connection from:', addr)
            except BlockingIOError:
                pass

            # Получаем данные от игроков
            # player_data.clear()
            for sock in player_sockets.copy():
                data = handle(sock)
                if not data:
                    player_sockets.remove(sock)
                    sock.close()
                else:
                    try:
                        data = json.loads(data)
                        addr = sock.getpeername()
                        # print('Received from:', addr, data)
                    except json.JSONDecodeError:
                        data = dict()
                    player_data[addr[0]].set_data(data)
                    # Обработка активности
                    player_data[addr[0]].prepare()

            # Игровая механика
            for socket in player_sockets:
                pass

            # Передача данных игрокам
            data = dict()
            for addr, value in player_data.items():
                data[addr] = value.get_data()
            try:
                data = json.dumps({'players': data})
            except:
                print('error')
            for sock in player_sockets:
                if not send_data(sock, data):
                    player_sockets.remove(sock)
                    sock.close()
                # else:
                #     try:
                #         addr = sock.getpeername()
                #         print(addr[0], data)
                #     except:
                #         pass
