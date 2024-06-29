import json
from random import random
import socket
import threading
from time import sleep

clients = {}


def handle_client(client_socket, client_address, n, coeffs):
    client_name = client_socket.recv(1024).decode('utf-8')
    clients[client_name] = client_socket
    print(f"[{client_address}] {client_name} has connected.")

    try:
        while len(clients) < n:
            pass
        message = "S:" + json.dumps(coeffs)
        client_socket.send(message.encode('utf-8'))
        while True:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                print(f"Received message from {client_name}: {message}")
                recipient, msg = message.split(':', 1)
                if recipient in clients:
                    clients[recipient].send(f"{client_name}:{msg}".encode('utf-8'))
                    sleep(0.2)
                else:
                    client_socket.send(f"User {recipient} not found.".encode('utf-8'))
            else:
                break
    except:
        pass

    client_socket.close()
    del clients[client_name]
    print(f"{client_name} has disconnected.")

def start_server(port, n, coeffs):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', port))
    server.listen(5)
    print(f"[*] Listening on 0.0.0.0:{port}")

    while True:
        client_socket, client_address = server.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address, n, coeffs))
        client_handler.start()

if __name__ == "__main__":
    server_port = int(input("Enter the port to listen on: "))
    n = int(input("Number of parties: "))
    coeffs = [int(x) for x in input("Linear combination: ").split(' ')]
    start_server(server_port, n, coeffs)
