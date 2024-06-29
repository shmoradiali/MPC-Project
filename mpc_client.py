import socket
import threading
import json
import random
from interpolation import interpolate

global instance_count


class MPCClient:

    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.shares = {}
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.number_of_participants = 0
        self.t = 0
        self.secret = 0
        self.prime = 97

    def connect_to_server(self):
        self.client_socket.connect((self.host, self.port))
        threading.Thread(target=self.listen_to_server).start()
        client_address = self.client_socket.getsockname()
        client_ip, client_port = client_address
        self.port = client_port

    def listen_to_server(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                data = json.loads(message)
                self.process_message(data)
            except Exception as e:
                print(f'Error: {e}')
                break

    def process_message(self, data):
        command = data.get('command')
        if command == 'set_number_of_participants':
            self.number_of_participants = data['number']
            self.t = (self.number_of_participants - 1) // 2
        if command == 'receive_share':
            print("received shared of value with id {}. my share is {}.".format(data['id'], data['share']))
            self.shares[data['id']] = data['share']
        elif command == 'add':
            self.add_shares(data['id1'], data['id2'], data['result_id'])
        elif command == 'multiply_step':
            self.handle_multiply_step(data)
        elif command == 'recon':
            self.client_socket.send(json.dumps({'command': 'recon', 'port': self.port,
                                                'share': self.shares[data['id']]}).encode('utf-8'))

    def get_number_of_participants(self):
        self.client_socket.send(json.dumps({'command': 'number_of_participants'}).encode('utf-8'))

    def share_value(self, value=None):
        while self.number_of_participants == 0:
            pass
        if value is None:
            value = self.secret
        # Split the value into shares using Shamir's Secret Sharing
        shares = self.split_into_shares(value, self.t)
        self.client_socket.send(json.dumps({'command': 'share', 'share': shares}).encode('utf-8'))

    def add_shares(self, id1, id2, result_id):
        share1 = self.shares[id1]
        share2 = self.shares[id2]
        self.shares[result_id] = share1 + share2
        print("received shared of value with id {}. my share is {}.".format(result_id, share1 + share2))

    def multiply_shares(self, id1, id2, result_id):
        share1 = self.shares[id1]
        share2 = self.shares[id2]
        result_share = share1 * share2
        self.client_socket.send(
            json.dumps({'command': 'share', 'id': result_id, 'share': result_share}).encode('utf-8'))

    def calculate_polynomial(self, coefficients, x, value):
        shared_value = value
        for i in range(len(coefficients)):
            shared_value += coefficients[i] * (x ** (i + 1)) % self.prime
        return shared_value

    def split_into_shares(self, value, degree):
        # Implement Shamir's Secret Sharing to split the value into shares
        coefficients = self.create_random_polynomial_coeffs(degree)
        shares = []
        for i in range(self.number_of_participants):
            shares.append(self.calculate_polynomial(coefficients, i + 1, value))
        return shares

    def handle_multiply_step(self, data):
        step = data.get('step')
        if step == 'create_polynomials':
            self.create_and_share_random_polynomials(data)
        elif step == 'share_d0':
            self.compute_d_shares(data)
        elif step == 'compute_final_shares':
            self.compute_final_shares(data)

    def create_and_share_random_polynomials(self, data):
        id1 = data['id1']
        id2 = data['id2']
        result_id = data['result_id']
        random_share = random.randint(1, self.prime)
        rt_shares = self.split_into_shares(random_share, self.t)
        new_degree = self.t * 2
        r2t_shares = self.split_into_shares(random_share, new_degree)
        self.client_socket.send(json.dumps(
            {'command': 'multiply_step', 'port': self.port, 'step': 'compute_d_shares', 'rt_shares': rt_shares, 'r2t_shares': r2t_shares,
             'id1': id1, 'id2': id2, 'result_id': result_id}).encode('utf-8'))

    def create_random_polynomial_coeffs(self, degree):
        # Create and return random polynomial shares
        coefficients = [random.randint(1, self.prime) for _ in range(degree)]
        return coefficients

    def compute_d_shares(self, data):
        id1 = data['id1']
        id2 = data['id2']
        result_id = data['result_id']
        # Compute d(i) shares and send to server
        id1 = int(id1)
        id2 = int(id2)
        di_share = self.shares[id1] * self.shares[id2] - data['r2t_share']
        self.client_socket.send(json.dumps(
            {'command': 'multiply_step', 'step': 'share_d0', 'port': self.port, 'rt_share': data['rt_share'],
             'di_share': di_share, 'id1': id1, 'id2': id2, 'result_id': result_id}).encode('utf-8'))

    def compute_final_shares(self, data):
        print("OK")
        id1 = data['id1']
        id2 = data['id2']
        result_id = data['result_id']
        d0 = interpolate(data['di_shares'], self.t, self.prime)
        c_prime_share = data['rt_share'] + d0
        self.shares[result_id] = c_prime_share


if __name__ == "__main__":
    client = MPCClient()
    client.connect_to_server()
    # Example usage
    client.secret = int(input())
    status = ""
    while status != "ok":
        status = input()
    client.get_number_of_participants()
    client.share_value()
