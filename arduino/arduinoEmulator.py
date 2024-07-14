import socket
import time
import re
import os

# Function to read server and port from config.h
def read_config(config_file_path):
    server = ''
    server_port = 0

    server_re = re.compile(r'const char\* server = "(.*)";')
    server_port_re = re.compile(r'const int serverPort = (\d+);')

    with open(config_file_path, 'r') as file:
        for line in file:
            server_match = server_re.search(line)
            server_port_match = server_port_re.search(line)

            if server_match:
                server = server_match.group(1)

            if server_port_match:
                server_port = int(server_port_match.group(1))
    # Output the parsed values
    print(f'Server: {server}')
    print(f'Server Port: {server_port}')
    return server, server_port

# Path to the config.h file
config_file_path = './config_example.h'
server, server_port = read_config(config_file_path)

# Initialize TCP client
def connect_to_server():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((server, server_port))
        print("Connected to server")
        return client
    except Exception as e:
        print(f"Failed to connect to server: {e}")
        return None

def send_data(client, message):
    try:
        client.sendall(message.encode('utf-8'))
        print(f"Sent: {message}")
    except Exception as e:
        print(f"Failed to send data: {e}")
        print("Attempting to connect to server...")
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        time.sleep(1) # avoid overflooding the server
        send_data(client, message)

def emulate_arduino():
    client = connect_to_server()
    if client is None:
        print("Failed to connect to server...Quitting Program...")
        return
    while True:
        message = input("Enter the sensor data to send: ")
        send_data(client, message)

if __name__ == "__main__":
    emulate_arduino()
