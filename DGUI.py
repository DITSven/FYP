from tkinter import *
import socket
import pickle
import threading
import time
import random
import json
import ssl

class DGUI(object):
    def __init__(self, device_name, host, s_port, name, psw, commands):
        self.central_server_host = host
        self.central_server_port = s_port
        self.device_name = name
        self.device_psw = psw
        self.commands = commands
        self.peer = []
        self.out_command_cache = []
        self.in_command_cache = []
        self.connection = False
        self.window = Tk()
        self.l_frame = Frame(self.window)
        self.r_frame = Frame(self.window)
        self.l_up_frame = Frame(self.l_frame)
        self.l_down_frame = Frame(self.l_frame, width=50, height=50)
        self.window_label = Label(self.window, text=device_name)
        self.message = Label(self.r_frame, text="Message goes here")
        self.rng_label = Label(self.l_up_frame, text="Current Random Number")
        self.colour_label= Label(self.l_down_frame, text="Current Colour:")
        self.connect_label = Label(self.r_frame, text="No Connection Open")
        self.rng_button = Button(self.r_frame, text="Send Random Number", command=self.send_rng)
        self.time_button = Button(self.r_frame, text="Send Time", command=self.send_time)
        self.connect_button = Button(self.r_frame, text="Connect", command=self.change_connect)
        self.colour = Label(self.l_down_frame, bg="red", width=30, height=10)
        self.rng_result = Label(self.l_up_frame, text=str(0))

    #action for send random number button
    def send_rng(self):
        instruction = [self.commands[0], str(self.rng_num)]
        self.out_command_cache.append(instruction)

	#action for send time button
    def send_time(self):
        instruction = [self.commands[1], str(time.asctime())]
        self.out_command_cache.append(instruction) 
    
    #action for connection button
    def change_connect(self):
        if self.connection == False:
            if not self.peer:
                get_peer_thread = threading.Thread(target=self.server_connection(), args=())
                get_peer_thread.setDaemon(True)
                get_peer_thread.start()
                get_peer_thread.join()
            self.connection = True
            connection_thread = threading.Thread(target=self.peer_connection, args=())
            connection_thread.setDaemon(True)
            connection_thread.start()
            instruction = [self.commands[3], "Connected"]
            self.out_command_cache.append(instruction)
            self.connect_label["text"]= "Connected"
            self.connect_button["text"] = "Disconnect"
        elif self.connection == True:
            instruction = [self.commands[3], "Disconnected"]
            self.out_command_cache.append(instruction)
            self.connection = False            
        
    #connect to central server and receive peer data
    def server_connection(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
        conn = context.wrap_socket(sock, server_hostname="ServerFYP")
        try:
            conn.connect((self.central_server_host, self.central_server_port))
        except socket.error:
            print('Could not connect socket')
        print("Connected")
        if(conn.recv(4096).decode() == 'CONNECTED'):
            print("Received")
        else:
            print("Error wrong code")
        conn.send(b'THIS DEVICE')
        if (conn.recv(4096).decode() == 'PEER SEND'):
            conn.send(b'PEER REQUEST')
        if (conn.recv(4096).decode() == 'DEVICE ID REQ'):
            conn.send(self.device_name.encode())
        peer_unpickled = conn.recv(4096)
        self.peer = pickle.loads(peer_unpickled)
        conn.send(b'PEER RECEIVED')
        conn.shutdown(socket.SHUT_RDWR)
        conn.close()

    #connect to peer
    def peer_connection(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
        conn = context.wrap_socket(sock, server_hostname="PeerFYP")
        while True:
            try:
                conn.connect((self.peer[1], self.peer[2]))
                break
            except socket.error:
                print('Could not connect socket')
        print("Connected")
        conn.send(b'DEVICE')
        if(conn.recv(4096).decode() == 'DEVICE PEER CONNECTED'):
            print("Received")
        else:
            print("Error wrong code")
        conn.send(b'DEV ID SEND')
        if(conn.recv(4096).decode() == 'DEV ID REQ'):
            conn.send(self.device_name.encode())
        if(conn.recv(4096).decode() == 'DEV PSW REQ'):
            conn.send(self.device_psw.encode())
        accpt = conn.recv(4096).decode()
        if accpt == 'COMMAND IO REQ':
            self.command_io(conn)
        else:
            print("Device not found")
            conn.shutdown(socket.SHUT_RDWR)
            conn.close()
            self.connection = False
            self.connect_button["text"] = "Connect"
            self.connect_label["text"] = "No Connection Open"

    #run cached commands
    def command_io(self, conn):
        conn.send(b'COMMAND IO ACK')
        while True:
            rec = conn.recv(4096).decode()
            if rec == 'COMMAND REQ':
                print("got command req")
                print(self.out_command_cache)
                if len(self.out_command_cache) < 1:
                    conn.send(b'NO COMMAND')
                    print("sent no command")
                else:
                    conn.send(str(len(self.out_command_cache)).encode())
                    if (conn.recv(4096).decode() == 'COMMAND LENGTH RECEIVED'):
                        list_size = len(self.out_command_cache)
                        for i in range(0, list_size):
                            temp = self.out_command_cache[i]
                            if not temp:
                                conn.send(pickle.dumps('END'))
                                break
                            if temp[1] == "Disconnected":
                                print("doing disconnected")
                                pickled_temp = pickle.dumps(temp)
                                conn.send(pickled_temp)
                                if (conn.recv(4096).decode() == 'COMMAND RECEIVED'):
                                    conn.send(b'DISCONNECT')
                                print("got comm list rec")
                                del self.out_command_cache[:i+1]
                                conn.shutdown(socket.SHUT_RDWR)
                                conn.close()
                                self.connect_button["text"] =  "Connect"
                                self.connect_label["text"] = "No Connection Open"
                                return
                            pickled_temp = pickle.dumps(temp)
                            conn.send(pickled_temp)
                            if (conn.recv(4096).decode() == 'COMMAND RECEIVED'):
                                pass
                        conn.send(b'OK')
                        if (conn.recv(4096).decode() == 'COMMAND LIST RECEIVED'):
                            conn.send(b'COMMAND LIST RECEIVED ACK')
                            print("got comm list rec")
                            del self.out_command_cache[:list_size]
            elif rec == 'INSTRUCTION SEND':
                conn.send(b'INSTRUCTION ACK')
                list_size = int(conn.recv(4096).decode())
                conn.send(b'OK')
                for i in range(0, list_size):
                    temp_obj = conn.recv(4096)
                    temp_element = pickle.loads(temp_obj)
                    if (temp_element == 'EOL'):
                        break
                    self.in_command_cache.append(temp_element)
                    conn.send(b'COMMAND RECEIVED')
                conn.send(b'COMMAND LIST RECEIVED')
            

    #runs commands received 
    def run_commands(self):
        while True:
            if self.in_command_cache:
                instruction = self.in_command_cache[0]
                if instruction[1] == self.commands[3]:
                    print("Changing colour")
                    self.colour["bg"] = instruction[2]
                    del self.in_command_cache[0]
                if instruction[1] == self.commands[4]:
                    print("Changing text")
                    self.message["text"] = instruction[2]
                    del self.in_command_cache[0]

    #produce random number for display and sending
    def rng_thread(self):
        while True:
            time.sleep(6)
            self.rng_num = random.randrange(0, 40000)
            self.rng_result["text"] = str(self.rng_num)

	#load GUI elements into window and start RNG thread
    def load_window(self):
        self.window_label.pack(side=TOP, fill=X)
        self.l_frame.pack(side=LEFT, fill=BOTH, expand=True)
        self.r_frame.pack(side=RIGHT)
        self.l_up_frame.pack(fill=BOTH)
        self.l_down_frame.pack(fill=BOTH, expand=True)
        self.message.pack(side=TOP)
        self.rng_button.pack(side=TOP)
        self.time_button.pack(side=TOP)
        self.connect_button.pack(side=TOP)
        self.connect_label.pack(side=BOTTOM)
        self.rng_label.pack()
        self.colour_label.pack()
        self.colour.pack(fill=BOTH, expand=True)
        self.rng_result.pack()
        rng_thread = threading.Thread(target=self.rng_thread, args=())
        rng_thread.setDaemon(True)
        rng_thread.start()
        run_commands_thread = threading.Thread(target=self.run_commands, args=())
        run_commands_thread.setDaemon(True)
        run_commands_thread.start()
        self.window.mainloop()

def main():
    with open('./devices/device-0.json', 'rb') as df:
        openjsonfile = json.load(df)
    #with open(sys.argv[4], 'rb') as df:
        #openjsonfile = json.load(df)
    name = openjsonfile["device"]
    pswd = openjsonfile["pswd"]
    commands = openjsonfile["commands"]
    #dg = DGUI(device_name=sys.argv[1], host=sys.argv[2], s_port=int(sys.argv[3]), name=name, psw=pswd, commands=commands)
    dg = DGUI(device_name="Sample Device", host='localhost', s_port=20560, name=name, psw=pswd, commands=commands)
    print(sys.argv[0])
    dg.load_window()

if __name__=="__main__":
	main()