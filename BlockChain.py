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
        self.blockid = 1
        self.previous_hash = "This is where random input for previous hash goes"
        self.chain = []
        self.create_blockchain()

    #Returns array of commands from commands file
    def open_commands_file(self):
        commands = json.load(open(self.commands_file, 'rb'))["commands"]
        return commands
        
    #Return array of device details from commands file
    def open_devices_file(self):
        with open(self.devices_file, 'rb') as df:
            devices = json.load(df)["devices"]
        for d in devices:
            device_id = sha512(d["id"].encode()).hexdigest()
            device_pswd = sha512(d["pswd"].encode()).hexdigest()
            device_dict = {"id": device_id, "pswd": device_pswd}
            self.devices.append(device_dict)
            

    #Creates unique value for each command for each block
    def alter_commands(self):
        for i in range(0,self.blocksize):
            altered_commands = []
            for c in self.open_commands_file():
                c = sha512(c.encode()).hexdigest()
                altered_commands.append(c)
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
        return Block(self.devices[self.blockid - 1]["id"], self.devices[self.blockid - 1]["pswd"], self.commands[self.blockid -1], self.previous_hash, self.blockid, self.block_hash(self.commands[self.blockid -1], self.devices[self.blockid - 1]["id"], self.devices[self.blockid - 1]["pswd"]))

    #Creates list of blocks (blockchain)
    def create_blockchain(self):
        self.alter_commands()
        self.open_devices_file()
        for i in range(0, self.blocksize):
            block = self.create_block()
            self.chain.append(block)
            self.previous_hash = block.block_hash
            self.blockid += 1
   
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


