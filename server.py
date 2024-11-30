import socket
import threading
import tkinter
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
    """Broadcast a message to all clients."""
    
    for client in clients[:]:
        try:
            client.send(message)
        except Exception as e:
            print(f"Error broadcasting to a client: {e}")
            # Safely remove the problematic client
            if client in clients:
                index = clients.index(client)
                clients.pop(index)
                nicknames.pop(index)


def handle(client):
    """Handle communication with a connected client."""
    global client_counter
    try:
        while True:
            message = client.recv(1024).decode(FORMAT)
            if not message:
                raise ConnectionResetError

            nickname = nicknames[clients.index(client)]
            print(f"{nickname} says: {message}")
            broadcast(f"{message}".encode(FORMAT))
    except Exception as e:
        print(f"Error with client: {e}")
        remove_client_by_socket(client)


def decision_window(client_socket, nickname):
    """Show a GUI window to accept or reject a client connection."""
    def accept_client():
        global client_counter
        client_socket.send("ACCEPT".encode(FORMAT))
        with lock:
            nicknames.append(nickname)
            clients.append(client_socket)
            client_counter += 1
        broadcast(f"{nickname} has joined the chat!\n".encode(FORMAT))
        threading.Thread(target=handle, args=(client_socket,)).start()
        root.quit()
        root.destroy()

    def reject_client():
        client_socket.send("REJECT".encode(FORMAT))
        client_socket.close()
        root.quit()
        root.destroy()

    root = tkinter.Tk()
    root.title("Client Request")
    message = tkinter.Label(root, text=f"Do you accept {nickname} to join the chat?")
    message.pack()
    accept_button = tkinter.Button(root, text="Accept", command=accept_client)
    accept_button.pack(padx=20, pady=5)
    reject_button = tkinter.Button(root, text="Reject", command=reject_client)
    reject_button.pack(padx=20, pady=5)
    root.protocol("WM_DELETE_WINDOW", root.quit)
    root.mainloop()

def remove_client(nickname):
    """Remove a client by their nickname."""
    global client_counter

    def remove_client_thread():
        global client_counter
        with lock:
            try:
                # Ensure safe removal
                if nickname in nicknames:
                    index = nicknames.index(nickname)
                    client = clients.pop(index)
                    nicknames.pop(index)
                    client_counter -= 1
                    print(f"Removed {nickname}. Active clients: {len(clients)}")

                    # Notify other clients
                    broadcast(f"{nickname} has been removed by the admin.\n".encode(FORMAT))
                    
                    # Notify the removed client
                    try:
                        client.send("You have been removed by the admin.".encode(FORMAT))
                        print("HERE enjoying")
                    except Exception as e:
                        print(f"Error notifying {nickname}: {e}")
                else:
                    print(f"Client {nickname} not found.")
            except Exception as e:
                print(f"Error during client removal: {e}")

    threading.Thread(target=remove_client_thread, daemon=True).start()


def remove_client_by_socket(client):
    """Remove a client using their socket."""
    global client_counter
    with lock:
        if client in clients:
            index = clients.index(client)
            nickname = nicknames.pop(index)
            clients.pop(index)
            client_counter -= 1
            print(f"{nickname} disconnected. Active clients: {len(clients)}")
            broadcast(f"{nickname} has left the chat.".encode(FORMAT))

def receive():
    """Accept new client connections."""
    while True:
        try:
            client, address = server.accept()
            print(f"Connected with {str(address)}!")

            request_message = client.recv(1024).decode(FORMAT)
            if request_message.startswith("REQUEST:"):
                nickname = request_message.split(":")[1]
                decision_window(client, nickname)
        except OSError:
            break

def update_client_list(window, client_listbox):
    """Update the displayed list of clients in the admin GUI."""
    client_listbox.delete(0, tkinter.END)
    for nickname in nicknames:
        client_listbox.insert(tkinter.END, nickname)

def server_gui():
    """Create the server admin panel GUI."""
    window = tkinter.Tk()
    window.title("Server Admin Panel")

    client_listbox = tkinter.Listbox(window, width=40, height=10)
    client_listbox.pack(padx=20, pady=20)

    def remove_selected_client():
        selected = client_listbox.curselection()
        if selected:
            nickname = client_listbox.get(selected)
            remove_client(nickname)
            # Update the list asynchronously to prevent UI freeze
            window.after(100, update_client_list, window, client_listbox)
        else:
            messagebox.showwarning("No selection", "Please select a client to remove.")

    remove_button = tkinter.Button(window, text="Remove Client", command=remove_selected_client)
    remove_button.pack(padx=20, pady=5)

    update_button = tkinter.Button(window, text="Update Client List", command=lambda: update_client_list(window, client_listbox))
    update_button.pack(padx=20, pady=5)

    update_client_list(window, client_listbox)
    window.mainloop()

# Start the server and GUI
threading.Thread(target=receive, daemon=True).start()
server_gui()
