import subprocess

device_name="Sample Device"
host='127.0.0.1'
s_port='20560'

for i in range(0,5):
    filename = "./devices/device-"+str(i)+".json"
    subprocess.Popen(["py", "DGUI.py", device_name, host, s_port, filename])