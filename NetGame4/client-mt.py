#!/usr/bin/env python3
# coding:utf-8
import json
import random
import socket
import time

from const import Const


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    # client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    print(f"Подключение к серверу: {Const.data['HOST']}:{Const.data['PORT']}")
    client.connect((Const.data['HOST'], Const.data['PORT']))
    while True:
        cmd = {"cmd": random.choice(['left', 'right'])}
        client.sendall(json.dumps(cmd).encode('utf-8'))
        data = client.recv(Const.data['DATA_WIND'])

        print(cmd)
        print(data)

        time.sleep(2)
