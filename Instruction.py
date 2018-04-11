import time

class Instruction(object):
    
    def __init__(self, peer_id, device, user, command=None, command_data=None, ttl=None, datetime=time.time()):
        self.peer_id = peer_id
        self.device = device
        self.user = user
        self.command = command
        self.command_data = response
        self.ttl = ttl
        self.datetime = datetime
