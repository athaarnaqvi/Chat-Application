import socket
import threading
import tkinter
import tkinter.scrolledtext
from tkinter import simpledialog


HOST = socket.gethostbyname(socket.gethostname())
PORT = 1210
FORMAT = 'utf-8'
ADDR = (HOST, PORT)

class Client:
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        
        msg = tkinter.Tk()
        msg.withdraw()
        
        self.nickname = simpledialog.askstring("Nickname", "Please choose a nickname", parent=msg)
        self.gui_done = False
        self.running = True
        
        # Send the request to the server to join the chat
        self.sock.send(f"REQUEST:{self.nickname}".encode(FORMAT))
        
        # Start only the receive thread here
        receive_thread = threading.Thread(target=self.receive)
        receive_thread.start()
        
    def gui_loop(self):
        self.win = tkinter.Tk()
        self.win.title(self.nickname)
        self.win.configure(bg="lightgray")
    
        self.chat_label = tkinter.Label(self.win, text="CHAT: ", bg="lightgray")
        self.chat_label.config(font=("Arial", 14))
        self.chat_label.pack(padx=20, pady=5)
    
        self.text_area = tkinter.scrolledtext.ScrolledText(self.win)
        self.text_area.pack(padx=20, pady=5)
        self.text_area.config(state='disabled')  # so that the user cannot change chat history
    
        self.msg_label = tkinter.Label(self.win, text="CHAT: ", bg="lightgray")
        self.msg_label.config(font=("Arial", 14))
        self.msg_label.pack(padx=20, pady=5)
    
        self.input_area = tkinter.Text(self.win, height=3)
        self.input_area.pack(padx=20, pady=5)
    
        self.send_button = tkinter.Button(self.win, text="SEND", command=self.write)
        self.send_button.config(font=("Arial", 14))
        self.send_button.pack(padx=20, pady=5)

        # Add Leave button
        self.leave_button = tkinter.Button(self.win, text="LEAVE", command=self.leave_group)
        self.leave_button.config(font=("Arial", 14), bg="red", fg="white")
        self.leave_button.pack(padx=20, pady=5)
    
        self.gui_done = True
    
        self.win.protocol("WM_DELETE_WINDOW", self.leave_group)  # Handle window close as leave
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
            self.win.quit()  # Use quit instead of destroy to avoid tkinter errors
        exit(0)
        
    def receive(self):
        while self.running:
            try:
                message = self.sock.recv(1024).decode(FORMAT)
                if message == "You have been removed by the admin.":
                    self.update_chat("You have been removed by the admin. Closing...")
                    self.stop()  # Close the client GUI and socket
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


client = Client(HOST, PORT)