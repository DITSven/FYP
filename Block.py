import json
from hashlib import sha512
import pickle

class Block(object):
    
    def __init__(self, commands, previous_hash, blockid, block_hash):
        self.blockid = blockid
        self.commands = commands
        self.previous_hash = previous_hash
        self.block_hash = block_hash
       

class BlockChain(Block):

    def __init__(self, filename = 'commands.json', blocksize = 1000):
        self.filename = filename
        self.blocksize = blocksize
        self.commands =  []
        self.blockid = 1
        self.previous_hash = "This is where random input for previous hash goes"
        self.chain = []
        self.create_blockchain()

    #Returns array of commands from commands file
    def open_commands_file(self):
        commands = json.load(open(self.filename, 'rb'))["Commands"]
        return commands

    #Creates unique value for each command for each block
    def alter_commands(self):
        for i in range(0,self.blocksize):
            altered_commands = []
            for c in self.open_commands_file():
                c = sha512(c.encode()).hexdigest()
                altered_commands.append(c) 
            self.commands.append(altered_commands)

    #Creates hash value for block
    def block_hash(self, commands):
        commands_string = (b"")
        for command in commands:
            commands_string += command.encode()
        commands_string += self.previous_hash.encode()
        composite_hash = sha512(commands_string).hexdigest()
        return composite_hash

    #Simple method to create single block
    def create_block(self):
        return Block(self.commands[self.blockid -1], self.previous_hash, self.blockid, self.block_hash(self.commands[self.blockid -1]))

    #Creates list of blocks (blockchain)
    def create_blockchain(self):
        self.alter_commands()
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
    blockchain = BlockChain()
    print(blockchain.chain[0].block_hash + "\n")
    print(blockchain.chain[1].block_hash + "\n")
    print(str(blockchain.chain[2].blockid) + " : " + blockchain.chain[2].commands[1] + "\n")
    print(blockchain.chain[2].previous_hash + "\n")
    print(blockchain.chain[2].block_hash)
    blockchain.write_chain()


if __name__ == "__main__":
    main()


