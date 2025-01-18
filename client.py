#!/usr/bin/env python3
# coding:utf-8
import socket
import json
from threading import Thread


class Client:

    def __init__(self, addr):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.players = []  # Создаем массив для хранения данных об игроках
        self.addr = addr

    def start_session(self) -> bool:
        try:
            self.sock.connect(self.addr)  # подключаемся к айпи адресу сервера
            Thread(target=self.get_players).start()  # Делаем новый поток с циклом, в которым берем данные об игроках
            return True
        except Exception as o:
            print(o)
        return False

    def get_players(self):
        while True:
            self.sock.sendall(bytes(json.dumps({
                "request": "get_players"
            }), 'UTF-8'))  # Отправляем серверу запрос для получения игроков
            received = json.loads(self.sock.recv(1024).decode('UTF-8'))
            self.players = received["response"]  # сохраняем результат запроса в переменную

    def move(self, side):
        self.sock.sendall(bytes(json.dumps({
            "request": "move",
            "move": side
        }), 'UTF-8'))  # Отправляем серверу запрос для получения игроков
