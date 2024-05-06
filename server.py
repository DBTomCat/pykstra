import socket
import threading
from requests import get
# Dictionary to store connected clients and their code names
clients = {}

def handle_client(server_socket, data, address):
    print(f'[*] Accepted connection from {address[0]}:{address[1]}')

    # Decode the received data
    decoded_data = data.decode('utf-8')

    # Split the data into command and code name
    command, code_name = decoded_data.split(',', 1)

    # Handle loopback
    response_ip = address[0]
    if response_ip == '127.0.0.1' : 
        response_ip = get('https://api.ipify.org').content.decode('utf8')

    if command.strip() == "HELLO":
        if code_name in clients:
            # If the code name already exists in the dictionary, it means two users have the same code name
            print(f"[*] Binding {response_ip}:{address[1]} and {clients[code_name][0]}:{clients[code_name][2]} with Code name '{code_name}'.")

            # Send a response to both clients
            resp = f'SERVER:{response_ip}:{address[1]}'
            server_socket.sendto(resp.encode('utf-8'), clients[code_name][1:])
            resp = f'SERVER:{clients[code_name][0]}:{clients[code_name][2]}'
            server_socket.sendto(resp.encode('utf-8'), address)

            del clients[code_name]

        else:
            # If the code name doesn't exist in the dictionary, add it along with the client socket
            clients[code_name] = response_ip, address[0], address[1]

    else:
        print("[*] Invalid command received.")


def start_server(host, port):
    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the socket to the host and port
    server_socket.bind((host, port))

    # Listen for incoming connections
    # server_socket.listen(5)
    print(f'[*] Listening on {host}:{port}')

    try:
        while True:
            # Accept a connection from a client
            # client_socket, address = server_socket.accept()
            data, addr = server_socket.recvfrom(1024)
            # Create a new thread to handle the client
            if data:
                client_handler = threading.Thread(target=handle_client, args=(server_socket, data, addr))
                client_handler.start()

    except KeyboardInterrupt:
        print('[*] Server shutting down.')
        server_socket.close()

if __name__ == "__main__":
    HOST = '0.0.0.0'  # localhost
    PORT = 3371       # Arbitrary non-privileged port

    start_server(HOST, PORT)
