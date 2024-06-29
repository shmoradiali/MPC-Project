import socket
import threading
import json
from interpolation import interpolate


class MPCServer:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.clients = []
        self.shares = {}
        self.value_id = 0
        self.client_dic = {}
        self.known_rt_shares = {}
        self.known_di_shares = {}
        self.prime = 97

    def get_new_value_id(self):
        self.value_id += 1
        return self.value_id

    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        print(f'Server started on {self.host}:{self.port}')

        threading.Thread(target=self.command_listener).start()

        while True:
            client_socket, client_address = server_socket.accept()
            client_ip, client_port = client_address
            print(f'Connection from {client_address}')
            self.clients.append(client_socket)
            self.client_dic[client_port] = len(self.clients)
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                data = json.loads(message)
                self.process_message(data, client_socket)
            except Exception as e:
                print(f'Error: {e}')
                break

    def process_message(self, data, client_socket):
        command = data.get('command')
        if command == 'number_of_participants':
            client_socket.send(json.dumps({'command': 'set_number_of_participants',
                                           'number': len(self.clients)}).encode('utf-8'))
        if command == 'share':
            current_id = self.get_new_value_id()
            self.shares[current_id] = data['share']
            self.distribute_shares(current_id, data['share'])
        elif command == 'add':
            self.broadcast(client_socket, data)
        elif command == 'multiply_step':
            self.handle_multiply_step(data)
        elif command == 'recon':
            client_number = data['port']
            self.known_di_shares[self.client_dic[client_number]] = data['share']
            if len(self.known_di_shares) == len(self.clients):
                final_di_shares = []
                for i in range(1, len(self.clients) + 1):
                    final_di_shares.append(self.known_di_shares[i])
                print(interpolate(final_di_shares, len(self.clients) - 1, self.prime))
                self.known_rt_shares = {}
                self.known_di_shares = {}

    def distribute_shares(self, value_id, share):
        for i, client in enumerate(self.clients):
            client.send(json.dumps({'command': 'receive_share', 'id': value_id, 'share': share[i]}).encode('utf-8'))

    def broadcast(self, sender_socket, data):
        for client in self.clients:
            if client != sender_socket:
                client.send(json.dumps(data).encode('utf-8'))

    def command_listener(self):
        while True:
            command = input("Enter command (add/multiply/reconstruct): ").strip()
            if command == 'add':
                self.handle_add_command()
            elif command == 'multiply':
                self.handle_multiply_command()
            elif command == 'reconstruct':
                self.handle_reconstruct_command()

    def handle_reconstruct_command(self):
        id1 = int(input("Enter first value ID: ").strip())
        self.broadcast(None, {'command': 'recon', 'id': id1})

    def handle_add_command(self):
        id1 = int(input("Enter first value ID: ").strip())
        id2 = int(input("Enter second value ID: ").strip())
        result_id = self.get_new_value_id()
        self.broadcast(None, {'command': 'add', 'id1': id1, 'id2': id2, 'result_id': result_id})

    def handle_multiply_command(self):
        id1 = input("Enter first value ID: ").strip()
        id2 = input("Enter second value ID: ").strip()
        result_id = self.get_new_value_id()
        self.broadcast(None, {'command': 'multiply_step', 'step': 'create_polynomials', 'id1': id1, 'id2': id2,
                              'result_id': result_id})

    def distribute_rshares(self, id1, id2, result_id, rt_shares, r2t_shares):
        for i, client in enumerate(self.clients):
            client.send(json.dumps({'command': 'multiply_step', 'step': 'share_d0',
                                    'id1': id1, 'id2': id2, 'result_id': result_id,
                                    'rt_share': rt_shares[i], 'r2t_share': r2t_shares[i]}).encode('utf-8'))

    def handle_multiply_step(self, data):
        step = data.get('step')
        if step == 'create_polynomials':
            self.broadcast(None, {'command': 'multiply_step', 'step': 'create_polynomials', 'id1': data['id1'],
                                  'id2': data['id2'], 'result_id': data['result_id']})
        elif step == 'compute_d_shares':
            client_number = data['port']
            self.known_rt_shares[self.client_dic[client_number]] = data['rt_shares']
            self.known_di_shares[self.client_dic[client_number]] = data['r2t_shares']
            if len(self.known_di_shares) == len(self.clients):
                final_rt_shares = [0 for i in range(len(self.clients))]
                final_r2t_shares = [0 for i in range(len(self.clients))]
                for client, rt_share in self.known_rt_shares.items():
                    for i in range(len(self.clients)):
                        final_rt_shares[i] += rt_share[i]

                for client, r2t_share in self.known_di_shares.items():
                    for i in range(len(self.clients)):
                        final_r2t_shares[i] += r2t_share[i]
                self.known_rt_shares = {}
                self.known_di_shares = {}
                self.distribute_rshares(data['id1'], data['id2'], data['result_id'], final_rt_shares, final_r2t_shares)
        elif step == 'share_d0':
            client_number = data['port']
            self.known_rt_shares[self.client_dic[client_number]] = data['rt_share']
            self.known_di_shares[self.client_dic[client_number]] = data['di_share']
            if len(self.known_di_shares) == len(self.clients):
                final_di_shares = []
                for i in range(1, len(self.clients) + 1):
                    final_di_shares.append(self.known_di_shares[i])
                for i, client in enumerate(self.clients):
                    client.send(json.dumps({'command': 'multiply_step',
                                            'id1': data['id1'], 'id2': data['id2'],
                                            'result_id': data['result_id'], 'step': 'compute_final_shares',
                                            'di_shares': final_di_shares,
                                            'rt_share': self.known_rt_shares[i + 1]}).encode("utf-8"))
                self.known_rt_shares = {}
                self.known_di_shares = {}


if __name__ == "__main__":
    server = MPCServer()
    server.start_server()
