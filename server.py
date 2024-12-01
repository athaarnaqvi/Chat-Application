import socket
import threading
import tkinter
from tkinter import messagebox

# Server configuration
HOST = socket.gethostbyname(socket.gethostname())
PORT = 1210
FORMAT = 'utf-8'
ADDR = (HOST, PORT)

# Initialize server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(ADDR)

clients = []
nicknames = []
lock = threading.Lock()

print("[SERVER IS LISTENING]...")
server.listen()

# Broadcast message to all connected clients
def broadcast(message):
    with lock:
        for client in clients[:]:
            try:
                client.send(message)
            except Exception as e:
                #print(f"Error broadcasting to client: {e} \n")
                index = clients.index(client)
                nickname = nicknames.pop(index)
                clients.remove(client)
                print(f"Removed {nickname} from the client list.\n")
    # Check if no clients are left
    if len(clients) == 0:
        print("No more clients. Closing the server.\n")
        server.close()

# Handle messages from a single client
def handle(client):
    while True:
        try:
            message = client.recv(1024).decode(FORMAT)
            if not message:
                raise ConnectionResetError

            nickname = nicknames[clients.index(client)]
            print(f"{nickname} says: {message}")
            broadcast(message.encode(FORMAT))
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            with lock:
                if client in clients:
                    index = clients.index(client)
                    nickname = nicknames.pop(index)
                    clients.remove(client)
                    print(f"{nickname} disconnected.")
            break

# Accept or reject client connection via GUI
def decision_window(client_socket, nickname):
    def create_rounded_button(master, text, command, bg_color, hover_color):
        button = tkinter.Button(master, text=text, command=command, relief="raised", fg="white", bg=bg_color, font=("Helvetica", 8))
        button.config(borderwidth=3, padx=10, pady=5)
        button.bind("<Enter>", lambda e: button.config(bg=hover_color))
        button.bind("<Leave>", lambda e: button.config(bg=bg_color))
        return button

    def accept_client():
        client_socket.send("ACCEPT".encode(FORMAT))
        with lock:
            nicknames.append(nickname)
            clients.append(client_socket)
        broadcast(f"{nickname} has joined the chat!\n".encode(FORMAT))
        threading.Thread(target=handle, args=(client_socket,)).start()
        root.destroy()

    def reject_client():
        client_socket.send("REJECT".encode(FORMAT))
        client_socket.close()
        root.destroy()

    # GUI for accepting or rejecting a client
    root = tkinter.Tk()
    root.title("Client Request")
    message = tkinter.Label(root, text=f"Do you accept {nickname} to join the chat?")
    message.pack()

    accept_button = create_rounded_button(root, "Accept", accept_client, "#4CAF50", "#45a049")  # Green for accept
    accept_button.pack(padx=20, pady=5)

    reject_button = create_rounded_button(root, "Reject", reject_client, "#FF5733", "#FF8C66")  # Red for reject
    reject_button.pack(padx=20, pady=5)

    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()

# Function to accept client connections
def receive():
    while True:
        try:
            client, address = server.accept()
            print(f"Connected with {str(address)}!")
            request_message = client.recv(1024).decode(FORMAT)

            if request_message.startswith("REQUEST:"):
                nickname = request_message.split(":")[1]
                threading.Thread(target=decision_window, args=(client, nickname), daemon=True).start()
        except OSError:
            break

# Remove a client from the chat
def remove_client(nickname):
    with lock:
        try:
            index = nicknames.index(nickname)
            client = clients[index]
            client.send("You have been removed by the admin.".encode(FORMAT))
            client.close()
            nicknames.pop(index)
            clients.pop(index)
            print(f"{nickname} removed.")
        except ValueError:
            print(f"{nickname} not found.")
    broadcast(f"{nickname} has been removed by the admin.\n".encode(FORMAT))

# Admin panel GUI for managing clients
def server_gui():
    def create_rounded_button(master, text, command, bg_color, hover_color):
        button = tkinter.Button(master, text=text, command=command, relief="raised", fg="white", bg=bg_color, font=("Helvetica", 10))
        button.config(borderwidth=3, padx=10, pady=5)
        button.bind("<Enter>", lambda e: button.config(bg=hover_color))
        button.bind("<Leave>", lambda e: button.config(bg=bg_color))
        return button

    window = tkinter.Tk()
    window.title("Server Admin Panel")

    client_listbox = tkinter.Listbox(window, width=40, height=10)
    client_listbox.pack(padx=20, pady=20)

    def update_client_list():
        client_listbox.delete(0, tkinter.END)
        for client in nicknames:
            client_listbox.insert(tkinter.END, client)

    client_listbox.config(selectmode="single", font=("Helvetica", 10), bg="#f0f8ff", fg="black")

    def remove_selected_client():
        selected = client_listbox.curselection()
        if selected:
            nickname = client_listbox.get(selected)
            threading.Thread(target=remove_client, args=(nickname,)).start()
            update_client_list()
        else:
            messagebox.showwarning("No selection", "Please select a client to remove.")

    remove_button = create_rounded_button(window, "Remove Client", remove_selected_client, "#FF5733", "#FF8C66")  # Red for remove
    remove_button.pack(padx=20, pady=5)

    update_button = create_rounded_button(window, "Update Client List", update_client_list, "#4CAF50", "#45a049")  # Green for update
    update_button.pack(padx=20, pady=5)

    update_client_list()
    window.mainloop()

# Start the server GUI and begin receiving clients
threading.Thread(target=server_gui, daemon=True).start()
receive()
