import json
from hashlib import sha512
import pickle
import sys
from Block import Block

class BlockChain(Block):

    def __init__(self, commands_file = 'commands.json', devices_file = 'devices.json', blocksize = 1000):
        self.commands_file = commands_file
        self.devices_file = devices_file
        self.blocksize = blocksize
        self.commands =  []
        self.devices = []
        self.devices_unhashed = []
        self.block_id = 1
        self.previous_hash = "This is where random input for previous hash goes"
        self.chain = []
        self.no_device_commands = 5
        self.create_blockchain()

    #Returns array of commands from commands file
    def open_commands_file(self):
        commands = json.load(open(self.commands_file, 'rb'))["commands"]
        return commands
        
    #Return array of device details from devices file
    def open_devices_file(self):
        with open(self.devices_file, 'rb') as df:
            self.devices_unhashed = json.load(df)["devices"]
        for d in self.devices_unhashed:
            device_id = sha512(d["id"].encode()).hexdigest()
            device_pswd = sha512(d["pswd"].encode()).hexdigest()
            device_dict = {"id": device_id, "pswd": device_pswd}
            self.devices.append(device_dict)
            

    #Creates unique value for each command for each block
    def alter_commands(self):
        for i in range(0,self.blocksize):
            altered_commands = []
            for c in self.open_commands_file():
                if i < len(self.devices):
                    c = sha512(c.encode() + self.devices[i]["id"].encode()).hexdigest()
                    altered_commands.append(c)
                else:
                    print(len(self.devices))
                    c = sha512(c.encode()).hexdigest()
                    altered_commands.append(c)
                    self.no_device_commands += 1
                    print("Commands without device added:", str(self.no_device_commands))
            fname = "./devices/device-" + str(i) + ".json"
            temp_dict  = {"device": self.devices_unhashed[i]["id"], "pswd": self.devices_unhashed[i]["pswd"], "commands": altered_commands}
            with open(fname, 'w', encoding='utf-8') as df:
                json.dump(temp_dict, df)
            self.commands.append(altered_commands)

    #Creates hash value for block
    def block_hash(self, commands, id, pswd):
        hash_string = (b"")
        device_id_string = id.encode()
        device_pswd_string = pswd.encode()
        hash_string += device_id_string
        hash_string += device_pswd_string
        for command in commands:
            hash_string += command.encode()
        hash_string += self.previous_hash.encode()
        composite_hash = sha512(hash_string).hexdigest()
        return composite_hash

    #Simple method to create single block
    def create_block(self):
        return Block(self.devices[self.block_id - 1]["id"], self.devices[self.block_id - 1]["pswd"], self.commands[self.block_id -1], self.previous_hash, self.block_id, 
                     self.block_hash(self.commands[self.block_id -1], self.devices[self.block_id - 1]["id"], self.devices[self.block_id - 1]["pswd"]))

    #Creates list of blocks (blockchain)
    def create_blockchain(self):
        self.open_devices_file()
        self.alter_commands()
        for i in range(0, self.blocksize):
            block = self.create_block()
            self.chain.append(block)
            self.previous_hash = block.block_hash
            self.block_id += 1
   
    #Writes generated blockchain to disk
    def write_chain(self):
        out_file = open('blockchain_file.chain', 'wb')
        pickle.dump(self.chain, out_file)
        out_file.close()


def main():
    try:
        blockchain = BlockChain(blocksize = int(sys.argv[1]))
    except IndexError:
        blockchain = BlockChain()
    blockchain.write_chain()


if __name__ == "__main__":
    main()


