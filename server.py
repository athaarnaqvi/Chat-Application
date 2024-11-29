import socket
import threading

HOST = socket.gethostbyname(socket.gethostname())
PORT = 1210
FORMAT = 'utf-8'
ADDR = (HOST, PORT)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(ADDR)

clients = []
nicknames = []
client_counter = 0  # Initialize the counter with 0
lock = threading.Lock()  # To ensure thread-safe operations on the counter

print("[SERVER IS LISTENING]...")
server.listen()

def broadcast(message):
    for client in clients:
        try:
            client.send(message)
        except:
            pass  # Handle case where a client is disconnected

def handle(client):
    global client_counter
    while True:
        try:
            message = client.recv(1024)
            if not message:  # Empty message indicates disconnection
                raise ConnectionResetError
            print(f"{nicknames[clients.index(client)]} says {message.decode(FORMAT)}")
            broadcast(message)
        except:
            # Remove the client and its nickname
            with lock:
                index = clients.index(client)
                clients.pop(index)
                nickname = nicknames.pop(index)
                client_counter -= 1
                print(f"{nickname} disconnected. Active clients: {client_counter}")
                
                # Broadcast that the user left the chat
                #broadcast(f"{nickname} has left the chat.".encode(FORMAT))
            
            client.close()
            
            # Check if the counter is 0 to shut down the server
            if client_counter == 0:
                print("[SERVER SHUTTING DOWN] No clients connected.")
                server.close()
                break
            
            break

def receive():
    global client_counter
    print("[SERVER IS LOADING]...")
    while True:
        try:
            client, address = server.accept()
            print(f"Connected with {str(address)}!")
            
            # Ask for the client's nickname
            client.send("NICK".encode(FORMAT))
            nickname = client.recv(1024).decode(FORMAT)
            
            # Add the client and its nickname
            with lock:
                nicknames.append(nickname)
                clients.append(client)
                client_counter += 1
                print(f"Nickname of the client: {nickname}. Active clients: {client_counter}")
            
            # Notify other clients and the new client
            broadcast(f"{nickname} connected to the server!\n".encode(FORMAT))
            client.send("Connected to the server.".encode(FORMAT))
            
            # Start a thread to handle the client
            thread = threading.Thread(target=handle, args=(client,))
            thread.start()
        except OSError:
            # Server socket might be closed if client_counter reaches 0
            break

receive()
