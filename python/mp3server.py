import threading
import webbrowser
import cgi
import BaseHTTPServer
import SimpleHTTPServer
import os
import sys
import json
from subprocess import *

MOUNT_DIRECTORY = "/media/"
PORT = 8080

if len( sys.argv ) > 1:
	try:
		PORT = int(sys.argv[1])
	except ValueError:
		print "Port is not an int. Defaulting to 8080"
		PORT = 8080

if len( sys.argv ) > 2:
	MOUNT_DIRECTORY = sys.argv[2]

def exeC( cmd, prams="" ):
	os.system( "%s %s" % ( cmd, prams ) )

# Mp3 player commands
def startSServer():
  print( "Starting server" )
  exeC( "mocp", "-x" )
  exeC( "mocp", "-S" )

def play():
  print( "play" );
  exeC( "mocp", "-p -a %s" % MOUNT_DIRECTORY )

def pause():
  print "pause"
  exeC( "mocp", "--toggle-pause" )

def stop():
  print "stop"
  exeC( "mocp", "-c -s" )
  play.isPlaying = False

def next():
  print "next track"
  exeC( "mocp", "--next" )

def prev():
  print "prev track"
  exeC( "mocp", "--prev" )

def shuffle():
  print "toggle shuffle"
  exeC( "mocp", "--toggle shuffle" )

def reboot():
	exeC( "reboot" )

class Mp3Handler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    serverStarted = False
    def getPostData(self):
      result = {}
      form = cgi.FieldStorage(
          fp=self.rfile,
          headers=self.headers,
          environ={'REQUEST_METHOD':'POST',
                   'CONTENT_TYPE':self.headers['Content-Type'],
      })

      for item in form.list:
        result[item.name] = item.value
      return result

    def getMOCInfo(self):
      output = {}

      # Get the information from the mocp process
      raw = Popen(["mocp", "-i"], stdout=PIPE).communicate()[0]

      # Format the string into a understandable format
      raw = raw.split("\n")[0:-1] # Remove the last element

      # Pack the information into a dict and return that
      for pair in raw:
        info = pair.split(": ")
        if( len(info) == 2 ):
          output[info[0]] = info[1]

      return output
      
      
    def getIPInfo(self):
    	output = {}
	raw = Popen(["ifconfig", ""], stdout=PIPE).communicate()[0]
	output["ip"] = raw
	return output

    def do_POST(self):
      response = "Invalid command"

      # Start the sound server if it has not already been attempted to be started
      if not Mp3Handler.serverStarted:
        startSServer()
        Mp3Handler.serverStarted = True

      # Handle the command from the web client
      post = self.getPostData()
      if "action" in post:
        action = post["action"]
        response = "Command '%s' executed" % action
        if action == "play":
          play()
        elif action == "stop":
          stop()
        elif action == "pause":
          pause()
        elif action == "next":
          next()
        elif action == "prev":
          prev()
        elif action == "shuffle":
          shuffle()
        elif action == "reboot":
					reboot()
        elif action == "info":
          response = json.dumps(self.getMOCInfo())
        elif action == "ip":
          response = json.dumps(self.getIPInfo())
        else:
          response = "Command '%s' not found" % action

        
      self.wfile.write(response)

def start_server():
    server_address = ("", PORT)
    server = BaseHTTPServer.HTTPServer(server_address, Mp3Handler)
    server.serve_forever()

if __name__ == "__main__":
    print( "Started moc server and web server on port: %s, reading music recursivly from directory: %s" % ( PORT, MOUNT_DIRECTORY ) )
    start_server()



