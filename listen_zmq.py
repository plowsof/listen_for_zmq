#this leaves threads open while running .-.
import sys
import zmq
import threading
import os
import requests
from bs4 import BeautifulSoup
import time
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
            
            while True:
                data = socket.recv()
                print(data)
                break
            self._running = False

def check_zmq(node):
    c = CountdownTask()
    t = threading.Thread(target = c.run, args =(node, ))
    t.start()
    # wait 30 seconds for the thread to finish its work
    t.join(5)
    if t.is_alive():
        print("The server did not publish a zmq message after 30 seconds")
        c.terminate() 
    else:
        print("The server has a zmq port open :)")
        c.terminate()

def check_monero_fail():
    response = requests.get("https://monero.fail/?nettype=mainnet")
    webpage = response.content
    stagenet = []
    soup = BeautifulSoup(webpage, "html.parser")
    for tr in soup.find_all('tr'):
        values = [data for data in tr.find_all('td')]
        for value in values:
            if "http" in value.text:
                if "onion" not in value.text:
                    hostname = str(value.text)
                    hostname = hostname.split("//")[1]
                    if ":" in hostname:
                        hostname = hostname.split(":")[0]
                    stagenet.append(hostname)
    for node in stagenet:
        check_zmq(node)

check_monero_fail()
os._exit(1)

#node.cryptocano.de
