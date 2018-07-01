import time
import json
import urllib
import datetime
#import app
from hashlib import sha256
from datetime import datetime

class Block(object):
	def __init__(self,index,previous_hash,timestamp=None,surveys=None,votes=None,transactions=None,mine_time=0,block_hash=None,nonce = 0):
		self.index = index
		self.previous_hash = previous_hash
		self.timestamp = timestamp or time.time()
		self.mine_time = mine_time
		self.nonce = 0 or nonce
		self.votes = votes
		self.surveys = surveys or []
		self.votes = votes or []
		self.transactions = transactions or []

		self.block_hash = block_hash or self.hash_block()

	def hash_block(self):
		return sha256(str(str(self.index) + self.previous_hash + str(self.timestamp) + str(self.nonce)).encode()).hexdigest()

	def __repr__(self):
		return json.dumps(self.__dict__,indent=4, sort_keys=True)

	def __str__(self):
		return json.dumps(self.__dict__,indent=4, sort_keys=True)

class BlockChain(object):
	def __init__(self,difficulty=None):
		self.chain = []
		self.current_surveys = []
		self.current_votes = []
		self.current_transactions = []
		self.difficulty = difficulty or 4
		self.nodes = set()

		self.chain.append(self.create_block(nonce=0,previous_hash="0"))

	def mine(self,matr_num):
		self.add_transaction(sender="0",
							receiver=matr_num,
							amount = 3)

		self.sync_chain()

		new_block = self.create_block(0,self.previous_block().hash_block())

		start_time = time.time()
		while BlockChain.validate_proof(new_block,self.difficulty) is False:
			new_block.nonce += 1
		end_time = time.time()

		new_block.mine_time = str(round(end_time - start_time,2))
		new_block.block_hash = new_block.hash_block()
		self.chain.append(new_block)

		self.current_votes = []
		self.current_surveys = []
		self.current_transactions = []

	def validate_proof(block,difficulty):
		hash = block.hash_block()
		return hash[:difficulty] == ("0" * difficulty)

	def create_block(self,nonce,previous_hash):
		block = Block(
			index=len(self.chain),
			previous_hash=previous_hash,
			timestamp=time.time(),
			surveys=self.current_surveys,
			votes=self.current_votes,
			transactions=self.current_transactions)

		#self.chain.append(block)
		return block

	@staticmethod
	def is_valid_block (block,previous_block):
		if (previous_block.index + 1 == block.index and 
			previous_block.hash_block() == block.previous_hash and
			previous_block.timestamp < block.timestamp):
			return True
		else:
			return False

	@staticmethod
	def is_valid_chain(chain):
		previous_block = chain[0]
		current_index = 1
		while current_index < len(chain):
			block = chain[current_index]

			if not BlockChain.is_valid_block(block, previous_block):
				return False
			
			previous_block = block
			current_index += 1
			return True

	def add_transaction(self,sender,receiver,amount):
		transaction = {
			"from":sender,
			"to":receiver,
			"amount":amount
			}
		self.current_transactions.append(transaction)
		return transaction

	# Adds a new survey to the next block
	def add_survey(self,author,question,options):
		created = str(datetime.now())
		survey = {
			"author":author,
			"question":question,
			"options":options,
			"created":created,
			"survey_id": sha256(str(str(author) + str(question) + str(options) + str(created)).encode('utf-8')).hexdigest()
		}
		self.current_surveys.append(survey)
		return True

	## Adds a vote for the next block 
	def add_vote(self,author,survey_id,option_number):
		survey = self.survey_exists(survey_id)

		if (self.vote_exists(survey_id,author) == False and survey and int(option_number) <= len(survey["options"]) - 1 and int(option_number) >= 0):
			vote = {
				"author":author,
				"survey_id":survey_id,
				"option":option_number
			}
			self.current_votes.append(vote)
			return True
		else:
			return False

	## Checks if a given survey exists 
	def survey_exists(self,survey_id):
		for block in self.chain:
			for current_survey in block.surveys:
				if current_survey["survey_id"] == survey_id:
					return current_survey
		return None

	## Checks if a vote already exists 
	def vote_exists(self,survey_id,author):
		for current_vote in self.current_votes:
			if current_vote["author"] == author and current_vote["survey_id"] == survey_id:
					return True

		for block in self.chain:
			for current_vote in block.votes:
				if current_vote["author"] == author and current_vote["survey_id"] == survey_id:
					return True
		return False

	## Returns the TH Coin balance of the given matriculation number 
	def get_balance(self,m_number):
		balance = 0

		for transaction in self.current_transactions:
				if (transaction['to'] == str(m_number)):
					balance = balance + int(transaction['amount'])
				elif (transaction['from'] == str(m_number)):
					balance = balance - int(transaction['amount'])

		for block in self.chain:
			for transaction in block.transactions:
				if (transaction['to'] == str(m_number)):
					balance = balance + int(transaction['amount'])
				elif (transaction['from'] == str(m_number)):
					balance = balance - int(transaction['amount'])

		return balance 

	def previous_block(self):
		return self.chain[-1]

	@property
	def get_serialized_chain(self):
		return [vars(block) for block in self.chain]


	@staticmethod
	def get_block_object_from_block_data(block_data):
		return Block(
			index = block_data['index'],
			previous_hash = block_data['previous_hash'],
			surveys = block_data['surveys'],
			votes = block_data['votes'],
			transactions = block_data['transactions'],
			timestamp=block_data['timestamp'],
			nonce=block_data['nonce'],
			mine_time = block_data["mine_time"])

	def sync_chain(self):
		if (len(self.nodes) > 0 ):
			print ("Starting syncing ...")
		uri_get_chain = "/block/"
		neighbour_chains = []

		for node_address in self.nodes:
			resp = urllib.request.urlopen(node_address + uri_get_chain).read()
			resp = json.loads(resp)
			chain = resp['chain']
			neighbour_chains.append(chain)

		if not neighbour_chains:
			return {'message': 'No neighbour chain is available'}

		longest_chain = max(neighbour_chains, key=len)  # Get the longest chain
		longest_chain = [self.get_block_object_from_block_data(block) for block in longest_chain]

		# If our chain is longest, then do nothing
		if (BlockChain.is_valid_chain(longest_chain) == False):
		    response = {
			    "message":"Chain is not valid !"
		    }
		    print (response["message"])
		elif len(self.chain) >= len(longest_chain):
		    response = {
			    "message":"Chain is already up to date",
			    "chain": self.get_serialized_chain
		    }
		    print (response["message"])
		else:
			print ("New chain has " + str(len(longest_chain) - len(self.chain)) + " more block(s)")
			self.chain = longest_chain
			response = {
				"message":"Chain was replaced",
				"chain":self.get_serialized_chain
			}
		print ("Finished syncing ...")
		return response
