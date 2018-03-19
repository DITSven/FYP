import uuid
import sys
import json

class DeviceGen():
        
    def __init__(self):
        self.data = {}
        self.data['devices'] = []
        
    def generate(self, x):
        for i in range(0,x):
            id = str(uuid.uuid4())
            psw = str(uuid.uuid4())
            device = { 'id': id, 'pswd': psw }
            self.data['devices'].append(device)
        with open('devices.json', 'w+') as f:
                json.dump(self.data, f)
        
def main():
    d = DeviceGen()
    d.generate(int(sys.argv[1]))
    
if __name__ == '__main__':
    main()