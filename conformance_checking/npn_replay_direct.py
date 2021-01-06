import sys
import imp
from petri_net_loader import *
from drawer import *
import snakes.plugins
snakes.plugins.load(["gv", "labels"], "snakes.nets", "nets")
import random
from nets import *
from datetime import datetime, timedelta

# === CONFORMANCE CHECKING USING NESTED PETRI NETS (DIRECT APPROACH) ===
# === USE OF AN APPROACH BASED ON MOVING ("JUMP") TOKENS THAT ARE NOT AVAILABLE IN THE INPUT PLACES FOR KEEP REPLAYING ===
# This method individually replays each trace of an input event log on top
# of a nested Petri net model. The nested Petri net only allows to have WF-nets with name identifiers as tokens.
#Arc expressions are single variables.

testingInteractiveMode = True # if this Flag sets to True, each event will be displayed in the terminal. Then, the user will have to press ENTER to move to the following event to fire. Also, in each step, an image of the net is updated.

# ==== EVENT OF AN EVENT LOG OF A MULTI-AGENT SYSTEM ===
# In this part, we code an Event class, and how a line of an event log of a multi-agent system is parsed into an event object of a specific kind.
# EVENT TYPES:
EVENT_AGENT_AUTONOMOUS_STEP = 1		# a, r1							<--- activity "a" executed by agent "r1"
EVENT_TRANSFER_STEP = 2 			# a, SN, r1, ..., rm			<--- activity "a" executed by the system, which involved agents "r1", ..., "rm"("SN" shall be used for denoting an activity executed by the system)
EVENT_SYNCHRONOUS_STEP = 3			# a, SN, a1, r1, ..., am, rm	<--- activity "a" executed by the system, simultaneously with agents "r1",...,"rm" who executed activities "a1",...,"am"

class Event:

	def __init__(self, line, agentClasses):

		self.eventAsLine = line

		line = (line.replace("\n","")).split(",")

		self.traceIdentifier = str(line[0])
		self.timestamp = line[1]
		self.activity = str(line[2])
		
		self.eventResources = {}  # the key-value map, where key is the resource type (class of agent), and the value is a pair activity-agent (what an activity executed)

		# At this point, we need to check which is the type of this event
		var = line[3].replace("\'", "")

		# CASE #1: THE EVENT IS AN "AGENT-AUTONOMOUS" STEP, e.g., 1,31-12-2020 11:58:24.073,agent_loginreq,'r1'
		if var != "SN":
			self.eventType = EVENT_AGENT_AUTONOMOUS_STEP
			self.executor = var
			for agentClass in agentClasses:
				if agentClass in agentClasses:
					if var in agentClass:
						self.executorType = agentClass # looking for the class of this agent and keep it as an attribute of the event
						break

		elif var == "SN":
			
			self.executor = "SN"
			var2 = line[4].replace("\'", "") # check whether is the activity name or a resource name
			isResourceName = False
			for agentClass in agentClasses:
				if var2 in agentClass:
					isResourceName = True # this means that the 4-th element in the line is the name of a resource, therefore this event is a transfer step (not sycnchronous)
					break

			if isResourceName == True:
				# CASE #2: THE EVENT IS A "TRANSFER (SYSTEM)" STEP, e.g., 1,31-12-2020 12:00:23.611,system_test,'SN','r1'			
				# We know need to read a sequence of resource names 'r1',...,'rm'
				self.eventType = EVENT_TRANSFER_STEP
				i = 4
				while i < len(line):
					# check identifier of the next resource
					line[i] = line[i].replace("\'", "")
					resourceIdentifier = line[i]
					for agentClass in agentClasses:
						if resourceIdentifier in agentClass:
							self.eventResources[agentClass] = resourceIdentifier
							i = i + 1
							break
						#end_if
					#end_for
				#end_while
			else:
				# CASE #3: THE EVENT IS A "SYNCHRONOUS STEP", e.g., 1,31-12-2020 12:00:23.611,system_test,'SN','r1'			
				# We know need to read a sequence of pairs (activity,resource_name)
				self.eventType = EVENT_SYNCHRONOUS_STEP
				i = 4
				while i < len(line):
					# check identifier of the next resource
					line[i] = line[i].replace("\'", "")
					activityName = line[i]

					line[i+1] = line[i+1].replace("\'", "")
					resourceIdentifier = line[i+1]

					for agentClass in agentClasses:
						if resourceIdentifier in agentClass:
							self.eventResources[agentClass] = (activityName,resourceIdentifier)
							i = i + 2
							break
						#end_if
					#end_for
				#end_while

