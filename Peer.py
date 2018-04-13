import threading
import socket
import pickle
import time
import random
import ssl
from hashlib import sha512
from Block import Block

class Peer(object):

    def __init__(self, host='127.0.0.1', s_port=20560, u_port=20566):

        self.central_server_host = host
        self.central_server_port = s_port
        self.central_update_port = u_port
        self.peer_server_host = b''
        self.peer_server_port = 0
        self.peer_list = []
        self.device_list = []
        self.connected_list = []
        self.own_id = 1
        self.blockchain = []
        #self.out_command_cache = []
        self.out_command_cache = [["9fd4e0b4-fc67-4f2c-b6dd-e9b70f3659a0", "177daa1eb3fbb32464e9a6d4d935fc6cbaf96679f5e6c76fa7152662bb09b01f4804592a3ecbffba3eea6c7e542957de7e72f7569a965d5d928fb9eec123ae13", "green"], ["9fd4e0b4-fc67-4f2c-b6dd-e9b70f3659a0", "84fdaef521eb32f1e80fdfee8bc907bf94c4abc43ec49026df0d4ce90f8cda568ec6ee76fcf33b29f44a66f51ab597f2f1a653bed36899b2766efbf699ebe0d5", "It works!"]]
        self.in_command_cache = []
        self.cert_file = "./peercert.pem"
        self.key_file = "./peerkey.pem"
        self.lock = threading.Lock()

    #Connects to central server and downloads peer list and blockchain
    def first_connect(self):
        self.lock.acquire()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        #context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
        conn = context.wrap_socket(sock, server_hostname="ServerFYP")
        while True:
            try:
                conn.connect((self.central_server_host, self.central_server_port))
                break
            except socket.error:
                print('Could not connect socket')
        print("Connected to server")
        if(conn.recv(4096).decode() == 'CONNECTED'):
            print("Received")
        else:
            print("Error wrong code")
        conn.send(b'THIS PEER')
        if(conn.recv(4096).decode() == 'HOST REQUEST'):
            conn.send(self.peer_server_host)
        if(conn.recv(4096).decode() == 'PORT REQUEST'):
            conn.send(str(self.peer_server_port).encode())
        if(conn.recv(4096).decode() == 'PEER RECEIVED'):
            conn.send(b'Peer List Request')
        list_size = int(conn.recv(4096).decode())
        conn.send(b'OK')
        for i in range(0, list_size):
            temp_obj = conn.recv(4096)
            temp_element = pickle.loads(temp_obj)
            if (temp_element == 'EOL'):
                break
            self.peer_list.append(temp_element)
            conn.send(b'Element Received')
        conn.send(b'List Received')
        if(conn.recv(4096).decode() == 'CHAIN SEND'):
            conn.send(b'CHAIN OK')
        chain_size = int(conn.recv(4096).decode())
        conn.send(b'CHAIN LENGTH RECEIVED')
        for i in range(0, chain_size):
            temp_obj = conn.recv(4096)
            temp_element = pickle.loads(temp_obj)
            if (temp_element == 'EOF'):
                print("EOF")
                break
            self.blockchain.append(temp_element)
            conn.send(b'Chain Element Received')
        print("chain received")
        conn.send(b'Chain Received')
        conn.shutdown(socket.SHUT_RDWR)
        conn.close()
        self.lock.release()
        for i in self.peer_list:
            print(i)
        print(self.blockchain[0].device_id)

    def update_list(self):
        while True:
            time.sleep(2)
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                #context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
                conn = context.wrap_socket(sock, server_hostname="ServerFYP")
                conn.connect((self.central_server_host, self.central_update_port))
                flag = 1
            except socket.error:
                print('Could not connect socket')
                flag = 0
                conn.close()
            if flag == 1:
                if(conn.recv(4096).decode() == 'CONNECTED'):
                    conn.send(b'Peer List Request')
                list_size = int(conn.recv(4096).decode())
                conn.send(b'OK')
                self.peer_list[:] = []
                for i in range(0, list_size):
                    temp_obj = conn.recv(4096)
                    temp_element = pickle.loads(temp_obj)
                    if (temp_element == 'EOL'):
                        break
                    self.peer_list.append(temp_element)
                    conn.send(b'Element Received')
                #This loop will be more effective when peers run off different hosts
                for i in range(0, len(self.peer_list)):
                    if self.peer_server_host == self.peer_list[i][1]:
                        if self.peer_server_port == self.peer_list[i][2]:
                            self.own_id = self.peer_list[i][0]
                conn.send(b'List Received')
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()

    #listener for incoming peer connections
    def peer_server_listener(self):
        #self.peer_server_host = socket.gethostname().encode()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.peer_server_host = b'127.0.0.1' #used for local test purposes
        for i in range(30000,40000):
            try:
                sock.bind((self.peer_server_host.decode(), i))
                self.peer_server_port = i
                print("Peer server socket open")
                break
            except socket.error:
                pass
        sock.listen(5)
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile=self.cert_file, keyfile=self.key_file)
        #context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
        context.set_ciphers('EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH')
        self.first_connect()
        while True:
            connection, address = sock.accept()
            conn = context.wrap_socket(connection, server_side=True)
            try:
                rec = conn.recv(4096).decode()
                if rec == 'PEER':
                    print("Peer Socket accepted " + str(address))
                elif rec == 'DEVICE':
                    print("Device connected")
                    conn.send(b'DEVICE PEER CONNECTED')
                    device_thread= threading.Thread(target=self.device_auth, args=(conn,))
                    device_thread.setDaemon(True)
                    device_thread.start()
                elif rec == 'USER COM IN':
                    self.user_connection_in(conn)
                elif rec == 'USER COM OUT':
                    self.user_connection_out(conn)
            except socket.error:
                print("Socket tested")
                conn.close()
    
    def user_connection_out(self, conn):
        conn.send(b'DEVICE ID?')
        devid = conn.recv(4096).decode()
        match = False
        for i in self.blockchain:
            if i.device_id == sha512(devid.encode()).hexdigest():
                commands = i.commands
                break
        for i in self.in_command_cache:
           if i[0] == sha512(devid.encode()).hexdigest():
                tempcache.append(i)
        comlen = len(commands)
        conn.send(str(comlen).encode())
        if conn.recv(4096).decode() == 'COMLEN OK':
            pass
        for i in range(0, comlen):
            temp = commands[i]
            if not temp:
                conn.send(pickle.dumps('EOF'))
                break
            pickled_temp = pickle.dumps(temp)
            conn.send(pickled_temp)
            if (conn.recv(4096).decode() == 'Command Received'):
                pass
        conn.send(b'SEND COMMAND')
        com = conn.recv(4096)
        colourcom = pickle.loads(com)
        print(colourcom)
        self.out_command_cache.append(colourcom)
        conn.send(b'OK')
        com = conn.recv(4096)
        messagecom = pickle.loads(com)
        print(messagecom)
        self.out_command_cache.append(messagecom)
        conn.close()



    def user_connection_in(self, conn):
        tempcache = []
        conn.send(b'DEVICE ID?')
        devid = conn.recv(4096).decode()
        for i in self.blockchain:
            if i.device_id == sha512(devid.encode()).hexdigest():
                print("commands ok")
                commands = i.commands
                break
        for i in self.in_command_cache:
            if i[0] == sha512(devid.encode()).hexdigest():
                tempcache.append(i)
                print(tempcache)
        comlen = len(commands)
        conn.send(str(comlen).encode())
        if conn.recv(4096).decode() == 'COMLEN OK':
            pass
        for i in range(0, comlen):
            temp = commands[i]
            if not temp:
                conn.send(pickle.dumps('EOF'))
                break
            pickled_temp = pickle.dumps(temp)
            conn.send(pickled_temp)
            if (conn.recv(4096).decode() == 'Command Received'):
                pass
        if len(tempcache) < 1:
            conn.send(b'NO CACHE')
            conn.close()
        else:
            conn.send(b'CACHE TO SEND')
            if conn.recv(4096).decode() == 'OK':
                conn.send(str(len(tempcache)).encode())
            if conn.recv(4096).decode() == 'CACHE LEN OK':
                pass
            for i in range(0, len(tempcache)):
                temp = tempcache[i]
                if not temp:
                    conn.send(pickle.dumps('EOF'))
                    break
                pickled_temp = pickle.dumps(temp)
                conn.send(pickled_temp)
                if (conn.recv(4096).decode() == 'Cache element Received'):
                    pass
            conn.close()


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
                                    thread.exit()
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
                    thread.exit()
                    return
    
    #Connects to peer
    def peer_client_connect(self, host, port):
        is_connected = False
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        #context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
        conn = context.wrap_socket(sock, server_hostname="PeerFYP")
        print("Created socket")
        try:
            conn.connect((host, port))
            print("connected socket")
            is_connected = True
        except socket.error:
            print("Socket failed to connect")
        if is_connected:
            if host == self.peer_server_host.decode() and port == self.peer_server_port:
                print("Connected to self")
            conn.send(b'PEER')
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
                                if self.peer_server_host.decode() != host or self.peer_server_port != port:
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
                                if self.peer_server_host.decode() != host or self.peer_server_port != port:
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
