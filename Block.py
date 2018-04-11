class Block(object):
    
    def __init__(self, device_id, device_pswd, commands, previous_hash, block_id, block_hash):
        self.blockid = block_id
        self.device_id = device_id
        self.device_pswd = device_pswd
        self.commands = commands
        self.previous_hash = previous_hash
        self.block_hash = block_hash
       