# === END CLASS EVENT ===

def consumeBlackDotSinkWFnet(netToken):

	ep = 0
	ec = 0
	em = 0
	er = 0

	# look for the sink place
	for p in netToken.place():
		if netToken.place(str(p)).label("mark") == "SINK":
			sink = p
			deviationDescription = sink # this variable will hold the name of the sink, and it will be used to inform that the sink is not marked in case
			break

	# check whether the sink place is not marked
	if len(sink.tokens) == 0:
		em = 1 # count one missing token
		sink.add([dot]) # add a black dot token
	
	sink.remove(dot)
	ec = 1 # count one consumed token

	# count remaining tokens in the wf-net
	for p in netToken.place():
		er = er + len(netToken.place(str(p)).tokens)

	return ec,ep,em,er,deviationDescription

def consumeAllResourcesInFinalPlaces(traceResources, finalPlaces, nestedNet):

	ek = 0 # number of all tokens transferred
	ej = 0 # number of final jumps

	agentsToJump = []

	deviationDescription = None

	for (atype, aname) in traceResources:
		agentInFinalPlace = False
		for token in nestedNet.place(finalPlaces[atype]).tokens:
			if token.name == aname:
				agentInFinalPlace = True
				break 
		if not agentInFinalPlace:
			agentsToJump.append((atype,aname))

	for (atype, aname) in agentsToJump:
		# look in places of the net for resource with id. "aname"
		for p in nestedNet.place():
			placeType = p.checker()
			if placeType == atype:
				for netToken in p.tokens:
					if aname == netToken.name:
						# TOKEN JUMP: We have found the "missing" token (the token to jump!) in place p.
						# (1) Delete token with id. "aname" from place p
						p.remove(netToken)
						# (2) Add the token with id. "aname" to the final place for agents of its class.
						nestedNet.place(finalPlaces[atype]).add(netToken)
						break
	
	if len(agentsToJump) > 0 and testingInteractiveMode == True:
		#nestedNet.draw("sn-run.png")
		input("Press any key to jump remaining tokens to final places...")
		draw_net(nestedNet, "sn-run.png")

	for atype in finalPlaces:
		nestedNet.place(finalPlaces[atype]).empty()

	if testingInteractiveMode == True:
		input("Press any key to consume tokens from final places...")
		draw_net(nestedNet, "sn-run.png")

	ej = len(agentsToJump)
	ek = len(traceResources)

	return ek, ej, deviationDescription

