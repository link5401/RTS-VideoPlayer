from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3

	RTSP_VER = "RTSP/1.0"
	TRANSPORT = "RTP/UDP"
	# Initiation..
	def __init__(self, master, serveraddr, serverport, rtpport, filename):
		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.createWidgets()
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = filename
		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1
		self.teardownAcked = 0
		self.connectToServer()
		self.frameNbr = 0
		
	# THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI 	
	def createWidgets(self):
		"""Build GUI."""
		# Create Setup button
		self.setup = Button(self.master, width=20, padx=3, pady=3)
		self.setup["text"] = "Setup"
		self.setup["command"] = self.setupMovie
		self.setup.grid(row=1, column=0, padx=2, pady=2)
		
		# Create Play button		
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=1, column=1, padx=2, pady=2)
		
		# Create Pause button			
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=1, column=2, padx=2, pady=2)
		
		# Create Teardown button
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Teardown"
		self.teardown["command"] =  self.exitClient
		self.teardown.grid(row=1, column=3, padx=2, pady=2)
		
		# Create a label to display the movie
		self.label = Label(self.master, height=19)
		self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5) 
	
	def setupMovie(self):
		"""Setup button handler."""
	#TODO
		self.sendRtspRequest(self.SETUP)
	
	def exitClient(self):
		"""Teardown button handler."""
	#TODO
		self.sendRtspRequest(self.TEARDOWN)
		self.master.destroy() # Close GUI
		os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT) # Delete cached image from video
	def pauseMovie(self):
		"""Pause button handler."""
	#TODO
		if self.state == self.PLAYING:
			self.sendRtspRequest(self.PAUSE)
	
	def playMovie(self):
		"""Play button handler."""
	#TODO
		#new thread - listening to RTP packets
		if self.state == self.READY:
			threading.Thread(target=self.listenRtp).start()
			self.playEvent = threading.Event()
			self.playEvent.clear()
			self.sendRtspRequest(self.PLAY)
	
	def listenRtp(self):		
		"""Listen for RTP packets."""
		#TODO
		while True:
			try:
				print("listening")
				data = self.rtpSocket.recv(20480)
				if data:
					rtpPacket = RtpPacket()
					rtpPacket.decode(data)

					currentFrameNbr = rtpPacket.seqNum()
					print("Current Seq Num: " + str(currentFrameNbr))
					if currentFrameNbr > self.frameNbr:
						self.frameNbr = currentFrameNbr
						self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
			except:
				# Stop listening upon requesting PAUSE or TEARDOWN
				if self.playEvent.isSet():
					break

				# Upon receiving ACK for TEARDOWN request,
				# close the RTP socket
				if self.teardownAcked == 1:
					self.rtpSocket.shutdown(socket.SHUT_RDWR)
					self.rtpSocket.close()
					break


					
	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
	#TODO
		cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
		file = open(cachename, "wb")
		file.write(data)
		file.close()
		return cachename
	
	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
	#TODO
		photo = ImageTk.PhotoImage(Image.open(imageFile))
		self.label.configure(image=photo, height=288)
		self.label.image = photo
	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
	#TODO
		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.rtspSocket.connect((self.serverAddr, self.serverPort))
		except:
			tkinter.messagebox.showwarning('Connection Failed', f'Connection to {self.serverAddr} failed.')
	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""	
		#-------------
		# TO COMPLETE
		#-------------
		#setup
		if requestCode == self.SETUP and self.state == self.INIT:
			threading.Thread(target=self.recvRtspReply).start()
			self.rtspSeq+=1
			request = f'SETUP {self.fileName} {self.RTSP_VER}'
			request += f'\nCSeq: {self.rtspSeq}'
			request += f'\nTransport: {self.TRANSPORT}; client_port= {self.rtpPort}'

			self.requestSent = self.SETUP
		elif requestCode == self.PLAY and self.state == self.READY:
			# Update RTSP sequence number.
			# ...
			self.rtspSeq += 1

			# Write the RTSP request to be sent.
			request = f'PLAY {self.fileName} {self.RTSP_VER}'
			request += f'\nCSeq: {self.rtspSeq}'
			request += f'\nSession: {self.sessionId}'

			# Keep track of the sent request.
			self.requestSent = self.PLAY
		elif requestCode == self.PAUSE and self.state == self.PLAYING:
			self.rtspSeq+=1

			request = f'PAUSE {self.fileName} {self.RTSP_VER}'
			request+= f'\nCSeq: {self.rtspSeq}'
			request+= f'\nSession: {self.sessionId}'

			self.requestSent = self.PAUSE
		else:
			return
		self.rtspSocket.send(request.encode())
		print('\nData sent:\n' + request)
	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		#TODO
		while True:
			reply = self.rtspSocket.recv(1024)

			if reply:
				self.parseRtspReply(reply.decode())

			if self.requestSent == self.TEARDOWN:
				self.rtspSocket.shutdown(socket.SHUT_RDWR)
				self.rtspSocket.close()
				break
	
	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		#TODO
		lines = data.split('\n')
		seqNum = int(lines[1].split(' ')[1])

		if seqNum == self.rtspSeq:
			session = int(lines[2].split(' ')[1])
			# New RTSP session ID
			if self.sessionId == 0:
				self.sessionId = session

			# Process only if the session ID is the same
			if self.sessionId == session:
				if int(lines[0].split(' ')[1]) == 200:
					if self.requestSent == self.SETUP:
						# -------------
						# TO COMPLETE
						# -------------
						# Update RTSP state.
						self.state = self.READY

						# Open RTP port.
						self.openRtpPort()
					elif self.requestSent == self.PLAY:
						self.state = self.PLAYING
					elif self.requestSent == self.PAUSE:
						self.state = self.READY
						# The play thread exits. A new thread is created on resume.
						self.playEvent.set()
					elif self.requestSent == self.TEARDOWN:
						self.state = self.INIT
						# Flag the teardownAcked to close the socket.
						self.teardownAcked = 1
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		#-------------
		# TO COMPLETE
		#-------------
		# Create a new datagram socket to receive RTP packets from the server
		# self.rtpSocket = ...
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		# Set the timeout value of the socket to 0.5sec
		# ...
		self.rtpSocket.settimeout(0.5)

		try:
			self.state =self.READY
			self.rtpSocket.bind(('',self.rtpPort))
		except:
			tkinter.messagebox.showwarning('Unable to Bind',f'Unable to bind PORT={self.rtpPort}')


	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		#TODO
		self.pauseMovie()
		if tkinter.messagebox.askokcancel("Quit?","Are you sure you want to quit?"):
			self.exitClient()
		else:
			self.playMovie()