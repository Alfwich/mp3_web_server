import threading
import webbrowser
import cgi
import BaseHTTPServer
import SimpleHTTPServer
import os
import sys
import json
from subprocess import *
from mp3locator import *

MOUNT_DIRECTORY = "/media/"
PORT = 8080

if len( sys.argv ) > 1:
	try:
		PORT = int(sys.argv[1])
	except ValueError:
		print "Port is not an int. Defaulting to 8080"
		PORT = 8080

if PORT == 8080:
  print( "Server starting on default port. Some features will be disabled while on the default port." )

if len( sys.argv ) > 2:
	MOUNT_DIRECTORY = sys.argv[2]

def exeC( cmd, prams="" ):
  try:
    os.system( "%s %s" % ( cmd, prams ) )
  except:
    print "Could not execute command: %s, with prams: %s" % ( cmd, prams )

locator = Mp3Locator()
locator.updateRoot( MOUNT_DIRECTORY )


class Mp3Handler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    serverStarted = False
		# Server methods
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

    def getCommandOutput(self, command):
      result = []

      # Get the information from the mocp process
      raw = Popen(command, stdout=PIPE).communicate()[0]

      # Format the string into a understandable format
      result = raw.split("\n")[0:-1]

      return result
      
      
    def getIPInfo(self):
      output = {}
      raw = Popen(["ifconfig"], stdout=PIPE).communicate()[0]
      output["ip"] = raw
      return output

		# Mp3 player commands
    def startSServer(self):
      print( "Starting server" )
      exeC( "mocp", "-x" )
      exeC( "mocp", "-S" )

    def play(self):
      self.stop()
      print( "playing from: %s" % locator.current() );
      exeC( "mocp", "-p -a '%s'" % locator.current() )

    def pause(self):
      print "pause"
      exeC( "mocp", "--toggle-pause" )

    def stop(self):
      print "stop"
      exeC( "mocp", "-c -s" )

    def next(self):
      print "next track"
      exeC( "mocp", "--next" )

    def prev(self):
      print "prev track"
      exeC( "mocp", "--prev" )

    def next_album(self):
      print "next album"
      self.stop()
      return locator.next()

    def prev_album(self):
      print "next album"
      self.stop()
      return locator.prev()
    
    def info(self):
      result = []
      
      try: result = self.getCommandOutput( ["mocp", "-i"])
      except: print "Could not get MOCP information!"
        
      return result
      
    def info_dirs(self):
      return locator.listDirs()

    def ip(self):
      return self.getCommandOutput( ["ifconfig"])

    def refresh_data(self):
      self.stop()
      locator.updateRoot( MOUNT_DIRECTORY )
      print "Dirs loaded...", locator.listDirs() 
      return locator.listDirs()

    def shuffle(self):
      print "toggle shuffle"
      exeC( "mocp", "--toggle shuffle" )
      
    def reboot(self):
      # Disable reboot button on default port
      if( PORT != 8080 ):
        exeC( "reboot" )

    def do_POST(self):
      try:
        response = { "message": "Invalid command", "output":"" }

        # Start the sound server if it has not already been attempted to be started
        if not Mp3Handler.serverStarted:
          self.startSServer()
          Mp3Handler.serverStarted = True

        # Handle the command from the web client
        post = self.getPostData()
        if "action" in post:
          action = post["action"]
          if hasattr(self, action):
            response["output"] = getattr(self, action)()
            response["message"] = "Command '%s' executed" % action
          else:
            response["message"] = "Command '%s' not found" % action
          
        self.wfile.write( json.dumps( response ) )
      except:
        print( "Error in post handler for mp3 server!" )
        self.wfile.write( "[]" )        

def start_server():
    server_address = ("", PORT)
    server = BaseHTTPServer.HTTPServer(server_address, Mp3Handler)
    server.serve_forever()

if __name__ == "__main__":
    print( "Started moc server and web server on port: %s, reading music recursivly from directory: %s" % ( PORT, MOUNT_DIRECTORY ) )
    start_server()



