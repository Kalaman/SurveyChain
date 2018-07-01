import os
import datetime
import json
import time
import socket
import types 
import urllib

from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib import request 
from pprint import pprint
from hashlib import sha256
from flask import Flask, jsonify, request
from blockchain import BlockChain,Block

os.system("clear")

print ("###############################")
print ("####### Survey Chain 1.1 ######")
print ("###############################\n")

def update_node_list ():
	new_nodes = set() 

	for adress in blockchain.nodes:
		register_url = adress + "/node/register"
		post_fields = {"adress": server_address}

		request = Request(register_url, urlencode(post_fields).encode())
		response = urlopen(request).read().decode()

		json_resp = json.loads(response)

		for adress in json_resp["nodes"]:
			new_nodes.add(str(adress))

	for adress in new_nodes:
		if (adress != server_address):
			register_url = adress + "/node/register"
			post_fields = {"adress": server_address}

			request = Request(register_url, urlencode(post_fields).encode())
			response = urlopen(request).read().decode()

			blockchain.nodes.add(adress)

	print ("-> New nodelist: " + str(list(blockchain.nodes)) + "\n")



blockchain = BlockChain(4)
blockchain.add_survey("1337","Baba",["ja","nein"])
surveyid = blockchain.current_surveys[0]["survey_id"]
blockchain.mine(12345)
blockchain.add_vote("12312",surveyid,0)
blockchain.add_vote("231",surveyid,0)
blockchain.add_vote("1234412",surveyid,0)
blockchain.add_vote("5342",surveyid,0)
blockchain.add_vote("2",surveyid,0)
blockchain.add_vote("3",surveyid,0)
blockchain.add_vote("555",surveyid,1)
blockchain.add_vote("63",surveyid,1)
blockchain.add_vote("234",surveyid,1)
blockchain.add_vote("1132",surveyid,1)
blockchain.mine(12345)
#blockchain.nodes.add("http://localhost:5001")

matr_number = str(input("Matrikelnummer: "))
if not matr_number:
	matr_number = "12345"
	print ("-> Using default matriculation number (12345)")

server_port = input("Port: ")
if not server_port:
	server_port = 5000
	print ("-> Using default port (5000)")
else:
	server_port = int(server_port)

server_ip = str(socket.gethostbyname(socket.gethostname()))
server_address = "http://" + server_ip + ":" + str(server_port)
uri_get_chain = "/block/"

print("IP : " + str(server_ip) + "\n")

nnode = input("Neighbour node address: ")
if not nnode:
	print ("-> No neighbour nodes added\n")
else:
	blockchain.nodes.add("http://" + nnode)
	update_node_list()

blockchain.sync_chain()

app = Flask(__name__)


## Mines a new block 
@app.route('/mine/', methods=['POST'])
def mine_block():
	blockchain.mine(matr_number)
	return jsonify({
			"success":0,
			"block":vars(blockchain.previous_block())
		})

## Gives the complete blockchain back 
@app.route('/block/', methods=['GET'])
def get_blockchain():
	return jsonify({"chain" : blockchain.get_serialized_chain})

## Returns the requested block 
@app.route('/block/<index>', methods=['GET'])
def get_block(index):
	try:
		resp = str(blockchain.chain[int(index)])
	except IndexError:
		resp = "Invalid Block Index !"
	return resp

## Adds a new survey for the new block 
@app.route('/block/survey', methods=['POST'])
def add_survey():
	author = request.form['author'];
	question = request.form['question'];
	options = json.loads(request.form['options']);

	if (blockchain.get_balance(author) > 0):
		if (blockchain.add_survey(author,question,options)):
			blockchain.add_transaction(author,"#Survey-Creation#",1)
			return "New survey has been added\n" + str(blockchain.current_surveys[-1])
		else:
			"Error while adding a new survey !"
	else:
		return "Not enough TH Coins"


## Adds a new vote for an existing survey 
@app.route('/block/vote',methods=['POST'])
def add_vote():
	author = request.form['author']
	survey_id = request.form['survey_id']
	option = request.form['option']

	success = blockchain.add_vote(author,survey_id,option)

	if success:
		#return "Vote has been added  \n\n" + str(blockchain.current_votes[-1])
		return jsonify({"success":0,"message":"Vote has been added","vote":str(blockchain.current_votes[-1])}) 
	else:
		return jsonify({"success":1,"message":"Error while adding a new vote"}) 
		#return "Error while adding a new vote\nCheck the survey_id for correctness !"

## Registers a node address
@app.route('/node/register',methods=['POST'])
def register_node():
	node_adress = request.form['adress']
	blockchain.nodes.add(node_adress)

	response = {
		"nodes":list(blockchain.nodes),
		"message":"Added new node"
	}
	print ("Added new node to list (" + node_adress + ")")
	print (list(blockchain.nodes))
	return jsonify(response),201

## Returns the balance for the given matriculation number
@app.route('/balance/<matriculation_num>',methods=['GET'])
def get_balance(matriculation_num):
	balance = blockchain.get_balance(matriculation_num)
	return jsonify({"matriculation_number":matriculation_num,"balance":balance})


@app.route('/stats/survey/<survey_id>')
def survey_info(survey_id):
	survey = blockchain.survey_exists(survey_id)
	vote_sum = 0

	if (survey):
		option_count = len(survey["options"])
		votes = [0] * option_count
	else:
		return jsonify({"message":"Survey doesn't exist"})

	for block in blockchain.chain:
		for vote in block.votes:
			votes[int(vote["option"])] += 1
			vote_sum += 1

	results = []
	for i in range(option_count):
		results.append({
				"option":survey["options"][i],
				"vote_count": votes[i]
			})

	response = {
		"vote_sum": vote_sum,
		"survey" : survey,
		"results" : results
	}

	return jsonify(response)

@app.route('/sync/', methods=['GET'])
def sync_chain():
	
	# print ("Starting syncing ...")
	# neighbour_chains = []
	# for node_address in blockchain.nodes:
	# 	resp = urllib.request.urlopen(node_address + uri_get_chain).read()
	# 	resp = json.loads(resp)
	# 	chain = resp['chain']
	# 	neighbour_chains.append(chain)

	# if not neighbour_chains:
	# 	return jsonify({'message': 'No neighbour chain is available'})

	# longest_chain = max(neighbour_chains, key=len)  # Get the longest chain
	# longest_chain = [blockchain.get_block_object_from_block_data(block) for block in longest_chain]

	# # If our chain is longest, then do nothing
	# if (BlockChain.is_valid_chain(longest_chain) == False):
	#     response = {
	# 	    "message":"Chain is not valid !"
	#     }
	# elif len(blockchain.chain) >= len(longest_chain):
	#     response = {
	# 	    "message":"Chain is already up to date",
	# 	    "chain": blockchain.get_serialized_chain
	#     }
	# else:
	# 	print ("New chain has " + str(len(longest_chain) - len(blockchain.chain)) + " more block(s)")
	# 	blockchain.chain = longest_chain
	# 	response = {
	# 		"message":"Chain was replaced",
	# 		"chain":blockchain.get_serialized_chain
	# 	}
	# print ("Finished syncing ...")

	response = blockchain.sync_chain()

	return jsonify(response)

if __name__ == "__main__":
    app.run(
    host="0.0.0.0",
    port=server_port
)