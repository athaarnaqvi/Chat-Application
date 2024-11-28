import socket
import threading


HOST = socket.gethostbyname(socket.gethostname())
PORT = 1210
FORMAT = 'utf-8'
ADDR= (HOST,PORT)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server.bind(ADDR)
print("[SERVER IS LISTENING]....")
server.listen()

clients = []
nicknames = []

def broadcast(message):
    for client in clients:
        try:
            client.send(message)
        except:
            pass  # Handle case where client is disconnected


def handle(client):
    print("Here 2")
    while True:
        try:
            message = client.recv(1024)
            print(f"{nicknames[clients.index(client)]} says {message}")
            broadcast(message)
       
        except:
            index = clients.index(client)
            clients.remove(client)
            client.close()
            nickname = nicknames[index]
            nicknames.remove(nickname)
            break

def receive():
    print("Here 1")
    # print("[SERVER IS LISTENING.....]")
    while True:
        client, address = server.accept()
        print(f"Connected with {str(address)} !")
        
        client.send("NICK".encode(FORMAT))
        nickname = client.recv(1024).decode(FORMAT)
        print(nickname)
        nicknames.append(nickname)
        clients.append(client)
        
        print(f"Nickname of the client is {str(nickname)}")
        broadcast(f"{str(nickname)} connected to the server!\n". encode(FORMAT))
        client.send("Connected to the server".encode(FORMAT))
        
        thread = threading.Thread(target=handle,args=(client,) )
        thread.start()
         
print("[SERVER IS LOADING......]")
receive()