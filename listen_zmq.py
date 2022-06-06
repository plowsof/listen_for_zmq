import sys
import zmq
import threading
import os

node_list = ["node.community.rino.io","192.168.1.68"]

port = "18083"

class CountdownTask:
    def __init__(self):
        self._running = True
      
    def terminate(self):
        self._running = False
          
    def run(self, node):
        while self._running:
            print(node)
            context = zmq.Context()
            socket = context.socket(zmq.SUB)
            socket.setsockopt_string(zmq.SUBSCRIBE, '')
            socket.setsockopt(zmq.CONFLATE, 1)  # last msg only.
            socket.connect(f"tcp://{node}:{port}")  # must be placed after above options.
            data = socket.recv()
            print(data)
            self._running = False
      
for node in node_list:
    c = CountdownTask()
    t = threading.Thread(target = c.run, args =(node, ))
    t.start()
    # wait 30 seconds for the thread to finish its work
    t.join(30)
    if t.is_alive():
        print("The server did not publish a zmq message after 30 seconds")
        c.terminate() 
    else:
        print("The server has a zmq port open :)")
        c.terminate()
os._exit(1)
