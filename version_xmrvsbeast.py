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

stagenet = {}
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
    global stagenet
    response = requests.get("https://monero.fail/?nettype=mainnet")
    webpage = response.content
    soup = BeautifulSoup(webpage, "html.parser")
    for tr in soup.find_all('tr'):
        values = [data for data in tr.find_all('td')]
        for value in values:
            if "http" not in value.text:
                continue
            if "onion" in value.text:
                continue
            hostname = str(value.text)
            hostname = hostname.split("//")[1]
            if ":" in hostname:
                address = hostname.split(":")[0]
                if len(address.split(".")) > 3:
                    continue
                rpc_port = hostname.split(":")[1]
                stagenet[address] = rpc_port
    for node in stagenet:
        #check if port open first
        os.system(f"nc -zv -w 3 {node} 18083 2>&1 | tee -a zmq_output.tmp")

def main(api_key):
    global stagenet
    if os.path.isfile("zmq_output.tmp"):
        os.remove("zmq_output.tmp")
    check_monero_fail()

    with open("zmq_output.tmp", "r") as f:
        lines = f.readlines()

    for line in lines:
        if "open" in line.strip():
            hostname = line.split(" [")[0]
            print(hostname)
            check_zmq(hostname)
        '''
        if "succeeded" in line.strip():
            hostname = line[14:][:-24].split()[0]
            print(hostname)
            check_zmq(hostname)
        '''

    os.remove("zmq_output.tmp")
    with open("zmq_list.txt", "w+") as f:
        for node in the_list:
            rpc_port = stagenet[node]
            address = socket.gethostbyname(node)
            r = requests.get(f"http://ipinfo.io/{address}?token={api_key}").json()
            f.write(f"{node} | {r['country']} - {r['region']} | rpcport {rpc_port} | p2port 18083\n")

    with open("zmq_list.html", "w+") as f:
        f.write("<table>\n")
        f.write("<tr><th>Hostname</th><th>Country</th><th>RPCport</th><th>P2Pport</th></tr>\n")
        for node in the_list:
            rpc_port = stagenet[node]
            address = socket.gethostbyname(node)
            r = requests.get(f"http://ipinfo.io/{address}?token={api_key}").json()
            f.write(f"<tr><td>{node}</td><td>{r['country']} - {r['region']}</td><td>{rpc_port}</td><td>p2port 18083</td></tr>\n")
        f.write("</table>\n")

if __name__ == "__main__":
   main("hunter2")

os._exit(1)

