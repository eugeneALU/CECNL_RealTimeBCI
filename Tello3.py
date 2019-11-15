# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 10:10:36 2019

@author: ALU
@ref : http://www.ryzerobotics.com/
"""
import threading 
import socket
import platform

host = ''
port = 9000
locaddr = (host,port) 

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

tello_address = ('192.168.10.1', 8889) # specified in manual

sock.bind(locaddr)

def recv():
    while True: 
        try:
            data, server = sock.recvfrom(1518)
            print(data.decode(encoding="utf-8"))
        except Exception:
            print ('\nExit . . .\n')
            break


print ('\r\n\r\nTello Python3 Demo.\r\n')

print ('Tello: command takeoff land flip forward back left right\r\n\
       up down cw ccw speed speed?\r\n')

print ('end -- quit demo.\r\n')


#recvThread create
recvThread = threading.Thread(target=recv)
recvThread.setDaemon(True)
recvThread.start()

while True:  
    # Need to send 'command' at first and recieve correct response(ok)
    msg = 'command'.encode(encoding="utf-8") 
    sent = sock.sendto(msg, tello_address)
    try:
        python_version = str(platform.python_version())
        version_init_num = int(python_version.partition('.')[0]) 

        if version_init_num == 3:
            msg = input("")
        elif version_init_num == 2:
            msg = raw_input("")
        
        if not msg:
            break  

        if 'end' in msg:
            print ('...')
            sock.close()  
            break

        # Send data
        msg = msg.encode(encoding="utf-8") 
        sent = sock.sendto(msg, tello_address)
    except KeyboardInterrupt:
        print ('\n . . .\n')
        sock.close()  
        break




