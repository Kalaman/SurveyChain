import datetime
import hashlib
import os
import json
import time

from datetime import datetime
from hashlib import sha256
from flask import Flask, jsonify, request

os.system("cls")


print("Starting node ...\n")

class Block(object):
	def __init__(self,block_chain,prev_hash=None):
		self.index = len(block_chain.chain)
		self.timestamp = str(datetime.now())
		self.previous_hash = prev_hash or block_chain.last_block().block_hash
		self.nonce = 0
		self.block_hash = ""
		self.hash_block()
		self.votes = []
		self.surveys = []
		self.mine_time = -1

	def __str__(self):
		return json.dumps(self.__dict__,indent=4, sort_keys=True)

	def hash_block(self):
		self.block_hash = sha256(str(str(self.index) + str(self.timestamp) + str(self.previous_hash) + str(self.nonce)).encode('utf-8')).hexdigest()


class BlockChain(object):
	def __init__(self,difficulty):
		self.chain = []

		genesis_block = Block(self,"Genesis")
		self.chain.append(genesis_block)
		self.new_block = Block(self)
		self.difficulty = difficulty

	def get_block(self,index):
		return self.chain[index]

	def last_block(self):
		return self.chain[-1]

	def add_vote(self,author,survey_id,option_number):
		survey = self.survey_exists(survey_id)

		if (self.vote_valid(survey_id,author) == False and survey and int(option_number) <= len(survey["options"]) - 1 and int(option_number) >= 0):
			vote = {
				"author":author,
				"survey_id":survey_id,
				"option":option_number
			}
			self.new_block.votes.append(vote)
			print ("--> Added vote for survey " + survey_id)
			return True
		else:
			print ("--> Failed voting, survey " + survey_id + " doesnt exists !")
			return False

	def survey_exists(self,survey_id):
		for block in self.chain:
			for current_survey in block.surveys:
				if current_survey["survey_id"] == survey_id:
					return current_survey
		return None

	def vote_valid(self,survey_id,author):
		for current_vote in self.new_block.votes:
			if current_vote["author"] == author and current_vote["survey_id"] == survey_id:
					return True

		for block in self.chain:
			for current_vote in block.votes:
				if current_vote["author"] == author and current_vote["survey_id"] == survey_id:
					return True
		return False

	def add_survey(self,author,question,options):
		try:
			created = str(datetime.now())
			survey = {
				"author":author,
				"question":question,
				"options":options,
				"created":created,
				"survey_id": sha256(str(str(author) + str(question) + str(options) + str(created)).encode('utf-8')).hexdigest()
			}
			self.new_block.surveys.append(survey)
			return True
		except Exception:
			return False

	def mine_block (self):
		start_time = time.time()
		while self.validate_proof(self.new_block) is False:
			self.new_block.nonce += 1
		end_time = time.time()

		self.new_block.mine_time = str(round(end_time - start_time,2))
		self.chain.append(self.new_block)
		#print ("\n## New block mined in "+ str(round(end_time - start_time,2))  + " sec ##\n" + str(self.new_block))
		self.new_block = Block(self)

	def validate_proof(self,block):
		block.hash_block()
		return block.block_hash[:self.difficulty] == ("0" * self.difficulty)

	def print_blockchain(self):
		for block in self.chain:
			print (block)

block_chain = BlockChain(4)
block_chain.add_survey("Professor Zuzu","Wie findet ihr die Mensa ?",["Gut","Durchschnitt","Schlecht"])

app = Flask(__name__)

@app.route('/mine/', methods=['POST'])
def mine_block():
	block_chain.mine_block()

	return "New Block (" + str(block_chain.last_block().index) + ") mined  \n\n " + str(block_chain.last_block())


@app.route('/block/<index>', methods=['GET'])
def get_block(index):
	try:
		resp = str(block_chain.chain[int(index)])
	except IndexError:
		resp = "Invalid Block Index !"
	return resp

@app.route('/block/survey', methods=['POST'])
def add_survey():
	author = request.form['author'];
	question = request.form['question'];
	options = json.loads(request.form['options']);

	print ("lautet : " + str(author))
	success = block_chain.add_survey(author,question,options)

	if success:
		return "New survey has been added\n" + str(block_chain.new_block.surveys[-1])
	else:
		return "Error while adding a new survey !"

@app.route('/block/vote',methods=['POST'])
def add_vote():
	author = request.form['author']
	survey_id = request.form['survey_id']
	option = request.form['option']

	success = block_chain.add_vote(author,survey_id,option)

	if success:
		return "Vote has been added  \n\n" + str(block_chain.new_block.votes[-1])
	else:
		return "Error while adding a new vote\nCheck the survey_id for correctness !"


if __name__ == "__main__":
    app.run(
    host="0.0.0.0",
    port=5000
)


#block_chain = BlockChain(4)
block_chain.add_survey("Professor Zuzu","Wie findet ihr die Mensa ?",["Gut","Durchschnitt","Schlecht"])
#block_chain.add_survey("Dr. Alos","War die KI Klausur schwer ?",["Ja","Geht so","Nein"])
#block_chain.mine_block()
#block_chain.add_vote("Julius",block_chain.chain[1].surveys[0],3)
#block_chain.mine_block()
#block_chain.mine_block()
#block_chain.mine_block()
#block_chain.mine_block()

