import socket
import sys

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

PORT = 8080
IP = '127.0.0.1'
s.connect((IP, PORT))
msg = s.recv(1024)
print(msg.decode())


while True:
    cmd = input("-> ")
    if cmd == "quit":
        s.close()
        sys.exit()
    elif cmd == "":
        print("INVALID COMMAND")
    else:
        s.send(cmd.encode("utf-8"))
        print(s.recv(2048).decode())
