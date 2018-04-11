from  Block import Block
import pickle

with open('blockchain_file.chain', 'rb') as bcf:
    blockchain = pickle.load(bcf)

for i in blockchain:
    if i.blockid > 1:
        break
    print(i.commands)