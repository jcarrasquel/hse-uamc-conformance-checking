import sys
import imp
from petri_net_loader import *
import snakes.plugins
snakes.plugins.load(["gv", "labels"], "snakes.nets", "nets")
import random
from nets import *
from datetime import datetime, timedelta

# === CONFORMANCE CHECKING USING COLORED PETRI NETS WITH ATOMIC DATA RESOURCES ===
# === USE OF AN APPROACH BASED ON MOVING ("JUMP") TOKENS THAT ARE NOT AVAILABLE IN THE INPUT PLACES FOR KEEP REPLAYING ===
# This method individually replays each trace of an input event log on top
# of a colored Petri net model. The colored Petri net only allows to have atomic data resources
# as tokens. Arc expressions are single variables.
# INPUT:
#	(1) cpn - a colored Petri net with empty initial marking
#	(2) initialPlaces - a collection "p_1",...,"p_d" of place names, where each "p_i" (1 <= i <= d)
#	indicates the initial place for all distinct resources of type i.
#	(3) colors - it indicates all possible types (colors) in the cpn
#	(4) eventLogFilename - file where the event log resides

testingInteractiveMode = False # if this Flag sets to True, each event will be displayed in the terminal. Then, the user will have to press ENTER to move to the following event to fire. Also, in each step, an image of the net is updated.

tokenJumpHeuristic = True # if this option sets to True, we active the heuristic to move tokens within the marking to keep replaying...
# That is, for each resource requested be consumed: if the resource is not available in an input place of the transition to fire,
# but is in any other input place of the marking, then we make the token to "jump" to the requested input place.

class Event:

	def __init__(self, line, colors):

		self.eventAsLine = line

		line = (line.replace("\n","")).split(",")

		#['1111036', '18-02-2019T09:13:07.536', 'submit buy order', "'00d0PhpNnWPl'", '1', '22', '3']

		self.traceIdentifier = str(line[0])
		self.timestamp = line[1]
		self.activity = str(line[2])
		self.eventResources = {} # the key-value map, where key is the resource type, and the resource value

		var = line[3].replace("\'", "")

		i = 3 # current singleton value of the line to check (we assume is the identifier of a resource)

		# In this section, now we are going to take all resources observed in this event 
		# and add it to our set of resources "eventResources"
		while i < len(line):
			
			# check identifier of the next resource
			line[i] = line[i].replace("\'", "")
			resourceIdentifier = line[i]

			# using the resource identifier, check the type (color) of this resource
			for colorName in colors:
				if(resourceIdentifier in colorName):
					self.eventResources[colorName] = resourceIdentifier
					i = i + 1
					break
				#end_if
			#end_for
		#end_while