def replayEventSystemNet(activity,eventResources, nestedNet):

	# local event counters
	ej = 0	# number of event jumps performed (tokens that jumped from their location to input places of the transition to fire)
	ek = 0	# number of tokens transferred

	deviationDescription = None

	selectedTransition = None

	# look for transition labeled with label "activity"
	for t in nestedNet.transition():
		if activity == nestedNet.transition(str(t)).label("activity"):
			selectedTransition = str(t)
			break

	# CHECK POSSIBLE DEVIATION. IS IT EACH RESOURCE OBSERVED (AGENT) IN THE EVENT IN AN INPUT PLACE OF THE TRANSITION TO FIRE?

	# Grab identifiers of tokens of each input place!
	tokenIdentifiers = {}
	for i in range(len(nestedNet.transition(selectedTransition).input())):
		p = str(nestedNet.transition(selectedTransition).input()[i][0])
		inputType = nestedNet.place(p).checker()
		tokenIdentifiers[inputType] = []
		for token in nestedNet.place(p).tokens:
			tokenIdentifiers[inputType].append(token.name)

	# Is it each event's observed resource in each input place of the transition to fire?
	nonAvailableResources = {} # resources to consume, but that they are not in the input places of the transition to fire
	comment = ""
	for rtype in eventResources:
		# Checking if the identifier belongs to the set of available identifiers in the 
		# input place of type 'rtype'

		if isinstance(eventResources[rtype],tuple): # check if element is a tuple (activity,agentname) or simply a value indicating the agent name
			agentName = eventResources[rtype][1]
		else:
			agentName = eventResources[rtype]

		if agentName not in tokenIdentifiers[rtype]:
			deviationOccurred = True
			nonAvailableResources[rtype] = agentName # token with id. 'agentName' of type 'rtype' is not the input place of t. 

	# ========  TOKEN JUMP HEURISTIC (movement of tokens within the marking to keep replaying!) ========
	for rtype in nonAvailableResources:

		rvalue = nonAvailableResources[rtype]
		for p in nestedNet.place(): # look in places of the net for resource with id. "rvalue" of color "rtype"
			placeType = p.checker()
			if placeType == rtype:
				for netToken in p.tokens:
					if rvalue == netToken.name:
						# TOKEN JUMP: We have found the "missing" token (the token to jump!) in place p.
						# (1) Delete token with id. "rvalue" from place p
						p.remove(netToken)
						# (2) Add the token with id. "rvalue" to the input place (of type "rtype") of the transition to fire
						for i in range(len(nestedNet.transition(selectedTransition).input())):
							inputPlace = str(nestedNet.transition(selectedTransition).input()[i][0])
							if nestedNet.place(inputPlace).checker() == rtype:
								nestedNet.place(inputPlace).add(netToken)
								deviationDescription = netToken.name + "," + p.name + "," + inputPlace # to print in the log that token with id. "rvalue" jumped from place "p.name" to place "inputPlace" of the transition to fire
								#fileDeviations.write(str(e.traceIdentifier) + "," + str(e.timestamp) + "," + str(e.activity) + jumpDescription + "\n")	
							break
					break

	# SELECT BINDING
	# If all input places of the transition to fire have required observed resources (identifiers)
	# then we select a selected binding with these resources
	resourceIds = []
	for rtype in eventResources:

		if isinstance(eventResources[rtype],tuple): # check if element is a tuple (activity,agentname) or simply a value indicating the agent name
			rId = eventResources[rtype][1]
		else:
			rId = eventResources[rtype]
		resourceIds.append(rId)

	# Select the "Substitution" (BINDING) where all resource identifiers are included...
	selectedBinding = None
	for b in nestedNet.transition(selectedTransition).modes():
		counter = 0
		for rid in resourceIds:
			for var in b:
				if b[var].name == rid: # check whether this variable contains a given identifier
					counter = counter + 1
					break # identifier in variable found! Move to check next identifier

		if counter == len(resourceIds):
			# If we enter here, it means that all resource identifiers were found in this binding
			# "We have a winner!" Select this binding :-)
			selectedBinding = b
			break

	nestedNet.transition(selectedTransition).fire(selectedBinding)

	ej = len(nonAvailableResources) # how many resources (net tokens) we had to jump!
	ek = len(eventResources)

	return ek, ej, deviationDescription

def replayEventWFnet(activity, netToken):

	# local event counters
	ec = 0	# event consumed tokens
	ep = 0	# event produced tokens
	em = 0	# event missing tokens

	deviationDescription = None

	# look for transition labeled with label "activity"
	selectedTransition = None
	for t in netToken.transition():
		if activity == netToken.transition(str(t)).label("activity"):
			selectedTransition = str(t)
			break
	
	# check whether transition "selectedTransiton" is enabled
	# we check whether each input place has at least one token to consume
	for i in range(len(netToken.transition(selectedTransition).input())):

		p = str(netToken.transition(selectedTransition).input()[i][0])

		if(len(netToken.place(p).tokens) < 1):	# if there are no tokens available to consume
			netToken.place(p).add([dot])		# add a missing token
			em = em + 1							# update the counter of missing tokens

			# since a token has been mising here, print this information in the deviations file
			# this data will be passed to the main function, so that this string will be printed in the deviation file.
			deviationDescription = p

	# fire transition in the WF-net
	b = netToken.transition(selectedTransition).modes().pop()
	netToken.transition(selectedTransition).fire(b)

	# update the counter of consumed/produced tokens (which is actually the number of input/output places of transition "selectedTransition")
	ec = len(netToken.transition(selectedTransition).input())
	ep = len(netToken.transition(selectedTransition).output())

	return ec,ep,em,deviationDescription


