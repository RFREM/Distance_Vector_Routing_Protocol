import socket
import threading
import subprocess

subprocess.call('start DVR_C1.py', shell=True)
subprocess.call('start DVR_C2.py', shell=True)
subprocess.call('start DVR_C3.py', shell=True)
subprocess.call('start DVR_C4.py', shell=True)

hostname=socket.gethostname()   
IPAddrGET=socket.gethostbyname(hostname) 

ServerName = (hostname)
SERVER_ADDR = (IPAddrGET, 4545)