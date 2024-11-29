import socket
import threading
import tkinter
import tkinter.scrolledtext
from tkinter import simpledialog


HOST = socket.gethostbyname(socket.gethostname())
PORT = 1210
FORMAT = 'utf-8'
#DISCONNECT_MESSAGE = "!disconnect"
ADDR = (HOST,PORT)

class Client:
    
    def __init__(self, host, port):
        print("Here 4")
        self.sock= socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.connect((host,port))
        
        
        msg = tkinter.Tk()
        msg.withdraw()
        
        self.nickname = simpledialog.askstring("Nickname","Please choose a nickname",parent = msg)
        self.gui_done = False
        self.running = True
        
        gui_thread = threading.Thread(target=self.gui_loop)
        receive_thread = threading.Thread(target=self.receive)
        
        gui_thread.start()
        receive_thread.start()
        
    def gui_loop(self):
        print("Here 5")
        self.win = tkinter.Tk()
        self.win.title(self.nickname)  # Set the window title to the client's nickname
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
        print("Here 11")
        leave_message = f"{self.nickname} has left the chat."
        try:
            self.sock.send(leave_message.encode(FORMAT))
        except:
            pass
        self.stop()
      
    def write(self):
        print("Here 6")
        message = f"{self.nickname}: {self.input_area.get('1.0','end')}" #getting the whole text
        self.sock.send(message.encode(FORMAT))
        self.input_area.delete('1.0','end')
        
    def stop(self):
        print("Here 7")
        self.running = False
        try:
            self.sock.close()
        except:
            pass
        if self.gui_done:
            self.win.quit()  # Use `quit` instead of `destroy` to avoid `tkinter` errors
        exit(0)
        
    def receive(self):
        print("Here 8")
        while self.running:
            try:
                message = self.sock.recv(1024).decode(FORMAT)
                if message == 'NICK':
                    print("Here 9")
                    self.sock.send(self.nickname.encode(FORMAT))
                elif message == "You have been removed by the admin.":
                    self.stop()  # Close the client if the admin removes it
                else:
                    if self.gui_done:
                        print("Here 10")
                        # Use `after` to safely update GUI from a different thread
                        self.win.after(0, self.update_chat, message)
            except:
                print("Closing connection.")
                self.running = False
                break

    def update_chat(self, message):
        """Safely update the chat area from the main thread."""
        self.text_area.config(state='normal')
        self.text_area.insert('end', message + "\n")
        self.text_area.yview('end')
        self.text_area.config(state='disabled')

client = Client(HOST,PORT)