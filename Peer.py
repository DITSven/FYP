import multiprocessing
import threading
import socket
import pickle
import time
from ctypes import c_char_p

class Peer(object):

    def __init__(self, host='127.0.0.1', s_port=20560, u_port=20566):
        manager = multiprocessing.Manager()
        self.central_server_host = host
        self.central_server_port = s_port
        self.central_update_port = u_port
        self.peer_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.peer_server_host = multiprocessing.Value(c_char_p, b'')
        self.peer_server_port = multiprocessing.Value('l', 0)
        self.peer_list = manager.list()
        self.connected_list = manager.list()
        self.own_id = multiprocessing.Value('l', 1)
        self.lock = multiprocessing.Lock()
        self.blockchain = []

    def first_connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((self.central_server_host, self.central_server_port))
        except socket.error:
            print('Could not connect socket')
        print("Connected")
        if(sock.recv(4096).decode() == 'CONNECTED'):
            print("Received")
        else:
            print("Error wrong code")
        sock.send(b'THIS PEER')
        if(sock.recv(4096).decode() == 'HOST REQUEST'):
            sock.send(self.peer_server_host.value)
        if(sock.recv(4096).decode() == 'PORT REQUEST'):
            sock.send(str(self.peer_server_port.value).encode())
        if(sock.recv(4096).decode() == 'PEER RECEIVED'):
            sock.send(b'Peer List Request')
        list_size = int(sock.recv(4096).decode())
        sock.send(b'OK')
        for i in range(0, list_size):
            temp_obj = sock.recv(4096)
            temp_element = pickle.loads(temp_obj)
            if (temp_element == 'EOL'):
                break
            self.peer_list.append(temp_element)
            sock.send(b'Element Received')
        sock.send(b'List Received')
        if(sock.recv(4096).decode() == 'CHAIN SEND'):
            sock.send(b'CHAIN OK')
        chain_size = int(sock.recv(4096).decode())
        sock.send(b'CHAIN LENGTH RECEIVED')
        for i in range(0, chain_size):
            temp_obj = sock.recv(4096)
            temp_element = pickle.loads(temp_obj)
            if (temp_element == 'EOF'):
                break
            self.blockchain.append(temp_element)
            print("block received")
            sock.send(b'Chain Element Received')
        print("chain received")
        sock.send(b'Chain Received')
        sock.close()
        for i in self.peer_list:
            print(i)
        print(self.blockchain[0].device_id)

    def update_list(self):
        lock = self.lock
        while True:
            time.sleep(6)
            
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.central_server_host, self.central_update_port))
                flag = 1
            except socket.error:
                print('Could not connect socket')
                flag = 0
                sock.close()
            if flag == 1:
                print("Connected")
                if(sock.recv(4096).decode() == 'CONNECTED'):
                    sock.send(b'Peer List Request')
                list_size = int(sock.recv(4096).decode())
                print(list_size)
                sock.send(b'OK')
                self.peer_list[:] = []
                for i in range(0, list_size):
                    temp_obj = sock.recv(4096)
                    temp_element = pickle.loads(temp_obj)
                    if (temp_element == 'EOL'):
                        break
                    self.peer_list.append(temp_element)
                    sock.send(b'Element Received')
                #This loop will be more effective when peers run off different hosts
                for i in range(0, len(self.peer_list)):
                    if self.peer_server_host == self.peer_list[i][1]:
                        if self.peer_server_port == self.peer_list[i][2]:
                            self.own_id.value = self.peer_list[i][0]
                sock.send(b'List Received')
                sock.close()

    def peer_server_listener(self):
        #self.peer_server_host.value = socket.gethostname().encode()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.peer_server_host.value = b'127.0.0.1' #used for local test purposes
        for i in range(30000,40000):
            try:
                sock.bind((self.peer_server_host.value.decode(), i))
                self.peer_server_port.value = i
                print("Peer server socket open")
                break
            except socket.error:
                pass
        sock.listen(5)
        self.first_connect()
        while True:
            connection, address = sock.accept()
            
            try:
                if connection.recv(4096).decode() == 'PEER':
                    print("Peer Socket accepted " + str(address))
                    
            except socket.error:
                print("Socket tested")
                connection.close()
            
            
    def peer_client_connect(self, host, port):
        lock = self.lock
        print("opened thread")
        is_connected = False
        print("lock acquired")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Created socket")
        try:
            sock.connect((host, port))
            print("connected socket")
            is_connected = True
        except socket.error:
            print("Socket failed to connect")
        if is_connected:
            if host == self.peer_server_host.value.decode() and port == self.peer_server_port.value:
                print("Connected to self")
            sock.send(b'PEER')
            print("Peer Client Connected" + host + " " + str(port))

    def peer_client(self):
        lock = self.lock
        while True:
            time.sleep(8)
            peer_list = list(self.peer_list)
            is_connected = False
            if len(self.connected_list) < 6:
                connected_list = list(self.connected_list)
                if(len(peer_list) < 14):
                    for i in range(0,len(peer_list)):
                        if connected_list:
                            for j in range(0,len(connected_list)):
                                if connected_list[j] == peer_list[i]:
                                    is_connected = True
                                    break
                        if not is_connected:
                            id, host, port = peer_list[i][0], peer_list[i][1], peer_list[i][2]
                            if self.peer_server_host.value.decode() != host or self.peer_server_port.value != port:#not working
                                client_connect = threading.Thread(name='peer_client_connect', target=self.peer_client_connect, args=(host, port))
                                client_connect.start()
                                client_connect.join()
                                self.connected_list.append([id, host, port])
                                print(self.connected_list)
                                if(len(self.connected_list) >= 6):
                                    break

                if(len(peer_list) > 13):
                    fib_numbers = fibonacci_function(6 - len(connected_list))
                    for i in range(0,6):
                        j = len(peer_list) - fib_numbers[i]
                        if len(connected_list) > 0:
                            for k in range(0,len(connected_list)):
                                if connected_list[k] == peer_list[j]:
                                    is_connected = True
                                    print("It's connected already")
                                    break
                        if not is_connected:
                            id, host, port = peer_list[i][0], peer_list[i][1], peer_list[i][2]
                            if self.peer_server_host.value.decode() != host or self.peer_server_port.value != port:#not working
                                client_connect = threading.Thread(name='peer_client_connect', target=self.peer_client_connect, args=(host, port))
                                client_connect.start()
                                self.connected_list.append([id, host, port])
                                if(len(self.connected_list) >= 6):
                                    break


    def fibonacci_function(i):
        a, b = 1, 1
        l = []
        while i > 0:
            a, b = b, a + b
            i -= 1
            l.append(a)
            return l
            
            
    def start_peer(self):
        listener = threading.Thread(target=self.peer_server_listener, args=())
        update = threading.Thread(target=self.update_list, args=())
        client = threading.Thread(target=self.peer_client, args=())
        listener.start()
        update.start()
        client.start()
        listener.join()
        update.join()
        client.join()

def main():
    p = Peer()
    p.start_peer()

if __name__ == "__main__":
    main()
