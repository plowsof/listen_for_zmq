import sys
import zmq
import threading
import os
import requests
from bs4 import BeautifulSoup
import time
import pprint
import socket
port = "18083"

the_list = []
class CountdownTask:
    def __init__(self):
        self._running = True
      
    def terminate(self):
        self._running = False
          
    def run(self, node):
        while self._running:
            context = zmq.Context()
            socket = context.socket(zmq.SUB)
            socket.setsockopt_string(zmq.SUBSCRIBE, '')
            socket.setsockopt(zmq.CONFLATE, 1)  # last msg only.
            socket.connect(f"tcp://{node}:{port}")  # must be placed after above options
            
            while True:
                data = socket.recv()
                print(data)
                print(node)
                the_list.append(node)
                context.term()
                self._running = False
                break
            

def check_zmq(node):
    print("CHeck zmq")
    c = CountdownTask()
    t = threading.Thread(target = c.run, args =(node, ))
    t.start()
    # wait 30 seconds for the thread to finish its work
    t.join(20)
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
    ragequit = []
    for node in stagenet:
        #check if port open first
        os.system(f"nc -zv -w 3 {node} 18083 2>&1 | tee -a zmq_output.tmp")

def main(api_key):
    if os.path.isfile("zmq_output.tmp"):
        os.remove("zmq_output.tmp")
    check_monero_fail()

    with open("zmq_output.tmp", "r") as f:
        lines = f.readlines()

    for line in lines:
        if "succeeded" in line.strip():
            hostname = line[14:][:-24].split()[0]
            print(hostname)
            check_zmq(hostname)

    os.remove("zmq_output.tmp")
    with open("zmq_list.txt", "w+") as f:
        try:
            for node in the_list:
                address = socket.gethostbyname(node)
                r = requests.get(f"http://ipinfo.io/{address}?token={api_key}").json()
                f.write(f"{node} | {r['country']} - {r['region']} \n")
        except:
            print("Error?")
    pprint.pprint(the_list)

if __name__ == "__main__":
   secret = os.environ["API_IPINFO"]
   main(secret)

os._exit(1)
