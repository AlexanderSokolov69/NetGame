#!/usr/bin/env python3
# coding:utf-8
import json
import threading
import zlib
from random import randint
import socket

from const import Const

players = dict()


def random_coord():
    x = 50 * (randint(50, Const.WIDTH - 50) // 50)
    y = 50 * (randint(50, Const.HEIGHT - 50) // 50)
    return x, y


def handle_client(conn, addr):
    print(f"NEW CONNECTION {addr} connected.")
    players[addr[0]] = {"position": random_coord()}
    while True:
        try:
            data = conn.recv(Const.data['DATA_WIND']).decode('utf-8')
            if not data:
                break
            command = data.split()
            print(f"{addr}: {command}")

            data = '#####' + json.dumps(players) + '%%%%%'
            z_data = zlib.compress(data.encode('utf-8'))
            conn.sendall(z_data)
            print(f"[PACKET SIZE]: {len(z_data)} <{data}>")
        except Exception as e:
            print(f"[ERROR] {e}")
            break
    print(f"[DISCONNECTED] {addr} disconnected.")
    del players[addr[0]]
    conn.close()


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((Const.data['HOST'], Const.data['PORT']))
    server.listen()
    print(f"[SERVER] Listening on {Const.data['HOST']}:{Const.data['PORT']}")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")


if __name__ == "__main__":
    start_server()
