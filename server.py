import socket
import threading
import tkinter as tk
from tkinter import messagebox

HOST = socket.gethostbyname(socket.gethostname())
PORT = 1210
FORMAT = 'utf-8'
ADDR = (HOST, PORT)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(ADDR)

clients = []
nicknames = []
client_counter = 0
lock = threading.Lock()

print("[SERVER IS LISTENING]...")
server.listen()

def broadcast(message):
    for client in clients:
        try:
            client.send(message)
        except:
            pass

def handle(client):
    global client_counter
    while True:
        try:
            message = client.recv(1024)
            if not message:
                raise ConnectionResetError
            print(f"{nicknames[clients.index(client)]} says {message.decode(FORMAT)}")
            broadcast(message)
        except:
            with lock:
                if client in clients:
                    index = clients.index(client)
                    nickname = nicknames.pop(index)
                    clients.pop(index)
                    client_counter -= 1
                    print(f"{nickname} disconnected. Active clients: {client_counter}")
            client.close()
            if client_counter == 0:
                print("[SERVER SHUTTING DOWN] No clients connected.")
                server.close()
                break
            break

def remove_client(nickname):
    global client_counter  # Make sure we modify the global counter
    with lock:
        try:
            index = nicknames.index(nickname)
            client = clients.pop(index)
            nicknames.pop(index)
            client_counter -= 1
            broadcast(f"{nickname} has been removed by the admin\n".encode(FORMAT))
            client.send("You have been removed by the admin.".encode(FORMAT))
            print(f"Removed {nickname} from the chat.")
            client.close()  # Close the client socket here
        except ValueError:
            print(f"Client {nickname} not found.")


def receive():
    global client_counter
    print("[SERVER IS LOADING]...")
    while True:
        try:
            client, address = server.accept()
            print(f"Connected with {str(address)}!")
            client.send("NICK".encode(FORMAT))
            nickname = client.recv(1024).decode(FORMAT)

            with lock:
                nicknames.append(nickname)
                clients.append(client)
                client_counter += 1
                print(f"Nickname of the client: {nickname}. Active clients: {client_counter}")

            broadcast(f"{nickname} connected to the server!\n".encode(FORMAT))
            client.send("Connected to the server.".encode(FORMAT))

            thread = threading.Thread(target=handle, args=(client,))
            thread.start()

        except OSError:
            break

def server_gui():
    window = tk.Tk()
    window.title("Server Admin Panel")

    client_listbox = tk.Listbox(window, width=40, height=10)
    client_listbox.pack(padx=20, pady=20)

    def update_client_list():
        client_listbox.delete(0, tk.END)
        for client in nicknames:
            client_listbox.insert(tk.END, client)

    def remove_selected_client():
        selected = client_listbox.curselection()
        if selected:
            nickname = client_listbox.get(selected)
            remove_client(nickname)
            update_client_list()
        else:
            messagebox.showwarning("No selection", "Please select a client to remove.")

    remove_button = tk.Button(window, text="Remove Client", command=remove_selected_client)
    remove_button.pack(padx=20, pady=5)

    update_button = tk.Button(window, text="Update Client List", command=update_client_list)
    update_button.pack(padx=20, pady=5)

    update_client_list()

    window.mainloop()

# Start the server and GUI
thread = threading.Thread(target=receive)
thread.start()

server_gui()
