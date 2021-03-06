#! /usr/bin/python
""" 
    IRCExchangeBot
    by Arielle B Cruz <arielle.cruz@gmail.com> <http://www.abcruz.com>
    Dedicated to the Public Domain on 05 October 2013
    
    This script spawns two IRC robots on two separate IRC networks. The goal
    is to pass public (in channel) messages from one network to another using
    the two robots. This was originally developed so that the author can see
    any Python-PH messages on freenode in the Python-PH channel on DalNet.
"""
import os
import socket

class IRCExchangeBot:
    host = "irc.freenode.net"
    port = 6667
    channel = "#temp-chan-876"
    nick = "IrCxBoTpY"
    master = "Samhain13"
    socket = None
    socket_on = False
    socket_timeout = 15.0
    inbound_file = "inbound_file.txt"
    outbound_file = "outbound_file.txt"
    quit_message = "Bye."
    view_lines = True  # True to display recv in the terminal.
    
    def connect(self):
        """Connects to the IRC network (host)."""
        # Make sure we have our inbound and outbound files.
        for f in [self.inbound_file, self.outbound_file]:
            if os.path.isfile(f):
                os.remove(f)
            with open(f, "w") as of:
                of.write("")
        # Start the connection.
        self.socket_on = True
        self.socket = socket.socket()
        self.socket.settimeout(self.socket_timeout)
        self.socket.connect((self.host, self.port))
        self.socket.send("NICK %s\r\n" % self.nick)
        self.socket.send("USER %s %s blah :%s\r\n" %
            (self.nick, self.host, self.nick))
        self.socket.send("JOIN :%s\r\n" % self.channel)
    
    def disconnect(self):
        """Disconnects from the IRC network."""
        self.socket.send("QUIT %s\r\n" % self.quit_message)
        self.socket_on = False
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
    
    def get_nick(self, line):
        """Gets the nick from the line."""
        return "\x02%s\x0F" % line.split("!~")[0][1:]
    
    def master_exec(self, command):
        """Executes a command from the master issued as a message."""
        if command.startswith(":quit"):
            self.disconnect()
        if command.startswith(":nick"):
            self.nick = command.split(" ")[-1]
            self.socket.send("NICK %s" % self.nick)
        if command.startswith(":exec "):  # Hardcore IRC command.
            if self.view_lines:
                print command[6:]
            self.socket.send("%s\r\n" % command[6:])
        # Add more "executables" here.
    
    def parse_buffer(self, line):
        """Parses the received line and decides what to do with it."""
        # Handle pongs.
        if line.startswith("PING"):
            self.socket.send("PONG %s\r\n" % line.split(":")[1])
        # Handle public messages.
        if ("PRIVMSG %s :" % self.channel) in line:
            msg = line.split("PRIVMSG %s :" % self.channel)
            # Save the message and the nick to the outbound queue.
            self.send_outbound("%s: %s" % (self.get_nick(msg[0]), msg[1]))
        # Handle private messages from the master.
        elif ("PRIVMSG %s :" % self.nick) in line:
            msg = line.split("PRIVMSG %s :" % self.nick)
            if msg[0].startswith(":%s!" % self.master):
                # Commands are prefixed with ":", send them to exec.
                if msg[1].startswith(":"):
                    self.master_exec(msg[1])
                # For non-commands, simply send them to the channels.
                else:
                    self.send_outbound(msg[1])
                    self.send_channel(msg[1])
        # Handle joins, parts, etc.
        else:
            if len(line.split("JOIN :%s" % self.channel)) == 2 or \
                len(line.split("JOIN %s" % self.channel)) == 2:
                self.send_outbound("%s joined %s in %s." % \
                    (self.get_nick(line), self.channel, self.host))
            if len(line.split("PART :%s" % self.channel)) == 2 or \
                len(line.split("PART %s" % self.channel)) == 2:
                self.send_outbound("%s parted %s in %s." % \
                    (self.get_nick(line), self.channel, self.host))
            if len(line.split("QUIT :")) == 2 or len(line.split("QUIT")) == 2:
                self.send_outbound("%s quit %s in %s." % \
                    (self.get_nick(line), self.channel, self.host))
    
    def receive(self):
        """Reads any text received from the IRC server."""
        readbuffer = ""
        try: readbuffer = readbuffer + self.socket.recv(1024)
        except: pass
        temp = readbuffer.split("\n")
        readbuffer = temp.pop( )
        for line in temp:
            if self.view_lines:
                print line
            self.parse_buffer(line)
    
    def send_inbound(self):
        """Sends out the messages from the inbound file to the channel."""
        if os.path.isfile(self.inbound_file):
            with open(self.inbound_file) as f:
                for line in f.readlines():
                    self.send_channel(line[:-1])
            with open(self.inbound_file, "w") as f:
                f.write("")
    
    def send_outbound(self, line):
        """Writes a line to the outbound file, which can be a log or another
        IRCExchangeBot's inbound_file.
        """
        with open(self.outbound_file, "w+") as f:
            f.write("%s\n" % line)
    
    def send_channel(self, message):
        """Sends a message to the channel."""
        self.socket.send("PRIVMSG %s :%s\r\n" % (self.channel, message))


if __name__ == "__main__":
    # Bot one on freenode.
    bot1 = IRCExchangeBot()
    bot1.host = "irc.freenode.net"
    bot1.channel = "#python-ph"
    bot1.inbound_file = "dal.net.txt"
    bot1.outbound_file = "freenode.net.txt"
    # Bot two on dalnet.
    bot2 = IRCExchangeBot()
    bot2.nick = bot1.nick
    bot2.host = "irc.dal.net"
    bot2.channel = bot1.channel
    bot2.inbound_file = bot1.outbound_file
    bot2.outbound_file = bot1.inbound_file
    # Connect.
    bot1.connect()
    bot2.connect()
    # The loop.
    while bot1.socket_on and bot2.socket_on:
        bot1.receive()
        bot1.send_inbound()
        bot2.receive()
        bot2.send_inbound()