# === DIRECT CONFORMANCE CHECKING WITH NESTED PETRI NETS (REPLAY WITH JUMP HEURISTIC) ===
# INPUT:
#	(1) nestedNet - a nested Petri net with empty initial marking
#	(2) initialPlaces - a collection "p_1",...,"p_d" of place names, where each "p_i" (1 <= i <= d)
#	indicates the initial place for all distinct resources of type i.
#	(3) finalPlaces
#	(4) agentClasses - it indicates all possible types (agent classes) in the nested Petri net
#	(5) eventLogFilename - file where the multi-agent system event log resides

def NPNDirectReplay(nestedNet, initialPlaces, finalPlaces, agentClasses, eventLogFilename, modelFilename, agentTemplates):

	nonFittingTraces = 0
	numberOfTraces = 0

	# GENERAL METRICS
	systemTraceFitness = {}	 # each element of this container indicates the fitness metric for a trace of the input event log
	agentsTraceFitness = {}  # each element of this container indicates the fitness metric of each agent of the input event log
	overallTraceFitness = {}	

	currentTraceIdentifier = None

	timestamp = datetime.now()

	# Buffer of a current trace
	currentTrace = []

	# file for flushing which were the traces that did not fit in the model
	nonFittingTracesFilename = "conformance_artifact_nonfitting_traces_" + timestamp.strftime("%d-%m-%Y") + "_" + timestamp.strftime("%H%M%S")
	nonFittingTracesFilename +=  "_" + timestamp.strftime("%f")[:-3] + ".csv"

	# file for printing which were the "deviating" events in traces
	eventDeviationsFilename = "conformance_artifact_deviations_" + timestamp.strftime("%d-%m-%Y") + "_" + timestamp.strftime("%H%M%S")
	eventDeviationsFilename +=  "_" + timestamp.strftime("%f")[:-3] + ".csv"

	# file which indicates the fitness value for each agent
	fitnessFilename = "conformance_artifact_fitness_" + timestamp.strftime("%d-%m-%Y") + "_" + timestamp.strftime("%H%M%S")
	fitnessFilename +=  "_" + timestamp.strftime("%f")[:-3] + ".csv"

	# Open event log (we assume the use of a file in CSV format)
	with open(eventLogFilename, "r") as eventLog, open(nonFittingTracesFilename, 'w') as fileNonFittingTraces, open(eventDeviationsFilename, 'w') as fileDeviations, open(fitnessFilename, 'w') as fileFitness:

		line = eventLog.readline()

		currentTraceIdentifier = (line.replace("\n","")).split(",")[0]

		event = Event(line, agentClasses) # Store (next) event, by parsing the current line.

		while True:

			# === STORE ALL EVENTS OF A TRACE IN A CACHE-STYLE BUFFER ===
			while event.traceIdentifier == currentTraceIdentifier:

				currentTrace.append(event) # add event to the current trace

				# read and store next event
				line = eventLog.readline()
				line = line.replace("\n", "")

				if not line:
					break
				else:
					event = Event(line, agentClasses) #This event belongs to a new trace!
			#end_while

			# Update the "number of traces" counter
			numberOfTraces = numberOfTraces + 1

			# === TRACE METRICS ===
			systemJumpedTokens = 0			# number of jumps performed in the system net
			systemTransferredTokens = 0		# number of tokens transferred (consumed/produced) in the system net

			# Key-value maps to store counters of consumed, produced, missing, and remaining tokens for each agent
			# For every of these arrays, the "key" shall correspond to the agent identifier, whereas the "value" will be the specific token counter, according to the case.
			agentConsumedTokens = {}
			agentProducedTokens = {}
			agentMissingTokens = {}
			agentRemainingTokens = {}

			# ==== LOOK FOR ALL DISTINCT AGENTS IDENTIFIERS IN THE TRACE ===
			# Here we iterate through events buffered in the "currentTrace" container
			# and we look for all distinct values "event.executor".

			distinctAgentIdentifiers = [] # in this array, collect resource identifiers (distinct tokens) and the class of the resource (atype)
			for e in currentTrace:
				if e.executor not in distinctAgentIdentifiers and e.executor != "SN": # do not count the system as an individual agent.
					for atype in agentClasses:
						if e.executor in atype and (atype, e.executor) not in distinctAgentIdentifiers:
							distinctAgentIdentifiers.append((atype, e.executor))
							break
				# Look also for distinct agents within the involved resources
				for rtype in e.eventResources:
					if isinstance(e.eventResources[rtype],tuple):
						agentIdentifier = e.eventResources[rtype][1]
					else: 
						agentIdentifier = e.eventResources[rtype]
					if (rtype, agentIdentifier) not in distinctAgentIdentifiers:
						distinctAgentIdentifiers.append((rtype, agentIdentifier))
						break

			if testingInteractiveMode == True:
				print("")
				print("REPLAY OF TRACE: " + currentTraceIdentifier)
				draw_net(nestedNet, "sn-run.png")
				input("Generating initial state of the system net...")

			# === POPULATE THE SYSTEM NET WITH NET TOKENS CARRYING THE AGENT IDENTIFIERS ACCORDING TO THEIR CLASS ===
			
			# Associate first each agents identifier with an initial place
			initialResourcesPerPlace = {}
			for placeType in initialPlaces:
				placeName  = initialPlaces[placeType]
				for (atype, aname) in distinctAgentIdentifiers:
					if atype ==  placeType: # if the type of the current place coincides with the type of the individual agent, then add it to this initial place
						if placeType not in initialResourcesPerPlace:
							initialResourcesPerPlace[placeType] = [] # initialize

						netToken = agentTemplates[placeType](aname) # create net token of class "placeType" and identifier "aname"
						
						agentProducedTokens[aname] = 1 # initializing counter of produced tokens (each netToken begins with a black dot in its source place)
						agentConsumedTokens[aname] = 0
						agentRemainingTokens[aname] = 0
						agentMissingTokens[aname] = 0

						initialResourcesPerPlace[placeType].append(netToken) # inform that a net token with name "aname" shall be added to the initial place for agents of type "placetype"

						if testingInteractiveMode == True:
							print("Agent " + netToken.name + " added in initial place " + placeName)
							draw_net(netToken, netToken.name+ "-run.png")

			for placeType in initialPlaces:
				placeName  = initialPlaces[placeType]
				if placeType in initialResourcesPerPlace:
					nestedNet.place(placeName).add(initialResourcesPerPlace[placeType])

			if testingInteractiveMode == True:
				draw_net(nestedNet, "sn-run.png")
				input("All observed agents in the trace were added to the model.\nPress any key to start the trace replay...\n")

			# TODO:
			# INITIALIZE COUNTERS OF PRODUCED, CONSUMED, REMAINING AND MISSING TOKENS TO 1. LOOK FOR THE VARAIBLES ABOVE

			# ========= REPLAY OF THE TRACE SECTION! ========= 
			# Take each event of the buffered trace

			deviationOccurred = False # "Innocent trace, 'till the opposite is proved :-)"

			for e in currentTrace:

				input(e.eventAsLine)

				# === CASE (1): IF e IS AN "AGENT-AUTONOMOUS STEP". REPLAY e WITHIN THE NET TOKEN WITH AGENT ID "e.executor" ===
				if e.eventType == EVENT_AGENT_AUTONOMOUS_STEP:

					# look in places of the net for agent with id. "e.executor"
					for p in nestedNet.place():
						placeType = p.checker()
						if placeType == e.executorType:
							for n in p.tokens:
								if n.name == e.executor:
									netToken = n # save the net token to replay in a variable
									break;

					# replay event e inside the agent's WF-net contained in variable "netToken".
					ec,ep,em,deviationDescription = replayEventWFnet(e.activity,netToken) # number of consumed, produced and missing tokens are retrived in this event

					# check whether a missing token had to be injected (a "deviation" occurred in this step?)
					if(em > 0):
						deviationOccurred = True
						fileDeviations.write(str(e.traceIdentifier) + "," + str(e.timestamp) + "," + str(agentIdentifier) + "," + str(e.activity) + "," + "missing" + "," + deviationDescription + "\n")	

					# update agent statistics
					agentConsumedTokens[netToken.name] = agentConsumedTokens[netToken.name] + ec
					agentProducedTokens[netToken.name] = agentProducedTokens[netToken.name] + ep
					agentMissingTokens[netToken.name] = agentMissingTokens[netToken.name] + em

					if testingInteractiveMode == True:
						draw_net(netToken, str(netToken.name) + "-run.png")
						#netToken.draw(str(netToken.name) + "-run.png")

				# === CASE (2): IF e IS A TRANSFER STEP. REPLAY e IN THE SYSTEM NET SN" ===
				if e.eventType == EVENT_TRANSFER_STEP:
					ek,ej,deviationDescription = replayEventSystemNet(e.activity,e.eventResources,nestedNet)

					systemTransferredTokens = systemTransferredTokens + ek
					systemJumpedTokens = systemJumpedTokens + ej

					# check whether a jump had to be made (a "deviation" occurred in this step?)
					if(ej > 0):
						deviationOccurred = True
						fileDeviations.write(str(e.traceIdentifier) + "," + str(e.timestamp) + "," + "SN" + "," + str(e.activity) + "," + "jump" + "," + deviationDescription + "\n")	

				# === CASE (3): IF e IS A SYNCHRONOUS STEP. REPLAY e IN THE SYSTEM NET SN AND IN ALL INVOLVED AGENTS OF e" ===
				if e.eventType == EVENT_SYNCHRONOUS_STEP:

					ek,ej,deviationDescription = replayEventSystemNet(e.activity,e.eventResources,nestedNet)

					systemTransferredTokens = systemTransferredTokens + ek
					systemJumpedTokens = systemJumpedTokens + ej

					if(ej > 0):
						deviationOccurred = True
						fileDeviations.write(str(e.traceIdentifier) + "," + str(e.timestamp) + "," + "SN" + "," + str(e.activity) + "," + "jump" + "," + deviationDescription + "\n")	

					for atype in e.eventResources:

						agentInternalActivity = e.eventResources[atype][0]
						agentIdentifier = e.eventResources[atype][1]

						# look in places of the net for agent with id. "e.executor"
						for p in nestedNet.place():
							placeType = p.checker()
							if placeType == atype:
								for n in p.tokens:
									if n.name == agentIdentifier:
										netToken = n # save the net token to replay in a variable
										break;

						ec,ep,em,deviationDescription = replayEventWFnet(agentInternalActivity, netToken)
						agentConsumedTokens[agentIdentifier] = agentConsumedTokens[agentIdentifier] + ec
						agentProducedTokens[agentIdentifier] = agentProducedTokens[agentIdentifier] + ep
						agentMissingTokens[agentIdentifier] = agentMissingTokens[agentIdentifier] + em

						if(em > 0):
							deviationOccurred = True

							# take the information from the deviationDescription variable and print it in the deviations file.
							# inform that in this trace occurred at a given time, when executing an agent activity, a control thread ("a token") was not available to execute this activity. (in other words, the agent process should not have executed this activity)
							# "deviationDescription" here has the name of the place where a missing token was missing
							fileDeviations.write(str(e.traceIdentifier) + "," + str(e.timestamp) + "," + str(agentIdentifier) + "," + str(agentInternalActivity) + "," + "missing" + "," + deviationDescription + "\n")	

						if testingInteractiveMode == True:
							draw_net(netToken, str(netToken.name) + "-run.png")
							#netToken.draw(str(netToken.name) + "-run.png")

				if testingInteractiveMode == True:
					draw_net(nestedNet, "sn-run.png")
					#nestedNet.draw("sn-run.png")
					#input(e.eventAsLine)

			# end_for <end of replaying events of a given trace>

			# === IN EACH NET TOKEN'S WF-NET, CONSUME A BLACK DOT FROM THE SINK PLACE ===
			# remaining tokens are also counted inside this function
			for p in nestedNet.place():
				for netToken in p.tokens:
					ec,ep,em,er,deviationDescription = consumeBlackDotSinkWFnet(netToken)
					agentConsumedTokens[netToken.name] = agentConsumedTokens[netToken.name] + ec
					agentProducedTokens[netToken.name] = agentProducedTokens[netToken.name] + ep
					agentMissingTokens[netToken.name] = agentMissingTokens[netToken.name] + em
					agentRemainingTokens[netToken.name] = agentRemainingTokens[netToken.name] + er

					if(er > 0 or em > 0):
						deviationOccurred = True
					
					if(em > 0):
						fileDeviations.write(str(e.traceIdentifier) + "," + str(e.timestamp) + "," + str(netToken.name) + "," + "sink" + "," + "missing" + "," + deviationDescription + "\n")	


			# === CONSUME NET TOKENS (INDIVIDUAL AGENTS) FROM FINAL PLACES IN THE SYSTEM NET ===
			# For each individual agent (net token), check whether the agent is in its corresponding final place
			# If the agent is not in the final place, locate the agent and perform a jump to its final place to consume it.
			ek, ej, deviationDescription = consumeAllResourcesInFinalPlaces(distinctAgentIdentifiers, finalPlaces, nestedNet)
			systemTransferredTokens = systemTransferredTokens + ek
			systemJumpedTokens = systemJumpedTokens + ej
			if(ej > 0):
				deviationOccurred = True
				#TODO think how to print the occurred deviation (some tokens were not available in final places...)

			# === PRINT FITNESS OF THIS TRACE AND FITNESS OF EACH RESOURCE IN A FILE ===
	 		# fitness of the system net 
			systemTraceFitness[currentTraceIdentifier] = 1 - ( systemJumpedTokens / systemTransferredTokens )
			# fitness of each agent
			agentsTraceFitness[currentTraceIdentifier] = {}
			for (atype, aname) in distinctAgentIdentifiers:
				leftTerm = 1 - (agentMissingTokens[aname] / agentConsumedTokens[aname])
				rightTerm = 1 - (agentRemainingTokens[aname] / agentProducedTokens[aname])
				agentsTraceFitness[currentTraceIdentifier][aname] = (0.5*leftTerm) + (0.5*rightTerm)

			# overall fitness of the trace
			fitnessWeight = float(1) / float((len(distinctAgentIdentifiers) + 1))
			overallTraceFitness[currentTraceIdentifier] = 0
			accum = 0
			for (atype, aname) in distinctAgentIdentifiers:
				accum = accum + (fitnessWeight * agentsTraceFitness[currentTraceIdentifier][aname])

			accum = accum + (fitnessWeight * systemTraceFitness[currentTraceIdentifier])
			overallTraceFitness[currentTraceIdentifier] = accum

			# print information of the overall fitness value, the fitness value of the system net and of the agents in one line of the file
			fitLine = str(currentTraceIdentifier)
			fitLine = fitLine + "," + str(overallTraceFitness[currentTraceIdentifier])
			fitLine = fitLine + "," + str(systemTraceFitness[currentTraceIdentifier])

			for aname in agentsTraceFitness[currentTraceIdentifier]:
				fitLine = fitLine + "," + str(agentsTraceFitness[currentTraceIdentifier][aname])
			fileFitness.write(fitLine + "\n")

			if deviationOccurred == True:
				# If while replaying the previous trace, there was a deviation (that is, at least one jump occurred,
				# then update the counter of "non-fitting traces"
				nonFittingTraces = nonFittingTraces + 1

				# if deviation ocurred, flush all the trace to the file of non-fitting traces
				for e in currentTrace:
					fileNonFittingTraces.write(e.eventAsLine + "\n")

			if not line:
				break
			else:
				currentTraceIdentifier = event.traceIdentifier
				currentTrace = []

		#end_while <end of replaying all traces recorded in the log>

		# === PRINTING SUMMARY STATISTICS ===

		# mean value of trace fitness
		averageTraceFitness = sum(overallTraceFitness.values()) / len(overallTraceFitness)

		print("")
		print("========== CONFORMANCE RESULTS ===========")
		print("Total number of traces: " + str(numberOfTraces))
		print("Non-fitting traces (with at least one token jump/missing): " + str(nonFittingTraces))
		print("")
		print("Average Trace Fitness : " + str("%.4f" % round(averageTraceFitness,4)))
		print("")
		print("Event deviations written in file: " + eventDeviationsFilename)
		print("Non-fitting traces cloned to file: " + nonFittingTracesFilename)
		print("==========================================")
		print("")