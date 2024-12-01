import socket
import threading
import tkinter
import tkinter.scrolledtext
from tkinter import simpledialog


HOST = socket.gethostbyname(socket.gethostname())
PORT = 1210
FORMAT = 'utf-8'
ADDR = (HOST, PORT)

# Emojis dictionary (can be extended)
EMOJIS = {
    ":smile:": "😊", 
    ":cry:": "😭", 
    ":laugh:": "😂", 
    ":wink:": "😉", 
    ":thumbsup:": "👍", 
    ":monkey:": "🙈", 
    ":skull:": "💀", 
    ":wave:": "👋",
    ":love:": "😍", 
    ":yawn:": "🥱", 
    ":chick:": "🐣", 
    ":rose:": "🌹", 
    ":burger:": "🍔", 
    ":pizza:": "🍕", 
    ":fries:": "🍟", 
    ":donut:": "🍩", 
    ":car:": "🚗"
}

def create_beautiful_emoji_button(master, emoji, command):
    button = tkinter.Button(
        master,
        text=emoji,
        command=command,
        font=("Helvetica", 12),  # Larger font for better visibility
        bg="#f0f0f0",  # Light gray background
        fg="black",  # Black text color
        relief="raised",  # Flat button style
        width=2,
        height=1,
        borderwidth=2
    )
    # Hover effects
    button.bind("<Enter>", lambda e: button.config(bg="#FFFFE0"))  # Light Yellow on hover
    button.bind("<Leave>", lambda e: button.config(bg="#f0f0f0"))  # Revert to original color
    button.pack(side=tkinter.LEFT, padx=5, pady=5)
    return button

def create_rounded_button(master, text, command, bg_color, hover_color):
    button = tkinter.Button(master, text=text, command=command, relief="raised", fg="white", bg=bg_color, font=("Helvetica", 12))
    button.config(borderwidth=3, padx=15, pady=5)
    button.bind("<Enter>", lambda e: button.config(bg=hover_color))
    button.bind("<Leave>", lambda e: button.config(bg=bg_color))
    return button

class Client:
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        
        msg = tkinter.Tk()
        msg.withdraw()
        
        self.nickname = simpledialog.askstring("Name", "Please enter your name", parent=msg)
        self.gui_done = False
        self.running = True
        
        # Send the request to the server to join the chat
        self.sock.send(f"REQUEST:{self.nickname}".encode(FORMAT))
        
        # Start only the receive thread here
        receive_thread = threading.Thread(target=self.receive)
        receive_thread.start()

    def gui_loop(self):
        self.win = tkinter.Tk()
        self.win.title(f"Chat Room - {self.nickname}")
        self.win.configure(bg="lightgray")

        self.chat_label = tkinter.Label(self.win, text="CHAT: ", bg="lightgray")
        self.chat_label.config(font=("Helvetica", 14))
        self.chat_label.pack(padx=30, pady=10)
    
        self.text_area = tkinter.scrolledtext.ScrolledText(self.win, font=("Helvetica", 12), bg="#f5f5f5", fg="black", wrap=tkinter.WORD)
        self.text_area.pack(padx=20, pady=10)
        self.text_area.config(state="disabled")  # For preventing user input

        self.msg_label = tkinter.Label(self.win, text="MESSAGE: ", bg="lightgray")
        self.msg_label.config(font=("Helvetica", 14))
        self.msg_label.pack(padx=20, pady=5)
    
        self.input_area = tkinter.Text(self.win, height=3)
        self.input_area.config(font=("Helvetica", 12))
        self.input_area.pack(padx=20, pady=5)
        
        # Emoji buttons
        self.emoji_button_frame = tkinter.Frame(self.win, bg="lightgray")
        self.emoji_button_frame.pack(padx=20, pady=5)
        
        # Add beautified emoji buttons
        for emoji_text, emoji in EMOJIS.items():
            create_beautiful_emoji_button(self.emoji_button_frame, emoji, lambda e=emoji: self.insert_emoji(e))

        # Create rounded blue Send button
        self.send_button = create_rounded_button(self.win, "SEND", self.write, "#007BFF", "#5AB0FF")
        self.send_button.pack(padx=20, pady=5)
        
        # Create rounded red Leave button
        self.leave_button = create_rounded_button(self.win, "LEAVE", self.leave_group, "#FF5733", "#FF8C66")
        self.leave_button.config(fg="white")
        self.leave_button.pack(padx=20, pady=5)
    
        self.gui_done = True
    
        self.win.protocol("WM_DELETE_WINDOW", self.leave_group)
        self.win.mainloop()

    def leave_group(self):
        try:
            self.sock.send(f"{self.nickname} has left the chat.".encode(FORMAT))
        except:
            pass
        self.stop()

    def write(self):
        message = f"{self.nickname}: {self.input_area.get('1.0','end')}"
        self.sock.send(message.encode(FORMAT))
        self.input_area.delete('1.0','end')

    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except:
            pass
        if self.gui_done:
            self.win.quit()
        exit(0)

    def receive(self):
        while self.running:
            try:
                message = self.sock.recv(1024).decode(FORMAT)
                if message == "You have been removed by the admin.":
                    self.update_chat("You have been removed by the admin. Closing...")
                    self.stop()
                elif message == "NICK":
                    self.sock.send(self.nickname.encode(FORMAT))
                elif message == "ACCEPT":
                    threading.Thread(target=self.gui_loop).start()
                    while not self.gui_done:
                        pass
                    self.update_chat("You have been accepted to the chat!")
                elif message == "REJECT":
                    self.update_chat("You have been rejected. Closing...")
                    self.stop()
                else:
                    self.update_chat(message)
            except:
                self.running = False
                break

    def update_chat(self, message):
        if self.gui_done:
            self.text_area.config(state='normal')
            self.text_area.insert('end', message + "\n")
            self.text_area.yview('end')
            self.text_area.config(state='disabled')

    def insert_emoji(self, emoji):
        self.input_area.insert('end', emoji)

client = Client(HOST, PORT)
