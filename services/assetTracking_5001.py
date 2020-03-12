#Module-2 Create a Cryptocurrency
import time
import datetime
import hashlib
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from uuid import uuid4
from urllib.parse import urlparse
import threading
run_once = True
# Part 1 - Building a Blockchain

class Blockchain:
    
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof = 1, previous_hash = '0')
        self.nodes = set()
        #self.mine_first_block()
    
    def create_block(self, proof, previous_hash):
        block = {'index' : len(self.chain) + 1,
                 'timestamp' : str(datetime.datetime.now()),
                 'proof' : proof,
                 'previous_hash' : previous_hash,
                 'transactions' : self.transactions}
        self.transactions = []
        self.chain.append(block)
        return block
     
    def get_previous_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:1] == '0':
                check_proof = True
            else:
                new_proof += 1
        return new_proof
    
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        previous_block = chain[0];
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            
            if block['previous_hash'] != self.hash(previous_block):
                return False
            
            previous_proof = previous_block['proof']
            proof = block['proof']
            
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:1] != '0':
                return False
        
            previous_block = block
            block_index += 1
        return True
    
    def add_transaction(self, orderID, productName, lat, lon, place, orderedBy, timestamp):
        data1 = "{\"orderID\":" + "\""+ str(orderID) + "\"" + ",\"productName\":" + "\"" + str(productName) + "\"" + ",\"lat\":"  + "\"" + str(lat)  + "\"" + ",\"lon\":"  + "\"" + str(lon)  + "\"" + ",\"place\":" + "\"" + str(place)  + "\"" + ",\"orderedBy\":" + "\"" + str(orderedBy)  + "\"" + ",\"timestamp\":" + "\"" + str(timestamp) + "\"}"
        data_json = json.loads(data1)
        self.transactions.append(data_json)
    
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1
    
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
        
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length =  len(self.chain)
        for nodes in network:
            try:
                response = requests.get(f'http://{nodes}/get_chain')
                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']
                    if length > max_length and self.is_chain_valid(chain):
                        max_length = length
                        longest_chain = chain
            except:
                print(f'Node {nodes} not available')
        if longest_chain:
            self.chain = longest_chain
            return True
        return False
    
    def announce_new_block(self,block):
        peers = self.nodes
        for peer in peers:
            try:
                url = "http://{}/add_block".format(peer)
                requests.post(url, json = json.dumps(block, sort_keys=True))
            except:
                print(f"Not all peers: {peer}")
    
  
    def mine_first_block(self):
        global run_once
        try:
            if len(self.chain) == 1:
                url = "http://127.0.0.1:5001/mine_block"
                requests.get(url)
                print("Mine first block " + str(run_once))
        except:
            run_once = True
            print("Exception : " + str(run_once))
            return len(self.chain)
        return len(self.chain)

# Creating Web App
app = Flask(__name__)
CORS(app)

#Creating a address for the node on port 5000
node_address = str(uuid4()).replace('-','')

# Creating a Blockchain

blockchain = Blockchain()

@app.route('/mine_block', methods = ['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    #blockchain.add_transaction(sender = node_address, receiver = 'Hadelin', amount = 10)
    block = blockchain.create_block(proof,previous_hash)
    response = {'message' : 'Congratulation you just mined a block!',
                'index' : block['index'],
                'timestamp' : block['timestamp'],
                'proof' : block['proof'],
                'previous_hash' : block['previous_hash'],
                'transactions' : block['transactions']}
    #print(response)
    blockchain.announce_new_block(block)
    return jsonify(response) , 200
    
# Getting the full Blockchain
    
@app.route('/get_chain' , methods = ['GET'])
def get_chain():
    response = [{'chain' : blockchain.chain,
                'length' : len(blockchain.chain)}]
    return jsonify(response) , 200

# Checking the chain Validity
    
@app.route('/is_valid', methods = ['Get'])
def is_valid():
    
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    
    if is_valid:
        response = {'message' : 'All good blockchain is good!'}
    else:
        response = {'message' : 'There is an error'}
    return jsonify(response), 200
            
@app.route('/add_transaction' , methods = ['POST'])
def add_transaction():
    json = request.get_json()
    print(json)
    transaction_keys = ['orderID', 'productName', 'lat', 'lon', 'place', 'orderedBy', 'timestamp']
    if not all (keys in json for keys in transaction_keys):
        print("Some elements of the transaction are missing")
        return "Some elements of the transaction are missing" , 400
    index = blockchain.add_transaction(json['orderID'] , json['productName'] , json['lat'] , json['lon'] ,  json['place'] ,
                                        json['orderedBy'] , json['timestamp'])
    response = {'message' : f'This transaction will be added to the Block {index}'}
    return jsonify(response) , 201


# Decentralizing our Blockchain
# Connnecting new nodes
@app.route('/connect_node', methods  = {'POST'})
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "No Node" , 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message' : 'All the nodes are now connected. These are the nodes :',
                       'total_nodes' : list(blockchain.nodes)}
    blockchain.replace_chain()
    return jsonify(response) , 201
    
# Replacing the chain with the longest chain if needed

@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message' : 'The chain was replced',
                    'new_chain' : blockchain.chain}
    else:
        response = {'message' : 'No change in the chain',
                    'actual_chain' : blockchain.chain}
    return jsonify(response), 200

@app.route('/add_block', methods=['POST', 'GET'])
def add_block():
    block_data = json.loads(request.get_json())
    #print(type(block_data))
    is_added = False
    new_proof = block_data['proof']
    previous_block = blockchain.get_previous_block()
    if new_proof == blockchain.proof_of_work(previous_block['proof']):
        block = blockchain.create_block(block_data['proof'],blockchain.hash(previous_block))
        block['timestamp'] = block_data['timestamp']
        block['transactions'] = block_data['transactions']
        is_added = True
    if not is_added:
        return "The block was discarded by the node", 400
    return "Block added to the chain", 201

@app.route('/get_detail', methods = ['GET'])
def get_detail():
    pID = request.args.get('id')
    response = {'details':[]}
    for block in blockchain.chain:
        transcations = block['transactions']
        for transaction in transcations:
            if(transaction['orderID']==pID):
                response['details'].append(transaction)
    return jsonify(response), 200
    
def first_request():
    threading.Timer(8.0,first_request).start()
    global run_once
    print("First request Called :" + str(run_once) )
    if run_once:
        #print("Mining first block")
        chain_size = blockchain.mine_first_block()
        if chain_size > 1:
            run_once = False

#first_request()            
# Running the App
app.run(host = '0.0.0.0', port = 5001)