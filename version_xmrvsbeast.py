import sys
import zmq
import threading
import os
import requests
from bs4 import BeautifulSoup
import time
import pprint
import socket

stagenet = {}
the_list = []
class CountdownTask:
    def __init__(self):
        self._running = True
      
    def terminate(self):
        self._running = False
          
    def run(self, node, port):
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
                node = f"{node}_{port}"
                the_list.append(node)
                context.term()
                self._running = False
                break
            

def check_zmq(node, port):
    print("CHeck zmq")
    c = CountdownTask()
    t = threading.Thread(target = c.run, args =(node, port, ))
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
        os.system(f"nc -zv -w 3 {node} 18083 2>&1 | tee -a zmq_output_18083.tmp")
        os.system(f"nc -zv -w 3 {node} 18084 2>&1 | tee -a zmq_output_18084.tmp")

def main(api_key):
    global stagenet
    if os.path.isfile("zmq_output_18083.tmp"):
        os.remove("zmq_output_18083.tmp")
    if os.path.isfile("zmq_output_18084.tmp"):
        os.remove("zmq_output_18084.tmp")
    check_monero_fail()

    with open("zmq_output_18083.tmp", "r") as f:
        lines_18083 = f.readlines()
    with open("zmq_output_18084.tmp", "r") as f:
        lines_18084 = f.readlines()
    for line in lines_18083:
        '''
        if "open" in line.strip():
            hostname = line.split(" [")[0]
            print(hostname)
            check_zmq(hostname, "18083")
        '''
        if "succeeded" in line.strip():
            hostname = line[14:][:-24].split()[0]
            print(hostname)
            check_zmq(hostname,"18083")
    for line in lines_18084:
        '''
        if "open" in line.strip():
            hostname = line.split(" [")[0]
            print(hostname)
            check_zmq(hostname, "18084")
        '''
        if "succeeded" in line.strip():
            hostname = line[14:][:-24].split()[0]
            print(hostname)
            check_zmq(hostname, "18084")
    os.remove("zmq_output_18083.tmp")
    os.remove("zmq_output_18084.tmp")
    with open("zmq_list.txt", "w+") as f:
        for node in the_list:
            p2port = node.split("_")[1]
            node = node.split("_")[0]
            rpc_port = stagenet[node]
            address = socket.gethostbyname(node)
            r = requests.get(f"http://ipinfo.io/{address}?token={api_key}").json()
            f.write(f"{node} | {r['country']} - {r['region']} | rpcport {rpc_port} | p2port {p2port}\n")

    with open("zmq_list.html", "w+") as f:
        f.write("<table>\n")
        f.write("<tr><th>Hostname</th><th>Country</th><th>RPCport</th><th>P2Pport</th></tr>\n")
        for node in the_list:
            p2port = node.split("_")[1]
            node = node.split("_")[0]
            rpc_port = stagenet[node]
            address = socket.gethostbyname(node)
            r = requests.get(f"http://ipinfo.io/{address}?token={api_key}").json()
            f.write(f"<tr><td>{node}</td><td>{r['country']} - {r['region']}</td><td>{rpc_port}</td><td>{p2port}</td></tr>\n")
        f.write("</table>\n")

if __name__ == "__main__":
   main("hunter2")

os._exit(1)
