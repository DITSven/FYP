import multiprocessing
import threading
import socket
import pickle
import time
import random
from hashlib import sha512
from ctypes import c_char_p
from Instruction import Instruction

class Peer(object):

    def __init__(self, host='127.0.0.1', s_port=20560, u_port=20566):
        manager = multiprocessing.Manager()#Allows data to be shared across threads
        self.central_server_host = host
        self.central_server_port = s_port
        self.central_update_port = u_port
        self.peer_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.peer_server_host = multiprocessing.Value(c_char_p, b'')
        self.peer_server_port = multiprocessing.Value('l', 0)
        self.peer_list = manager.list()
        self.device_list = manager.list()
        self.connected_list = manager.list()
        self.own_id = multiprocessing.Value('l', 1)
        self.blockchain = manager.list()
        #self.out_command_cache = manager.list()
        self.out_command_cache = [["9fd4e0b4-fc67-4f2c-b6dd-e9b70f3659a0", "177daa1eb3fbb32464e9a6d4d935fc6cbaf96679f5e6c76fa7152662bb09b01f4804592a3ecbffba3eea6c7e542957de7e72f7569a965d5d928fb9eec123ae13", "green"], ["9fd4e0b4-fc67-4f2c-b6dd-e9b70f3659a0", "84fdaef521eb32f1e80fdfee8bc907bf94c4abc43ec49026df0d4ce90f8cda568ec6ee76fcf33b29f44a66f51ab597f2f1a653bed36899b2766efbf699ebe0d5", "It works!"]]
        self.in_command_cache = manager.list()
        self.lock = threading.Lock()

    #Connects to central server and downloads peer list and blockchain
    def first_connect(self):
        self.lock.acquire()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                sock.connect((self.central_server_host, self.central_server_port))
                break
            except socket.error:
                print('Could not connect socket')
        print("Connected to server")
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
                print("EOF")
                break
            self.blockchain.append(temp_element)
            sock.send(b'Chain Element Received')
        print("chain received")
        sock.send(b'Chain Received')
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()
        self.lock.release()
        for i in self.peer_list:
            print(i)
        print(self.blockchain[0].device_id)

    def update_list(self):
        while True:
            time.sleep(2)
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.central_server_host, self.central_update_port))
                flag = 1
            except socket.error:
                print('Could not connect socket')
                flag = 0
                sock.close()
            if flag == 1:
                if(sock.recv(4096).decode() == 'CONNECTED'):
                    sock.send(b'Peer List Request')
                list_size = int(sock.recv(4096).decode())
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
                sock.shutdown(socket.SHUT_RDWR)
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
                rec = connection.recv(4096).decode()
                if rec == 'PEER':
                    print("Peer Socket accepted " + str(address))
                elif rec == 'DEVICE':
                    print("Device connected")
                    connection.send(b'DEVICE PEER CONNECTED')
                    device_thread= threading.Thread(target=self.device_auth, args=(connection,))
                    device_thread.setDaemon(True)
                    device_thread.start()
            except socket.error:
                print("Socket tested")
                connection.close()
    
    def device_auth(self, connection):
        if(connection.recv(4096).decode() == 'DEV ID SEND'):
            connection.send(b'DEV ID REQ')
        dev_id = connection.recv(4096).decode()
        connection.send(b'DEV PSW REQ')
        dev_psw = connection.recv(4096).decode()
        match = False
        for i in self.blockchain:
            if i.device_id == sha512(dev_id.encode()).hexdigest():
                print("Found device")
                if i.device_pswd == sha512(dev_psw.encode()).hexdigest():
                    print("Authentication accepted")
                    match = True
                    break
                print("Authentication failed")
            print("Not found")
        if match == True:
            self.device_commands_io(connection, dev_id)
            
    def device_commands_io(self, connection, dev_id):
        connection.send(b'COMMAND IO REQ')
        if connection.recv(4096).decode() == 'COMMAND IO ACK':
            while True:
                time.sleep(1)
                self.lock.acquire()
                try:
                    if len(self.out_command_cache) > 0:
                        list_size = len(self.out_command_cache)
                        connection.send(b'INSTRUCTION SEND')
                        if connection.recv(4096).decode() == 'INSTRUCTION ACK':
                            connection.send(str(list_size).encode())
                        if connection.recv(4096).decode() == 'OK':
                            for i in range(0, list_size):
                                temp = []
                                if self.out_command_cache[i][0] == dev_id:
                                    temp = self.out_command_cache[i]
                                if not temp:
                                    connection.send(pickle.dumps('EOL'))
                                    break
                                pickled_temp = pickle.dumps(temp)
                                del temp
                                connection.send(pickled_temp)
                                if connection.recv(4096).decode() == 'COMMAND RECEIVED':
                                    pass
                            if connection.recv(4096).decode() == 'COMMAND LIST RECEIVED':
                                del self.out_command_cache[:list_size]
                                self.lock.release()
                    else:
                        connection.send(b'COMMAND REQ')
                        print("sent comm req")
                        rec = connection.recv(4096).decode()
                        print("received rec")
                        if rec == 'NO COMMAND':
                            pass
                            self.lock.release()
                        else:
                            list_size = int(rec)
                            connection.send(b'COMMAND LENGTH RECEIVED')
                            for i in range(0, list_size):
                                temp_obj = connection.recv(4096)
                                temp_element = pickle.loads(temp_obj)
                                if (temp_element == 'END'):
                                    break
                                temp_com = [dev_id]
                                temp_com.append(temp_element[0])
                                temp_com.append(temp_element[1])
                                self.in_command_cache.append(temp_com)
                                del temp_com
                                connection.send(b'COMMAND RECEIVED')
                                resp = connection.recv(4096).decode()
                                if resp == 'DISCONNECT':
                                    print("Device closing connection (disconnect)")
                                    connection.close()
                                    self.lock.release()
                                    return
                                elif resp == 'OK':
                                    pass
                            connection.send(b'COMMAND LIST RECEIVED')
                            if connection.recv(4096).decode() == 'COMMAND LIST RECEIVED ACK':
                                    pass
                            print(self.in_command_cache)
                            self.lock.release()
                except socket.error:
                    print("Device connection closing (error)")
                    self.lock.release()
                    return
    
    #Connects to peer
    def peer_client_connect(self, host, port):
        is_connected = False
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

    #manages connected peer clients
    def peer_client(self):
        while True:
            time.sleep(3)
            peer_list = list(self.peer_list)
            is_connected = False
            if len(peer_list) > 0:
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
                                if self.peer_server_host.value.decode() != host or self.peer_server_port.value != port:
                                    client_connect = threading.Thread(target=self.peer_client_connect, args=(host, port))
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
                                if self.peer_server_host.value.decode() != host or self.peer_server_port.value != port:
                                    client_connect = threading.Thread(target=self.peer_client_connect, args=(host, port))
                                    client_connect.start()
                                    self.connected_list.append([id, host, port])
                                    if(len(self.connected_list) >= 6):
                                        break

    #quick fibonacci range generator for simple peer load distribution
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
        listener.setDaemon(True)
        listener.start()
        update.setDaemon(True)
        update.start()
        client.setDaemon(True)
        client.start()
        listener.join()
        update.join()
        client.join()
        

def main():
    p = Peer()
    p.start_peer()

if __name__ == "__main__":
    main()
