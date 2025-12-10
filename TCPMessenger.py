import socket
import threading
import json
import struct
import base64
import time

class TCPMessenger:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        self.listener_thread = None
        self.listening = False
        self.on_text_received = None

    def connect(self):
        try:
            if self.socket:
                try:
                    self.socket.close()
                except: 
                    pass


            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))

            if not self.listening:
                self.listening = True
                self.listener_thread = threading.Thread(target=self._listen)
                self.listener_thread.daemon = True
                self.listener_thread.start()
        except Exception as e:             
            print(f"Connection failed: {e}")

    def try_reconnect(self):
        try:
            self.connect()
        except Exception as e:
            time.sleep(60)
            self.try_reconnect()

    def _listen(self):
        while self.listening:
            try:
                message = self.receive_message()
                if not message:
                    if self.listening:
                        self.try_reconnect()
                elif message['type'] == 'text':
                    if self.on_text_received:
                        self.on_text_received(message)
            except ConnectionResetError:
                print("Connection was closed by the server.")
                self.connect()
            except Exception as e:
                print(f"Error receiving message: {e}")

    def receive_message(self):
        raw_len = self.recvall(4)
        if not raw_len:
            return None
        msg_len = struct.unpack('>I', raw_len)[0]
        data = self.recvall(msg_len)
        return json.loads(data.decode('utf-8'))
    
    def recvall(self, n):
        data = bytearray()
        while len(data) < n:
            packet = self.socket.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data
    
    def send_message(self, message):
        data = json.dumps(message).encode('utf-8')
        msg_len = struct.pack('>I', len(data))
        self.socket.sendall(msg_len + data)
    
    def send_text(self, title, content='', chatId=None, messageId=None):
        message = {
            'type': 'text',
            'title': title,
            'content': content,
            'chatId': chatId,
            'messageId': messageId
        }
        self.send_message(message)

    def send_image(self, image_path, title, chatId=None, messageId=None):
        with open(image_path, 'rb') as img_file:
            img_data = img_file.read()
            encoded_img = base64.b64encode(img_data).decode('utf-8')
        
        message = {
            'type': 'image',
            'content': encoded_img,
            'title': title,
            'chatId': chatId, 
            'messageId': messageId
        }
        self.send_message(message)
    
    def set_text_callback(self, callback):
        self.on_text_received = callback