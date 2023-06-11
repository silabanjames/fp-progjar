import sys
import os
import json
import base64
import uuid
import logging
from queue import  Queue

class Chat:
	def __init__(self):
		self.groups={}
		self.sessions={}
		self.users = {}
		self.users['messi']={ 'nama': 'Lionel Messi', 'negara': 'Argentina', 'password': 'surabaya', 'incoming' : {}, 'outgoing': {}}
		self.users['henderson']={ 'nama': 'Jordan Henderson', 'negara': 'Inggris', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}}
		self.users['lineker']={ 'nama': 'Gary Lineker', 'negara': 'Inggris', 'password': 'surabaya','incoming': {}, 'outgoing':{}}
	
	##### Menulis pesan dari server lain
	def write_incoming(self, data):
		j=data.split(" ")
		try:
			usernamefrom = j[1].strip()
			usernameto = j[2].strip()
			message = ""
			for w in j[3:]:
				message="{} {}".format(message, w)
			s_to = self.get_user(usernameto)
			if (s_to==False):
				return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
			message = { 'msg_from': usernamefrom, 'msg_to': s_to['nama'], 'msg': message }
			inqueue_receiver= s_to['incoming']
			try:
				inqueue_receiver[usernamefrom].put(message)
			except KeyError:
				inqueue_receiver[usernamefrom]=Queue()
				inqueue_receiver[usernamefrom].put(message)
			return {'status': 'OK', 'message': 'Message Sent', 'sendback': message}
		except IndexError:
			return {'status': 'ERROR', 'message': '--Protocol Tidak Benar'}
	
	##### Menulis history pesan setelah mengirim pesan ke server lain
	def write_outgoing(self, data):
		usernamefrom = data['msg_from']
		outqueue_sender = self.get_user(usernamefrom)
		try:	
			outqueue_sender[usernamefrom].put(data)
		except KeyError:
			outqueue_sender[usernamefrom]=Queue()
			outqueue_sender[usernamefrom].put(data)
	
	##### Request group dari server lain
	def groupOtherServer(self, socket, data):
		j=data.split(" ")
		username = j[1]
		groupname = j[2]
		state = j[3]
		hasil = self.group_chat(username, groupname, state, socket)
		return hasil
	
	##### Fungsi tambahan untuk group_chat()
	def broadcast(self, groupname, data):
		for c in self.groups[groupname]:          
			c[1].sendall(data.encode())

	def exitGroup(self, groupname, client):
		self.groups[groupname].remove(client)
	##### -----

	def proses(self, data, socket=[]):
		j=data.split(" ")
		try:
			command=j[0].strip()
			if (command=='auth'):
				username=j[1].strip()
				password=j[2].strip()
				logging.warning("AUTH: auth {} {}" . format(username,password))
				return self.autentikasi_user(username,password)
			elif (command == "regis"):
				logging.warning("REGIS: registration new user")
				username=j[1]
				nama1=j[2]
				nama2=j[3]
				negara=j[4]
				password=j[5]
				return self.registration(username, nama1, nama2, negara, password)
			elif (command=='logout'):
				sessionid = j[1].strip()
				return self.logout(sessionid)
			elif (command=='send'):
				sessionid = j[1].strip()
				usernameto = j[2].strip()
				message=""
				for w in j[3:]:
					message="{} {}" . format(message,w)
				usernamefrom = self.sessions[sessionid]['username']
				logging.warning("SEND: session {} send message from {} to {}" . format(sessionid, usernamefrom,usernameto))
				return self.send_message(sessionid,usernamefrom,usernameto,message)
			elif (command=='inbox'):
				sessionid = j[1].strip()
				username = self.sessions[sessionid]['username']
				logging.warning("INBOX: {}" . format(sessionid))
				return self.get_inbox(username)
			elif (command=='get'):
				sessionid = j[1].strip()
				if sessionid not in self.sessions:
					return {'status': 'ERROR', 'message': 'Session tidak ditemukan'}
				params = [x for x in j[2:]]
				logging.warning('GET: session {} download file {}'.format(sessionid, params[0]))
				return self.get_file(params)
			elif (command=='upload'):
				sessionid = j[1].strip()
				if sessionid not in self.sessions:
					return {'status': 'ERROR', 'message': 'Session tidak ditemukan'}
				params = [x for x in j[2:]]
				logging.warning('UPLOAD: session {} upload file {}'.format(sessionid, params[0]))
				return self.upload_file(params)
			elif (command=='group'):
				sessionid = j[1]
				groupname = j[2]
				state = j[3]
				logging.warning("GROUP: {}".format(groupname))
				username = self.sessions[sessionid]['username']
				if username:
					return self.group_chat(username, groupname, state, socket)
				else:
					return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
			else:
				return {'status': 'ERROR', 'message': '**Protocol Tidak Benar'}
		except KeyError:
			return { 'status': 'ERROR', 'message' : 'Informasi tidak ditemukan'}
		except IndexError:
			return {'status': 'ERROR', 'message': '--Protocol Tidak Benar'}
	
	def logout(self, sessionid):
		if sessionid  not in self.sessions:
			return {'status': 'ERROR', 'message': 'Session tidak ditemukan'}
		self.sessions.pop(sessionid)
		return {'status': 'OK', 'message': 'Berhasil log out'}
	
	def registration(self, username, nama1, nama2, negara, password):
		# Urutan input yang diminta: username, nama, negara, password
		try:
			print("REGIS: get username =",username)
			if username in self.users:
				return {'status': 'ERROR', 'message': 'Username telah digunakan'}
			self.users[username] = {'nama': f'{nama1} {nama2}', 'negara': negara, 'password':password, 'incoming':{}, 'outgoing':{}}
			return {'status': 'OK', 'message': 'Pendaftaran berhasil'}
		except Exception as e:
			return {'status': 'ERROR', 'message': f'e'}
		
	def autentikasi_user(self,username,password):
		if (username not in self.users):
			return { 'status': 'ERROR', 'message': 'User Tidak Ada' }
		if (self.users[username]['password']!= password):
			return { 'status': 'ERROR', 'message': 'Password Salah' }
		tokenid = str(uuid.uuid4()) 
		self.sessions[tokenid]={ 'username': username, 'userdetail':self.users[username]}
		return { 'status': 'OK', 'tokenid': tokenid }

	def get_user(self,username):
		if (username not in self.users):
			return False
		return self.users[username]

	def send_message(self,sessionid,username_from,username_dest,message):
		if (sessionid not in self.sessions):
			return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
		s_fr = self.get_user(username_from)
		s_to = self.get_user(username_dest)
		
		if (s_fr==False or s_to==False):
			return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}

		message = { 'msg_from': s_fr['nama'], 'msg_to': s_to['nama'], 'msg': message }
		outqueue_sender = s_fr['outgoing']
		inqueue_receiver = s_to['incoming']
		try:	
			outqueue_sender[username_from].put(message)
		except KeyError:
			outqueue_sender[username_from]=Queue()
			outqueue_sender[username_from].put(message)
		try:
			inqueue_receiver[username_from].put(message)
		except KeyError:
			inqueue_receiver[username_from]=Queue()
			inqueue_receiver[username_from].put(message)
		return {'status': 'OK', 'message': 'Message Sent'}

	def get_inbox(self,username):
		s_fr = self.get_user(username)
		incoming = s_fr['incoming']
		msgs={}
		for users in incoming:
			msgs[users]=[]
			while not incoming[users].empty():
				msgs[users].append(s_fr['incoming'][users].get_nowait())
		return {'status': 'OK', 'messages': msgs}
	
	def get_file(self, params=[]):
		try:
			filename = params[0]
			if filename=='':
				return {'status':'ERROR', 'message': 'Masukkan nama file'}
			with open(f'files/{filename}', 'rb') as fp:
				filecontent = base64.b64encode(fp.read()).decode()
			print("Mengirim file Kembali")
			return {'status': 'OK', 'message': 'File telah diterima', 'file':filecontent}
		except Exception as e:
			return {'status': 'ERROR', "message": f'{e}'}
	
	def upload_file(self, params=[]):
		try:
			filename = params[0]
			isifile = base64.b64decode(params[1])
			if filename == '' or isifile == '':
				return {'status': 'ERROR', 'message': 'Tidak ada file yang dikirim'}
			with open(f'files/{filename}', 'wb+') as fp:
				fp.write(isifile)
			return {'status': 'OK', 'message': 'File telah dikirim'}
		except Exception as e:
			return {'status': 'ERROR', 'message': f'{e}'}

	
	def group_chat(self, username, groupname, state, socket):
		groups = self.groups
		client = [username, socket]
		if groupname not in groups and state != 'comeback':
			# Jika nama grup tidak ada pada server
			return {'status': 'PENDING', 'message': f'Tidak ada grup {groupname} di server'}
		elif state == 'comeback':
			# Jika nama grup tidak ada di server sebelah, buat grup baru
			groups[groupname] = [client]
		else:
			sambutan = f"{username} telah bergabung"
			self.broadcast(groupname, sambutan)
			groups[groupname].append(client)

		return {'status': 'OK', 'message': f'Bergabung ke grup {username}'}
	
	def group_with_flet(self, groupname, username, socket):
		while True:
			try:
				print('CHAT: Menunggu pesan client')
				chat = socket.recv(1024).decode()
				print(f"menerima pesan dari client = {chat}")
				if chat != 'exit':
					chat = f"{username}: {chat}"
					self.broadcast(groupname, chat)
				else:
					socket.send("exit".encode())
					self.exitGroup(groupname, [username, socket])
					print(f'user {username} telah keluar')
					self.broadcast(groupname, f"{username} meninggalkan group")
					break
			except:
				self.exitGroup(groupname, [username, socket])
				break


if __name__=="__main__":
	j = Chat()
	sesi = j.proses("auth messi surabaya")
	print(sesi)
	#sesi = j.autentikasi_user('messi','surabaya')
	#print sesi
	tokenid = sesi['tokenid']
	print(j.proses("send {} henderson hello gimana kabarnya son " . format(tokenid)))
	print(j.proses("send {} messi hello gimana kabarnya mess " . format(tokenid)))

	#print j.send_message(tokenid,'messi','henderson','hello son')
	#print j.send_message(tokenid,'henderson','messi','hello si')
	#print j.send_message(tokenid,'lineker','messi','hello si dari lineker')


	print("isi mailbox dari messi")
	print(j.get_inbox('messi'))
	print("isi mailbox dari henderson")
	print(j.get_inbox('henderson'))