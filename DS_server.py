import socket
import threading

# Конфигурация сервера
HOST = '127.0.0.1'
PORT = 5555

# Игровой мир (пока просто сетка)
world = [[0 for _ in range(10)] for _ in range(10)]  # 0 - пусто, 1 - блок

# Список подключённых игроков
players = {}

# Обработка клиента
def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    players[addr] = {"position": [0, 0]}  # Начальная позиция игрока

    while True:
        try:
            data = conn.recv(1024).decode('utf-8')
            if not data:
                break

            # Обработка команд от игрока (например, движение)
            command = data.split()
            if command[0] == "move":
                direction = command[1]
                if direction == "up":
                    players[addr]["position"][1] -= 1
                elif direction == "down":
                    players[addr]["position"][1] += 1
                elif direction == "left":
                    players[addr]["position"][0] -= 1
                elif direction == "right":
                    players[addr]["position"][0] += 1

            # Отправка обновлённого состояния мира и игроков
            conn.sendall(f"{world}\n{players}".encode('utf-8'))

        except Exception as e:
            print(f"[ERROR] {e}")
            break

    print(f"[DISCONNECTED] {addr} disconnected.")
    del players[addr]
    conn.close()

# Запуск сервера
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER] Listening on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

if __name__ == "__main__":
    start_server()
    