def CPNJumpReplayAtomicDataTokens(inputModel, initialPlaces, colors, eventLogFilename, modelFilename):

	nonFittingTraces = 0
	numberOfTraces = 0

	deviations = 0 # number of times that all resources asked to consume did not appear in the input places of a transition to fire, so we needed to move.

	currentTraceIdentifier = None

	# Buffer of a current trace
	currentTrace = []

	timestamp = datetime.now()

	nonFittingTracesFilename = "conformance_artifact_nonfitting_traces_" + timestamp.strftime("%d-%m-%Y") + "_" + timestamp.strftime("%H%M%S")
	nonFittingTracesFilename +=  "_" + timestamp.strftime("%f")[:-3] + ".csv"

	eventDeviationsFilename = "conformance_artifact_deviations_" + timestamp.strftime("%d-%m-%Y") + "_" + timestamp.strftime("%H%M%S")
	eventDeviationsFilename +=  "_" + timestamp.strftime("%f")[:-3] + ".csv"

	# Open event log (we assume the use of a file in CSV format)
	with open(eventLogFilename, "r") as eventLog, open(nonFittingTracesFilename, 'w') as fileNonFittingTraces, open(eventDeviationsFilename, 'w') as fileDeviations:

		line = eventLog.readline()

		currentTraceIdentifier = (line.replace("\n","")).split(",")[0]

		event = Event(line, colors) # Store (next) event, by parsing the current line.

		while True:

			cpn = inputModel.copy()

			# === STORE ALL EVENTS OF A TRACE IN A CACHE-STYLE BUFFER ===
			while event.traceIdentifier == currentTraceIdentifier:

				currentTrace.append(event) # add event to the current trace

				# read and store next event
				line = eventLog.readline()
				line = line.replace("\n", "")

				if not line:
					break
				else:
					event = Event(line, colors) #This event belongs to a new trace!
			#end_while

			# Update the "number of traces" counter
			numberOfTraces = numberOfTraces + 1

			# TRACE METRICS
			jumpedTokens = 0 # number of jumps
			consumedTokens = 0 # number of consumed tokens
			producedTokens = 0 # number of produced tokens

			# ==== LOOK FOR ALL DISTINCT RESOURCES IN THE TRACE ===
			distinctResourceIdentifiers = [] # in this array, collect resource identifiers (distinct tokens)
			for e in currentTrace:
				for rtype in e.eventResources: #for each type of resource in the set of resources of the event
					if (rtype, e.eventResources[rtype]) not in distinctResourceIdentifiers:
						distinctResourceIdentifiers.append((rtype , e.eventResources[rtype]))

			# === POPULATE INITIAL PLACES WITH ALL THE OBSERVED DISTINCT RESOURCES ===
			initialResourcesPerPlace = {}
			for placeType in initialPlaces:
				placeName  = initialPlaces[placeType]
				for (rtype, rvalue) in distinctResourceIdentifiers:
					if rtype ==  placeType: # if the type of the current place coincides with the type of the token
						if placeType not in initialResourcesPerPlace:
							initialResourcesPerPlace[placeType] = [] # initialize
						initialResourcesPerPlace[placeType].append(rvalue) # add token with 'rvalue' id. to initial place of type 'placeType'

			for placeType in initialPlaces:
				placeName  = initialPlaces[placeType]
				if placeType in initialResourcesPerPlace:
					cpn.place(placeName).add(initialResourcesPerPlace[placeType])

			# ========= REPLAY OF THE TRACE SECTION! ========= 
			# Take each event of the buffered trace

			deviationOccurred = False # "Innocent trace, 'till the opposite is proved :-)"

			for e in currentTrace:

				if testingInteractiveMode == True:
					cpn.draw("run.png")
					input(e.eventAsLine)

				# SELECT TRANSITION TO FIRE ACCORDING TO ACTIVITY LABEL, e.g., t <- selectTransition(a)
				selectedTransition = None
				for t in cpn.transition():
					if e.activity == cpn.transition(str(t)).label("activity"):
						selectedTransition = str(t)
						break

				# CHECK POSSIBLE DEVIATION. IS IT EACH RESOURCE OBSERVED IN THE EVENT IN AN INPUT PLACE OF THE TRANSITION TO FIRE?

				# Grab identifiers of tokens of each input place
				tokenIdentifiers = {}
				for i in range(len(cpn.transition(selectedTransition).input())):
					p = str(cpn.transition(selectedTransition).input()[i][0])
					inputType = cpn.place(p).checker()
					tokenIdentifiers[inputType] = []
					for token in cpn.place(p).tokens:
						tokenIdentifiers[inputType].append(token)

				# Is it each event's observed resource in each input place of the transition to fire?
				nonAvailableResources = {} # resources to consume, but that they are not in the input places of the transition to fire
				comment = ""
				for rtype in e.eventResources:
					# Checking if the identifier belongs to the set of available identifiers in the 
					# input place of type 'rtype'
					if e.eventResources[rtype] not in tokenIdentifiers[rtype]:
						deviations = deviations + 1
						deviationOccurred = True
						rvalue = e.eventResources[rtype]
						nonAvailableResources[rtype] = rvalue # token with id. 'rvalue' of type 'rtype' is not the input place of t. 

				if deviationOccurred == True:
					# Indicate in the file of deviations what happened. Resources that were not available
					if tokenJumpHeuristic == False:
						break


					# ========  TOKEN JUMP HEURISTIC (movement of tokens within the marking to keep replaying!) ========
					for rtype in nonAvailableResources:
						rvalue = nonAvailableResources[rtype]
						for p in cpn.place(): # look in places of the net for resource with id. "rvalue" of color "rtype"
							placeType = p.checker()
							if placeType == rtype:
								if rvalue in p.tokens:
									# TOKEN JUMP: We have found the "missing" token (the token to jump!) in place p.
									# (1) Delete token with id. "rvalue" from place p
									p.remove(rvalue)
									# (2) Add the token with id. "rvalue" to the input place (of type "rtype") of the transition to fire
									for i in range(len(cpn.transition(selectedTransition).input())):
										inputPlace = str(cpn.transition(selectedTransition).input()[i][0])
										if cpn.place(inputPlace).checker() == rtype:
											cpn.place(inputPlace).add(rvalue)

											jumpDescription = "," + rvalue + "," + p.name + "," + inputPlace # to print in the log that token with id. "rvalue" jumped from place "p.name" to place "inputPlace" of the transition to fire
											fileDeviations.write(str(e.traceIdentifier) + "," + str(e.timestamp) + "," + str(e.activity) + jumpDescription + "\n")	
											break
									break

					jumpedTokens = jumpedTokens + len(nonAvailableResources) # how many resources we had to move!

				# SELECT BINDING
				# If all input places of the transition to fire have required observed resources (identifiers)
				# then we select a selected binding with these resources
				resourceIds = []
				for rtype in e.eventResources:
					rId = e.eventResources[rtype]
					resourceIds.append(rId)

				# Select the "Substitution" (BINDING) where all resource identifiers are included...
				selectedBinding = None
				for b in cpn.transition(selectedTransition).modes():
					counter = 0
					for rid in resourceIds:
						for var in b:
							if b[var] == rid: # check whether this variable contains a given identifier
								counter = counter + 1
								break # identifier in variable found! Move to check next identifier
					if counter == len(resourceIds):
						# If we enter here, it means that all resource identifiers were found in this binding
						# "We have a winner!" Select this binding :-)
						selectedBinding = b
						break

				# <<<< FIRE TRANSITION WITH SELECTED BINDING! >>>>
				#input(str("Fire: " + e.activity + "(" + selectedTransition + ") with resources: " + str(resourceIds)))
				#print(selectedTransition)
				#print(selectedBinding)
				#print(cpn.place("p6").tokens)
				cpn.transition(selectedTransition).fire(selectedBinding)
				#cpn.draw("run.png")

				consumedTokens = consumedTokens + len(cpn.transition(selectedTransition).input())
				producedTokens = producedTokens +  len(cpn.transition(selectedTransition).output())

			# end_for <end of replaying events of a given trace>
			
			# TODO <--- EXPERIMENT STILL ON DEVELOPMENT (FITNESS METRIC)
			print(consumedTokens)
			print(producedTokens)
			print(jumpedTokens)
			traceFitness = 1 - ( (2 * jumpedTokens) / (consumedTokens + producedTokens) )
			print(currentTraceIdentifier + " : " + str(traceFitness))

			# IDEAS:
			# - Nice the thing of printing on each iteration (put it as an "elective" option)
			# - When a deviation is found. As an elective option, print the image.

			if deviationOccurred == True:
				# If while replaying the previous trace, there was a deviation,
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
		print("")
		print("========== CONFORMANCE RESULTS ===========")
		print("Total number of traces: " + str(numberOfTraces))
		print("Non-fitting traces: " + str(nonFittingTraces))
		print("")
		fitness = 1 - (float(nonFittingTraces) / float(numberOfTraces) )
		print("Fitness : " + str("%.4f" % round(fitness,4)))
		print("")
		print("Deviations detected (non-available resources): " + str(deviations))
		print("")
		print("Event deviations written in file: " + eventDeviationsFilename)
		print("Non-fitting traces cloned to file: " + nonFittingTracesFilename)
		print("==========================================")
		print("")