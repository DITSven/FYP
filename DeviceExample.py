import socket
import pickle
import threading

class DeviceExample(object):

    def __init__(self, host='127.0.0.1', s_port=20560, name="9fd4e0b4-fc67-4f2c-b6dd-e9b70f3659a0", psw="9969b5e8-06fe-4f87-8861-6951ef7c09c8"):
        self.central_server_host = host
        self.central_server_port = s_port
        self.device_name = name
        self.device_psw = psw
        self.peer = []
        
    def server_connection(self):
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
        sock.send(b'THIS DEVICE')
        if (sock.recv(4096).decode() == 'PEER SEND'):
            sock.send(b'PEER REQUEST')
        peer_unpickled = sock.recv(4096)
        self.peer = pickle.loads(peer_unpickled)
        sock.send(b'PEER RECEIVED')
        sock.close()
        
    def peer_connection(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((self.peer[1], self.peer[2]))
        except socket.error:
            print('Could not connect socket')
        print("Connected")
        sock.send(b'DEVICE')
        if(sock.recv(4096).decode() == 'DEVICE PEER CONNECTED'):
            print("Received")
        else:
            print("Error wrong code")
        sock.send(b'DEV ID SEND')
        if(sock.recv(4096).decode() == 'DEV ID REQ'):
            sock.send(self.device_name.encode())
        if(sock.recv(4096).decode() == 'DEV PSW REQ'):
            sock.send(self.device_psw.encode())
        accpt = sock.recv(4096).decode()
        if accpt == 'COMMAND REQ':
            self.command_io(sock)
        else:
            print("Device not found")
            
    def command_io(self, sock):
        sock.send(b'COMMAND 1')
        if(sock.recv(4096).decode() == 'OK'):
            sock.send(b'COMMAND 4')
        
    def device_threads(self):
        server_conn = threading.Thread(target=self.server_connection, args=())
        peer_conn = threading.Thread(target=self.peer_connection, args=())
        server_conn.start()
        server_conn.join()
        peer_conn.start()

def main():
    d = DeviceExample()
    d.device_threads()
    
if __name__ == "__main__":
    main()