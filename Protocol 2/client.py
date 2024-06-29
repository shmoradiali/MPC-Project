from lib2to3.pgen2 import token
from random import random
from re import T
import socket
import threading
import json
from time import sleep
from computation import Circuit, lin_comb
from secret_sharing import make_shares, recover_secret


m = 1013
p = 2027
g = 199
base_port = 27199
 
protocol_started = False
blacklist = set()
reported = set()
saved_commits = {}
reported_by = {}
valid_shares = {}
final_shares = []
C = None

def receive_messages(client_socket, client_id, n):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            print("Got this " + message)
            if message:
                if message[0] == 'S':
                    global protocol_started
                    protocol_started = True
                    coeffs = json.loads(message.split(':')[1])
                    global C
                    C = lin_comb(coeffs, n)
                else:
                    tokens = message.split(':')
                    from_client = int(tokens[0])
                    if tokens[1] == "commit":
                        target = int(tokens[2])
                        print(f"Received commitment for {target} from client {from_client}.")
                        commits = json.loads(tokens[3])
                        saved_commits[target] = commits
                    elif tokens[1] == "share":
                        target = int(tokens[2])
                        print(f"Received share of {target} from client {from_client}.")
                        share = int(tokens[3])
                        print("hmmmmm ", share, target)
                        res = 1
                        for i in range(len(saved_commits[target])):
                            res = (res * saved_commits[target][i]**(client_id**i)) % p
                        if (g**share % p) != res:
                            blacklist.add(from_client)
                            valid_shares[target] = 0 # Defaults to zero when adversary sends bad share
                            print("Share was corrupted!")
                        else:
                            valid_shares[target] = share
                            print("Share was valid.")
                    elif tokens[1] == "complaint":
                        target = int(tokens[2])
                        if target not in reported_by:
                            reported_by[target] = {from_client}
                        else:
                            reported_by[target].add(from_client)
                        if len(reported_by[target]) > n // 3:
                            blacklist.add(target)
                    elif tokens[1] == "fin":
                        share = (from_client, int(tokens[2]))
                        final_shares.append(share)
            else:
                print("None")
                break
        except Exception as e:
            print(e)
            break
    client_socket.close()


def start_client(server_ip, server_port, n, client_id, secret):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, server_port))
    client.send(str(client_id).encode('utf-8'))

    receive_thread = threading.Thread(target=receive_messages, args=(client, client_id, n))
    receive_thread.start()

    while not protocol_started:
        pass
    print(f"Protocol starts.")

    t = 2 * (n // 3)
    shares, coeffs = make_shares(secret, n, t, m)
    print("My polynomial is: ", coeffs)
    commits = [(g**x % p) for x in coeffs]

    for i, s_i in shares:
        if i != client_id:
            message = f"{i}:commit:{client_id - 1}:" + json.dumps(commits)
            client.send(message.encode('utf-8'))
            sleep(1 - random()/2)
    
    print("Sent commits.")
    sleep(1 - random())
    
    for i, s_i in shares:
        if i != client_id:
            message = f"{i}:share:{client_id - 1}:{s_i}"
            print("Gonna send " + message)
            client.send(message.encode('utf-8'))
            sleep(1.2 - random()/3)
        else:
            valid_shares[i - 1] = s_i
    
    while len(valid_shares) < n:
        pass

    sleep(1.3 - random())

    for i in blacklist.difference(reported):
        for j in range(1, n + 1):
            if j != client_id:
                message = f"{j}:complaint:{i}"
                client.send(message.encode('utf-8'))
                sleep(2 - random()*3/2)
        reported.add(i)
    
    vals = []
    for i in range(n):
        vals.append(valid_shares[i])
    fin_share = C.compute(vals)

    for i in range(1, n + 1):
        if i != client_id:
            message = f"{i}:fin:{fin_share}"
            client.send(message.encode('utf-8'))
            sleep(1.7 - random()*4/3)
    
    while len(final_shares) < t:
        pass

    output = recover_secret(final_shares, m)
    print(f"The result of copmutation is: {output}")

    client.close()


if __name__ == "__main__":
    server_ip = "0.0.0.0"
    server_port = int(input("Server port: "))
    n = int(input("Number of parties: "))
    client_id = int(input("Client ID: "))
    secret = int(input(f"Client {client_id}'s secret: "))
    print("Starting client...")
    start_client(server_ip, server_port, n, client_id, secret)
    print("Done.")
