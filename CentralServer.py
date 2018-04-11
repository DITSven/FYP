import multiprocessing
import threading
import socket
import pickle
import time
import Block

class CentralServer(object):

    def __init__(self, client_list=None, peer_devices=None, peer_id=None):
        manager = multiprocessing.Manager()#For sending information across threads
        #Populate client list, option to use an existing list
        if client_list == None:
            self.client_list = manager.list()
        else:
            self.client_list = manager.list().extend(client_list)
        #List of devices connected to peers, option to use existing list
        if peer_devices == None:
            self.peer_devices = manager.list()
        else:
            self.peer_devices = manager.list().extend(peer_devices)
        #peer count to be shared across threads, option to use existing count
        if peer_id == None:
            self.peer_id = multiprocessing.Value('l', 1)
        else:
            self.peer_id = multiprocessing.Value('l', peer_id)
        #Open blockchain file and load into memory
        with open('blockchain_file.chain', 'rb') as bcf:
            self.blockchain = pickle.load(bcf)
        self.lock = threading.Lock()

    #Check that client is still up and running with exception for connection closing mid-test
    def client_connect_check(self, index):
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = self.client_list[index][1]
        port = self.client_list[index][2]
        try:
            test_result = test_sock.connect((host, port))
            if test_result == 0:
                print("Client not found")
                del self.client_list[index]
            else:
                index = index + 1
        except socket.error:
            print("Socket connection lost")
            del self.client_list[index]
        test_sock.close()
        return index

    #Iterate through clients and run client_connect_check() and amend peer id's
    def test_clients_live(self):
        while True:
            time.sleep(5)
            if len(self.client_list) > 0:
                index = 0
                while True:
                    index = self.client_connect_check(index)
                    if index >= len(self.client_list):
                        break
                for i in range(0, len(self.client_list)):
                    temp_array = [len(self.client_list[:i]) + 1, self.client_list[i][1],self.client_list[i][2]]
                    self.client_list[i] = temp_array
                self.peer_id.value = len(self.client_list) + 1

    #Opens socket to send the peer list to existing peer without addition to list
    def peer_list_update(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #host = socket.gethostname()
        host = '127.0.0.1' #used for local test purposes
        port = 20566
        sock.bind((host, port))
        print("Update Listening")
        sock.listen(5)
        while True:
            connection, address = sock.accept()
            connection.send(b'CONNECTED')
            if (connection.recv(4096).decode() == 'Peer List Request'):
                connection.send(str(len(self.client_list)).encode())
            if (connection.recv(4096).decode() == 'OK'):
                for i in range(0, len(self.client_list)):
                    temp = self.client_list[i]
                    if not temp:
                        connection.send(pickle.dumps('EOL'))
                        break
                    pickled_temp = pickle.dumps(temp)
                    connection.send(pickled_temp)
                    if (connection.recv(4096).decode() == 'Element Received'):
                        pass
                if(connection.recv(4096).decode() == 'List Received'):
                    connection.close()
            else:
                print("Error incorrect code received")
                connection.close()
    
    #Open socket for initial connection by peer and devices
    def listener_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #host = socket.gethostname()
        host = '127.0.0.1' #used for local test purposes
        port = 20560
        sock.bind((host, port))
        print("Listening")
        sock.listen(5)
        while True:
            connection, address = sock.accept()
            print("Socket opened "+str(address))
            connection.send(b'CONNECTED')
            rec = connection.recv(4096).decode()
            if (rec == 'THIS PEER'):
                self.send_peer_list(connection)
            elif(rec == 'THIS DEVICE'):
                self.device_connect(connection)
            else:
                print("Error incorrect code received")
            connection.close()

    #Adds new peer to list and transmits updated list to peer
    def send_peer_list(self, connection):
        self.lock.acquire()
        print("send peer list")
        connection.send(b'HOST REQUEST')
        this_peer_host = connection.recv(4096).decode()
        print("Peer host: "+ this_peer_host)
        connection.send(b'PORT REQUEST')
        this_peer_port = int(connection.recv(4096).decode())
        print("Peer port: " + str(this_peer_port))
        peer_details = [self.peer_id.value, this_peer_host, this_peer_port]
        self.peer_id.value = self.peer_id.value + 1
        self.client_list.append(peer_details)
        connection.send(b'PEER RECEIVED')
        if (connection.recv(4096).decode() == 'Peer List Request'):
            connection.send(str(len(self.client_list)).encode())
        if (connection.recv(4096).decode() == 'OK'):
            for i in range(0, len(self.client_list)):
                temp = self.client_list[i]
                if not temp:
                    connection.send(pickle.dumps('EOL'))
                    break
                pickled_temp = pickle.dumps(temp)
                connection.send(pickled_temp)
                if (connection.recv(4096).decode() == 'Element Received'):
                    pass
            if(connection.recv(4096).decode() == 'List Received'):
                self.send_chain(connection)
            if(connection.recv(4096).decode() == 'Chain Received'):
                self.lock.release()
        else:
            print("Error incorrect code received")
            

    #Connects device to peer
    def device_connect(self, connection):
        print("device connected")
        connection.send(b'PEER SEND')
        if (connection.recv(4096).decode() == 'PEER REQUEST'):
            connection.send(b'DEVICE ID REQ')
        devid = connection.recv(4096).decode()
        isconnected = False
        for i in range(0, len(self.client_list)):
            iscapacity = False
            if not self.client_list[i]:
                print("Send failed")
                connection.send(b'SEND FAIL')
            else:
                if not self.peer_devices:
                    peer_device = {"peer": self.client_list[i][0], "devices": [devid]}
                    self.peer_devices.append(peer_device)
                    connection.send(pickle.dumps(self.client_list[i]))
                    if (connection.recv(4096).decode() == 'PEER RECEIVED'):
                        print("Peer has been received")
                        break
                else:
                    for p in range(0, len(self.peer_devices)):
                        if self.peer_devices[p]["peer"] == self.client_list[i][0]:
                            print("devices connected:", str(self.peer_devices[p]["devices"]))
                            if len(self.peer_devices[p]["devices"]) >= 3:
                                iscapacity = True
                                break
                            if len(self.peer_devices[p]["devices"]) < 3:
                                self.peer_devices[p]["devices"].append(devid)
                                connection.send(pickle.dumps(self.client_list[i]))
                                if (connection.recv(4096).decode() == 'PEER RECEIVED'):
                                    print("Peer has been received")
                                isconnected = True
                                break
                    if isconnected == False and iscapacity == False:
                        peer_device = {"peer": self.client_list[i][0], "devices": [devid]}
                        self.peer_devices.append(peer_device)
                        connection.send(pickle.dumps(self.client_list[i]))
                        if (connection.recv(4096).decode() == 'PEER RECEIVED'):
                            print("Peer has been received")
                        break                

    #Sends complete chain to peer
    def send_chain(self, connection):
        print("Sending chain")
        connection.send(b'CHAIN SEND')
        if (connection.recv(4096).decode() == 'CHAIN OK'):
            connection.send(str(len(self.blockchain)).encode())
        if (connection.recv(4096).decode() == 'CHAIN LENGTH RECEIVED'):
            for i in range(0, len(self.blockchain)):
                temp = self.blockchain[i]
                if not temp:
                    connection.send(pickle.dumps('EOF'))
                    break
                pickled_temp = pickle.dumps(temp)
                connection.send(pickled_temp)
                if (connection.recv(4096).decode() == 'Chain Element Received'):
                    pass
        
    #Defines and starts threads
    def start_server(self):
        server_thread = threading.Thread(target=self.listener_socket, args=())
        test_clients = threading.Thread(target=self.test_clients_live, args=())
        peer_update = threading.Thread(target=self.peer_list_update, args=())
        server_thread.setDaemon(True)
        test_clients.setDaemon(True)
        peer_update.setDaemon(True)
        server_thread.start()
        test_clients.start()
        peer_update.start()
        server_thread.join()
        test_clients.join()
        peer_update.join()

def main():
    s = CentralServer()
    s.start_server()

if __name__ == "__main__":
    main()
