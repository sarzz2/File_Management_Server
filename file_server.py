import socket
import os
import shutil
from os import path
import threading
import json

Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

PORT = 8080
Socket.bind(('127.0.0.1', PORT))
Socket.listen(10)


class Server:
    def __init__(self):
        self.cmd = ""
        self.all_connections = []
        self.all_address = []
        self.login_data = self.load_login_data()
        self.admin_users = self.load_admins()
        self.login_validation = {}
        self.auth = {}
        self.auth_ip_user = {}
        self.user_name = []
        self.users_current_directory = {}
        self.logged_in_users = []

    # set up the connection
    def connections(self):
        while True:
            try:
                conn, addr = Socket.accept()
                conn.setblocking(True)
                conn.sendall(
                    "Please login to continue. Syntax: login <user> <password>,".encode("utf-8"))
                self.all_connections.append(conn)
                self.all_address.append(addr)
                print("Connection has been established :" + addr[0])
                t1 = threading.Thread(target=self.run_client_always, args=[conn, addr], daemon=True)
                t1.start()
            except Exception as e:
                print(e)
                print("Error accepting connections")
                break

    def run_client_always(self, conn, addr):
        while True:
            try:
                self.server(conn, addr)
            except Exception as e:
                if addr in self.auth.keys():
                    self.logged_in_users.remove(self.auth_ip_user[addr])
                    del self.auth[addr]
                    del self.auth_ip_user[addr]
                    del self.users_current_directory[addr]

    # List of all commands => help
    def commands(self, conn):
        data = ("change_folder <name>:                       "
                "Move the current working directory\n"
                "ls:                                         "
                "Displays all files & folders in current directory\n"
                "read <name>:                                "
                "Reads the file <name> in the current working directory\n"
                "write <name> <input>:                       "
                "Write data in <input> in current directory\n"
                "mkdir <name>:                               "
                "Create a new folder with the <name> in the current directory\n"
                "edit <name> <input>:                        "
                "Edits the file\n"
                "register <username> <password> <privileges>:"
                "Registers a new user"
                "to the server using the <username> and <password> provided\n"
                "login <username> <password>:                "
                "Log in the user conforming with <username>\n"
                "delete <username> <password>:"
                "Delete the user conforming with <username> from the server\n"
                "del <input>:                           ""deletes a directory\n"
                "mv <filename>:"                        "Move file to the server")
        return conn.sendall(data.encode("utf-8"))

    def load_login_data(self):
        with open("user.json") as json_file:
            return json.load(json_file)

    def load_admins(self):
        with open("priveleges.json") as json_file:
            return json.load(json_file)['users']

    # login function => login user password
    def login(self, conn, addr, user, passwor):
        if user in list(self.login_data["users"].keys()):
            if passwor == self.login_data["users"][user]:
                if user not in self.logged_in_users:
                    self.auth[addr] = True
                    self.auth_ip_user[addr] = user
                    self.user_name = user
                    self.logged_in_users.append(user)
                    self.users_current_directory[addr] = user + "/"
                    return conn.sendall("Login successful".encode("utf-8"))
                return conn.sendall("User already logged in".encode("utf-8"))
            return conn.sendall("Invalid password".encode("utf-8"))
        return conn.sendall("Invalid username".encode("utf-8"))

    # register function => register username password privilege
    def register(self, conn, user, passwor, priv):
        if user in list(self.login_data["users"].keys()):
            return conn.sendall("Username already taken".encode("utf=8"))
        with open("user.json") as json_file:
            users = json.load(json_file)
        users["users"][user] = passwor
        with open("user.json", 'w') as outfile:
            if user in list(self.login_data["users"].keys()):
                return conn.sendall("Username already taken".encode("utf=8"))
            json.dump(users, outfile)
            os.mkdir(user)
        if priv == "admin":
            with open("priveleges.json") as priv_file:
                admins = json.load(priv_file)
            admins["users"].append(user)
            with open("priveleges.json", "w") as priv_file:
                json.dump(admins, priv_file)
        elif priv == "user":
            pass
        self.login_data = self.load_login_data()
        self.admin_users = self.load_admins()
        return conn.sendall("User created".encode("utf-8"))

    def receive(self, conn):
        self.cmd = conn.recv(2048)
        return self.cmd.decode()

    # list all files in current directory => ls
    def list(self, conn, addr):
        msg = ""
        if path.exists(path.join(self.users_current_directory[addr])):
            f = os.listdir(path.join(self.users_current_directory[addr]))
            for entry in f:
                msg += entry + '\n'
            if msg != "":
                return conn.sendall(msg.encode("utf-8"))
            return conn.sendall("Directory empty".encode("utf-8"))

    # Create a new directory => mkdir dir_name
    def mkdir(self, conn, addr, d):
        try:
            pa = path.join(self.users_current_directory[addr], d)
            os.mkdir(pa)
            return conn.sendall(f"{d} created".encode("utf-8"))
        except:
            return conn.sendall(f"{d} already exists".encode("utf-8"))

    # read a file => read filename
    def read_file(self, conn, addr, com):
        if path.exists(path.join(self.users_current_directory[addr], com)):
            f = open(path.join(self.users_current_directory[addr], com), "r")
            return conn.sendall(f.read(100).encode("utf-8"))
        return conn.sendall(f"{com} does not exist".encode("utf-8"))

    # create a file => write file_name file_content
    def create_file(self, conn, addr, com, file):
        if path.exists(path.join(self.users_current_directory[addr], com)):
            return conn.sendall(f"{com} already exists".encode("utf-8"))
        f = open(path.join(self.users_current_directory[addr], com), "w")
        f.write(file)
        f.close()
        return conn.sendall("created".encode("utf-8"))

    def edit_file(self, conn, addr, file, com):
        f = open(path.join(self.users_current_directory[addr], com), "w")
        f.write(com)
        f.close()
        return conn.sendall(f"{file} edited".encode("utf-8"))

    # delete a user(admin only) => delete username password
    def delete(self, conn, addr, user, passwor):
        if user in list(self.login_data["users"].keys()):
            if passwor == self.login_data["users"][user]:
                if self.auth_ip_user[addr] in self.admin_users:
                    del self.login_data["users"][user]
                    with open("user.json", 'w') as outfile:
                        json.dump(self.login_data, outfile)
                    with open("priveleges.json") as json_file:
                        admins = json.load(json_file)
                    if user in admins["users"]:
                        admins["users"].remove(user)
                        with open("priveleges.json", 'w') as outfile:
                            json.dump(admins, outfile)
                    del self.auth[addr]
                    del self.auth_ip_user[addr]
                    shutil.rmtree(user)
                    return conn.sendall(f"{user} deleted".encode("utf-8"))
            return conn.sendall("Wrong password".encode("utf-8"))
        return conn.sendall("Wrong username".encode("utf-8"))

    # delete a directory => del_dir dir_name
    def delete(self, conn, addr, file):
        try:
            pa = path.join(self.users_current_directory[addr], file)
            if os.path.isfile(pa):
                os.remove(pa)
                return conn.sendall(f"{pa} deleted".encode("utf-8"))
            else:
                os.rmdir(pa)
            return conn.sendall(f"{pa} deleted".encode("utf-8"))
        except FileNotFoundError:
            return conn.sendall(f"{file} doesn't exist".encode("utf-8"))

    # change the current working directory => cd directory
    def cd(self, conn, addr, d):
        if path.exists(path.join(self.users_current_directory[addr], d)):
            self.users_current_directory[addr] += d + "/"
            if d == "..":
                self.users_current_directory[addr] = self.auth_ip_user[addr]
                return conn.sendall(f"In {self.users_current_directory[addr]}".encode("utf-8"))
            elif d == '.':
                return conn.sendall("directory doesn't exist".encode("utf-8"))
            return conn.sendall(f"In {self.users_current_directory[addr]}".encode("utf-8"))
        else:
            return conn.sendall("directory doesn't exist".encode("utf-8"))

    # copies the file in your system to cwd => mv filename
    def mv(self, conn, file, addr):
        invalid = ["user.json","priveleges.json","file_server.py","file_client.py"]
        if file not in invalid:
            try:
                shutil.copy(file, self.users_current_directory[addr])
            except FileNotFoundError:
                return conn.sendall("File Not Found".encode("utf-8"))
            return conn.sendall("File successfully uploaded".encode("utf-8"))
        else:
            return conn.sendall("Invalid".encode("utf-8"))

    # main function
    def server(self, conn, addr):
        command = self.receive(conn).rstrip()
        # if logged in
        if addr in self.auth.keys():
            if self.auth[addr]:
                if command == "ls":
                    self.list(conn, addr)
                elif command.split(" ")[0] == "mkdir":
                    if len(command.split(" ")) == 2:
                        self.mkdir(conn, addr, command.split(" ")[1])
                    else:
                        return conn.sendall("Invalid arguments".encode("utf-8"))
                elif command.split(" ")[0] == "cd":
                    if len(command.split(" ")) == 2:
                        self.cd(conn, addr, command.split(" ")[1])
                    else:
                        return conn.sendall("Invalid arguments".encode("utf-8"))
                elif command.split(" ")[0] == "read":
                    if len(command.split(" ")) == 2:
                        if "/" not in command.split(" ")[1]:
                            self.read_file(conn, addr, command.split(" ")[1])
                        else:
                            return conn.sendall("File doesn't exist".encode("utf-8"))
                    else:
                        return conn.sendall("Invalid arguments".encode("utf-8"))
                elif command.split(" ")[0] == "write":
                    if len(command.split(" ")) == 3:
                        if "/" not in command.split(" ")[1]:
                            self.create_file(conn, addr, command.split(" ")[1], "".join(command.split(" ")[2:]))
                        else:
                            return conn.sendall("Invalid location".encode("utf-8"))
                    else:
                        return conn.sendall("Invalid arguments".encode("utf-8"))
                elif command.split(" ")[0] == "edit":
                    if len(command.split(" ")) == 3:
                        self.edit_file(conn, addr, command.split(" ")[1], "".join(command.split(" ")[2:]))
                    else:
                        return conn.sendall("Invalid arguments".encode("utf-8"))
                elif command == "logout":
                    if addr in self.auth.keys():
                        self.logged_in_users.remove(self.auth_ip_user[addr])
                        del self.auth[addr]
                        del self.auth_ip_user[addr]
                        del self.users_current_directory[addr]
                        return conn.sendall("Logged out".encode("utf-8"))

                elif command.split(" ")[0] == "mv":
                    if len(command.split(" ")) == 2:
                        self.mv(conn, command.split(" ")[1], addr)
                    else:
                        return conn.sendall("Invalid arguments".encode("utf-8"))
                elif command.split(" ")[0] == "del":
                    if len(command.split(" ")) == 2:
                        self.delete(conn, addr, command.split(" ")[1])
                    else:
                        return conn.sendall("Invalid arguments".encode("utf-8"))

                # admin commands
                elif self.user_name in self.admin_users:
                    if command.split(" ")[0] == "delete":
                        if len(command.split(" ")) == 3:
                            self.delete(conn, addr, command.split(" ")[1], command.split(" ")[2])
                        else:
                            return conn.sendall("Invalid arguments".encode("utf-8"))

                    else:
                        return conn.sendall("Wrong command".encode("utf-8"))
                else:
                    return conn.sendall("Wrong command".encode("utf-8"))
            else:
                conn.sendall("Login again".encode("utf-8"))

        # if not logged in
        elif command == "help":
            self.commands(conn)
        elif command.split(" ")[0] == "login":
            if len(command.split(" ")) == 3:
                self.login(conn, addr, command.split(" ")[1], command.split(" ")[2])
            else:
                return conn.sendall("Invalid arguments".encode("utf-8"))
        elif command.split(" ")[0] == "register":
            if len(command.split(" ")) == 4:
                self.register(conn, command.split(" ")[1], command.split(" ")[2], command.split(" ")[3])
            else:
                return conn.sendall("Invalid arguments".encode("utf-8"))
        else:
            return conn.sendall("Invalid command. Please login to continue".encode("utf-8"))



OBJ = Server()
OBJ.connections()
