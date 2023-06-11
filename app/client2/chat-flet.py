import socket
import os
import json
import base64
from threading import Thread

TARGET_IP = os.getenv("SERVER_IP") or "127.0.0.1"
TARGET_PORT = os.getenv("SERVER_PORT") or "8890"


class ChatClient:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(TARGET_IP)
        print(TARGET_PORT)
        self.server_address = (TARGET_IP,int(TARGET_PORT))
        self.sock.connect(self.server_address)
        self.tokenid=""

    def sendstring(self,string):
        try:
            self.sock.sendall(string.encode())
            receivemsg = ""
            while True:
                data = self.sock.recv(64)
                # print("diterima dari server",data)
                if (data):
                    receivemsg = "{}{}" . format(receivemsg,data.decode())  #data harus didecode agar dapat di operasikan dalam bentuk string
                    if receivemsg[-4:]=='\r\n\r\n':
                        print("end of string")
                        return json.loads(receivemsg)
        except:
            self.sock.close()
            return { 'status' : 'ERROR', 'message' : 'Gagal'}

    # Fungsi untuk menerima pesan grup
    def client_received(self):
        while True:
            message = self.sock.recv(1024).decode()
            if message != 'exit':
                print(message)
            else:
                break

    # Fungsi untuk mengirim pesan ke grup
    def client_send(self):
        while True:
            chat = input("")
            ### inputdengan flet
            self.sock.sendall(chat.encode())
            if chat=='exit':
                break

    def proses(self,cmdline):
        j=cmdline.split(" ")
        try:
            command=j[0].strip()
            if (command=='auth'):
                username=j[1].strip()
                password=j[2].strip()
                return self.login(username,password)
            elif (command=='regis'):
                username=j[1].strip()
                nama1=j[2].strip()
                nama2=j[3].strip()
                negara=j[4].strip()
                password=j[5].strip()
                return self.registration(username, nama1, nama2, negara, password)
            elif (command=='send'):
                usernameto = j[1].strip()
                message=""
                for w in j[2:]:
                   message="{} {}" . format(message,w)
                return self.sendmessage(usernameto,message)
            elif (command=='inbox'):
                return self.inbox()
            elif (command=='get'):
                return self.get(j[1])
            elif (command=='upload'):
                return self.upload(j[1])
            elif (command=='group'):
                return self.groupChat(j[1])
            elif (command=='logout'):
                return self.logout()
            else:
                return "*Maaf, command tidak benar"
        except IndexError:
                return "-Maaf, command tidak benar"

    def login(self,username,password):
        string="auth {} {} \r\n" . format(username,password)
        result = self.sendstring(string)
        if result['status']=='OK':
            self.tokenid=result['tokenid']
            return "username {} logged in, token {} " .format(username,self.tokenid)
        else:
            return "Error, {}" . format(result['message'])

    def sendmessage(self,usernameto="xxx",message="xxx"):
        if (self.tokenid==""):
            return "Error, not authorized"
        string="send {} {} {} \r\n" . format(self.tokenid,usernameto,message)
        result = self.sendstring(string)
        if result['status']=='OK':
            return "message sent to {}" . format(usernameto)
        else:
            return "Error, {}" . format(result['message'])
    def inbox(self):
        if (self.tokenid==""):
            return "Error, not authorized"
        string="inbox {} \r\n" . format(self.tokenid)
        result = self.sendstring(string)
        if result['status']=='OK':
            return "{}" . format(json.dumps(result['messages']))
        else:
            return "Error, {}" . format(result['message'])
    
    def get(self, filename):
        if (self.tokenid==""):
            return "Error, not authorized"
        string = "get {} {} \r\n".format(self.tokenid, filename)
        result = self.sendstring(string)
        if result['status'] == 'OK':
            with open(filename, 'wb+') as fp:
                filecontent = base64.b64decode(result['file'])
                fp.write(filecontent)
            result.pop('file')
            return "{}".format(result['message'])
        else:
            return "Error, {}".format(result['message'])
    
    def upload(self, filename):
        if (self.tokenid==""):
            return "Error, not authorized"
        with open(filename, 'rb') as fp:
            filecontent = base64.b64encode(fp.read()).decode()
        string = "upload {} {} {} \r\n".format(self.tokenid, filename, filecontent)
        result = self.sendstring(string)
        if result['status'] == 'OK':
            return "{}".format(result['message'])
        else:
            return "Error, {}".format(result['message'])

    def groupChat(self, namagrup):
        if (self.tokenid==""):
            return "Error, not authorized"
        string='group {} {} origin \r\n'.format(self.tokenid, namagrup)
        self.sock.sendall(string.encode())

        try:
            receivemsg = ""
            while True:
                data = self.sock.recv(64)
                print("diterima dari server",data)
                if (data):
                    receivemsg = "{}{}" . format(receivemsg,data.decode())
                    if receivemsg[-4:]=='\r\n\r\n':
                        print("end of string")
                        receivemsg = json.loads(receivemsg)
                        break
        except:
            # self.sock.close()
            receivemsg = { 'status' : 'ERROR', 'message' : 'Gagal'}
        
        if receivemsg['status']=='OK':
            # return "{}".format(receivemsg['message'])
            return 'masuk'
        else:
            return "error"
    
    def logout(self):
        if (self.tokenid==""):
            return "Error, not authorized"
        string = "logout {} \r\n".format(self.tokenid)
        hasil = self.sendstring(string)

        if hasil['status'] =='OK':
            self.tokenid=""
            return hasil['message']
        else:
            return "Error, {}".format(hasil['message'])
    
    def registration(self, username, nama1, nama2, negara, password):
        string="regis {} {} {} {} {} \r\n".format(username, nama1, nama2, negara, password)
        hasil = self.sendstring(string)

        if hasil['status'] == 'OK':
            return hasil['message']
        else:
            return 'Error, {}'.format(hasil['message'])



if __name__=="__main__":
    cc = ChatClient()
    while True:
        cmdline = input("Command {}:" . format(cc.tokenid))
        print(cc.proses(cmdline))

