#!/usr/bin/env python3
# coding:utf-8
import json
import threading
import time
import zlib
from random import randint
import socket
import schedule

from const import Const

players_in = dict()
players_out = dict()


def random_coord():
    x = 50 * (randint(50, Const.WIDTH - 50) // 50)
    y = 50 * (randint(50, Const.HEIGHT - 50) // 50)
    return x, y


def handle_client(conn, addr, player_out, player_in):
    print(f"NEW CONNECTION {addr} connected.")
    while True:
        try:
            data = conn.recv(Const.data['DATA_WIND']).decode('utf-8')
            print(data)
            if not data:
                break
            command = json.loads(data)
            # with threading.Lock():
            #     player_in['command'] = command
            print(f"{addr}: {command}")

            data = '#####' + json.dumps(command) + '%%%%%'
            z_data = data.encode('utf-8')
            conn.sendall(z_data)
            print(f"[PACKET SIZE]: {len(z_data)} <{data}>")
        except Exception as e:
            print(f"[ERROR] {e}")
            break
    print(f"[DISCONNECTED] {addr} disconnected.")
    conn.close()


def prepare_to_send():
    data = dict()
    data_out = {'body': [300, 300], 'radius': 50, 'color': (255, 0, 0), 'figure': 0, 'length': 1, 'life': 10}
    if len(players_out) > 0:
        for addr, player in players_out.items():
            data[addr] = data_out
    return {'players': data}


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    server.bind((Const.data['HOST'], Const.data['PORT']))
    server.setblocking(False)
    server.listen()
    print(f"[SERVER] Listening on {Const.data['HOST']}:{Const.data['PORT']}")
    return server


def print_stat():
    print('IN: ', players_in)
    print('OUT:', players_out)


if __name__ == "__main__":
    schedule.every(1).second.do(print_stat)
    server = start_server()
    while True:
        try:
            conn, addr = server.accept()
            if conn:
                print(conn)
                players_out[addr[0]] = {"position": random_coord(), "addr": addr, "conn": conn}
                players_in[addr[0]] = dict()
                thread = threading.Thread(target=handle_client,
                                          args=(conn, addr, players_out[addr[0]], players_in[addr[0]]))
                thread.start()
                print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
            server.setblocking(False)
        except BlockingIOError:
            pass

        # dout = prepare_to_send()
        # data = b'#####' + zlib.compress(json.dumps(dout).encode('utf-8')) + b'%%%%%'
        #
        # print(f"[PACKET SIZE]: {len(data)} <{data}>")
        # for addr, player in players_out.items():
        #     conn = player['conn']
        #     try:
        #         player['conn'].sendall(data)
        #     except Exception as e:
        #         print(e)

        schedule.run_pending()
        # time.sleep(2)
