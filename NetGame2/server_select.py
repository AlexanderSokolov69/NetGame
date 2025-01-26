#!/usr/bin/env python3
# coding:utf-8
import socket
import select


def handle(sock, addr):
    try:
        data = sock.recv(1024)  # Should be ready
    except ConnectionError:
        print(f"Client suddenly closed while receiving {addr}")
        return False
    print(f"Received {data} from: {addr}")
    if not data:
        print("Disconnected by", addr)
        return False
    data = data.upper()
    print(f"Send: {data} to: {addr}")
    try:
        sock.send(data)  # Hope it won't block
    except ConnectionError:
        print(f"Client suddenly closed, cannot send")
        return False
    return True


HOST, PORT = '127.0.0.1', 5055
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as main_socket:
    main_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    main_socket.bind((HOST, PORT))
    main_socket.setblocking(False)
    main_socket.listen(1)

    inputs = [main_socket]
    outputs = []
    while True:
        readable, writeable, exceptional = select.select(inputs,
                                                         outputs,
                                                         inputs)
        for sock in readable:
            if sock == main_socket:
                new_socket, addr = main_socket.accept()
                inputs.append(new_socket)
                print('Connection from:', addr)
            else:
                addr = sock.getpeername()
                if not handle(sock, addr):
                    inputs.remove(sock)
                    if sock in outputs:
                        outputs.remove(sock)
                    sock.close()
        try:
            new_socket, addr = main_socket.accept()
            player_sockets.append((new_socket, addr))
            print('Connection from:', addr)
        except BlockingIOError:
            pass
        for sock, addr in player_sockets.copy():
            try:
                data = sock.recv(1024)
            except ConnectionError:
                print('Disconnected and removed from:', addr)
                player_sockets.remove((sock, addr))
                sock.close()
                continue
            except BlockingIOError:
                continue