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
    with lock:
        print(f"Broadcasting message to {len(clients)} clients.")
        for client in clients[:]:  # Iterate over a copy
            try:
                client.send(message)

            except Exception as e:
                print(f"Error broadcasting to client: {e}")
                # Clean up the disconnected client
                index = clients.index(client)
                nickname = nicknames.pop(index)
                clients.remove(client)
                print(f"Removed {nickname} from the client list.")
    
    if len(clients) == 0:
        print("No more clients. Closing the server.")
        server.close()  # Close the server socket


def handle(client):
    while True:
        if len(clients) == 0:
            print("No more clients. Closing the server.")
            server.close()  # Close the server socket
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
                    print(f"{nickname} forcefully disconnected.")
            print(f"Thread for {nickname} has exited.")  # Add this here
            break



def decision_window(client_socket, nickname):
    def accept_client():
        global client_counter
        client_socket.send("ACCEPT".encode(FORMAT))
        with lock:
            nicknames.append(nickname)
            clients.append(client_socket)
            client_counter += 1
        broadcast(f"{nickname} has joined the chat!\n".encode(FORMAT))
        thread = threading.Thread(target=handle, args=(client_socket,))
        thread.start()
        root.destroy()  # Close the decision window

    def reject_client():
        client_socket.send("REJECT".encode(FORMAT))
        client_socket.close()
        root.destroy()  # Close the decision window

    # GUI for decision
    root = tkinter.Tk()
    root.title("Client Request")
    message = tkinter.Label(root, text=f"Do you accept {nickname} to join the chat?")
    message.pack()
    accept_button = tkinter.Button(root, text="Accept", command=accept_client)
    accept_button.pack(padx=20, pady=5)
    reject_button = tkinter.Button(root, text="Reject", command=reject_client)
    reject_button.pack(padx=20, pady=5)
    root.protocol("WM_DELETE_WINDOW", root.destroy)  # Handle window close
    root.mainloop()


# Modified receive function
def receive():
    while True:
        try:
            client, address = server.accept()
            print(f"Connected with {str(address)}!")

            # Receive client request to join
            request_message = client.recv(1024).decode(FORMAT)

            if request_message.startswith("REQUEST:"):
                nickname = request_message.split(":")[1]

                # Show decision window in a new thread
                threading.Thread(target=decision_window, args=(client, nickname), daemon=True).start()
        except OSError:
            break

def remove_client(nickname):
    global client_counter
    with lock:
        try:
            index = nicknames.index(nickname)
            client = clients[index]

            # Close client socket and let handle clean up
            
            client.send("You have been removed by the admin.".encode(FORMAT))
            client.close()

            print(f"{nickname} successfully removed.")
            client_counter -= 1
        except ValueError:
            print(f"{nickname} not found.")
    broadcast(f"{nickname} has been removed by the admin.\n".encode(FORMAT))


# Add the server GUI function
def server_gui():
    window = tkinter.Tk()
    window.title("Server Admin Panel")

    client_listbox = tkinter.Listbox(window, width=40, height=10)
    client_listbox.pack(padx=20, pady=20)

    def update_client_list():
        client_listbox.delete(0, tkinter.END)
        for client in nicknames:
            client_listbox.insert(tkinter.END, client)

    def remove_selected_client():
        selected = client_listbox.curselection()
        if selected:
            nickname = client_listbox.get(selected)
            # Use a thread to handle client removal
            threading.Thread(target=remove_client, args=(nickname,)).start()
            update_client_list()
        else:
            messagebox.showwarning("No selection", "Please select a client to remove.")

    remove_button = tkinter.Button(window, text="Remove Client", command=remove_selected_client)
    remove_button.pack(padx=20, pady=5)

    update_button = tkinter.Button(window, text="Update Client List", command=update_client_list)
    update_button.pack(padx=20, pady=5)

    update_client_list()
    window.mainloop()

# Start the server GUI in a new thread
threading.Thread(target=server_gui, daemon=True).start()

receive()