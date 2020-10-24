import sys
import imp
from petri_net_loader import *
import snakes.plugins
snakes.plugins.load(["gv", "labels"], "snakes.nets", "nets")
import random
from nets import *
from datetime import datetime, timedelta

# === CONFORMANCE CHECKING BETWEEN COLORED PETRI NETS AND EVENT LOGS (AIST) ===
# This method individually replays each trace of an input event log on top
# of a colored Petri net model. The colored Petri net allows to have tuples
# as tokens. Arc expressions are dingle tuples, where each element can be either
# a constant, a variable, or a function between variables.
# INPUT:
#	(1) cpn - a colored Petri net with empty initial marking
#	(2) initialPlaces - a collection "p_1",...,"p_d" of place names, where each "p_i" (1 <= i <= d)
#	indicates the initial place for all distinct resources of type i.
#	(3) colors - it indicates all possible types (colors) in the cpn
#	(4) eventLogFilename - file where the event log resides

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

				# colorName has the definition of a cartesian product D_1 x ... x D_K
				# Then, check whether the resourceIdentifier belongs to D_1 (the first domain of the cartesian product)

				if(resourceIdentifier in colorName._types[0]):
					
					# take number of components in the cartesian product (number of attributes that the tuple will have)
					k = len(colorName._types) # k is the resource dimensionality (number of attributes in the tuple)
					
					# this means then we take the k elements (attributes of the array) and we add it to our set of event resources
					# IMPORTANT: Notice here that indeed for each color, we have exactly one resource!
					
					tmpResource = []
					for j in range(k):
						aux = line[i + j].replace("\n","")
						if colorName._types[j] == tNatural:
							tmpResource.append(int(aux))
						elif colorName._types[j] == tNumber:
							tmpResource.append(float(aux))
						else:
							tmpResource.append(str(aux))

					self.eventResources[colorName] = tmpResource # Python method to get a fancy slice of the array. This gives us exactly k attributes, starting from position i of the line.
					# Update the iterator i by k steps to the right
					i = i + k

					# we have found the color of this resource, so we can break, and look up for the next resource
					break
				#end_if
			#end_for
		#end_while

def CPNSimpleReplayTuples(inputModel, initialPlaces, colors, eventLogFilename, modelFilename):

	nonFittingTraces = 0
	numberOfTraces = 0

	deviation1controlFlowDeviations = 0
	deviation2ruleViolations = 0
	deviation3resourcesCorruputed = 0

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

			# ==== LOOK FOR ALL DISTINCT RESOURCES IN THE TRACE ===
			distinctResources = []
			distinctResourceIdentifiers = [] # in this array, just collect ids. Like this, it will speed up the search :)
			for e in currentTrace:
				for rtype in e.eventResources: #for each type of resource in the set of resources of the event
					if (rtype, e.eventResources[rtype][0]) not in distinctResourceIdentifiers:
						distinctResourceIdentifiers.append((rtype , e.eventResources[rtype][0]))
						distinctResources.append((rtype, e.eventResources[rtype]))

			# === POPULATE INITIAL PLACES WITH ALL THE OBSERVED DISTINCT RESOURCES ===

			initialResourcesPerPlace = {}
			for placeType in initialPlaces:
				placeName  = initialPlaces[placeType]
				for (rtype, rvalue) in distinctResources:
					if rtype ==  placeType:
						if placeType not in initialResourcesPerPlace:
							initialResourcesPerPlace[placeType] = []
						initialResourcesPerPlace[placeType].append(tuple(rvalue))	

			for placeType in initialPlaces:
				placeName  = initialPlaces[placeType]
				#if currentTraceIdentifier == "3000209":
				#	print(placeName)
				#	print(placeType)
				if placeType in initialResourcesPerPlace:
					cpn.place(placeName).add(initialResourcesPerPlace[placeType])

			#cpn.draw("run.png")

			# === REPLAY SECTION ===
			# Take each event of the buffered trace

			deviationOccurred = False # "Innocent trace, till the opposite is proved :-)"

			for e in currentTrace:

				#print(e.eventAsLine)

				# SELECT TRANSITION TO FIRE ACCORDING TO ACTIVITY LABEL, e.g., t <- selectTransition(a)
				selectedTransition = None
				for t in cpn.transition():
					if e.activity == cpn.transition(str(t)).label("activity"):
						selectedTransition = str(t)
						break

				# DEVIATION 1: CHECK CONTROL-FLOW DEVIATION 
				# Grab identifiers of tokens of each input place
				tokenIdentifiers = {}

				for i in range(len(cpn.transition(selectedTransition).input())):
					p = str(cpn.transition(selectedTransition).input()[i][0])
					inputType = cpn.place(p).checker()
					tokenIdentifiers[inputType] = []
					for token in cpn.place(p).tokens:
						tokenIdentifiers[inputType].append(token[0])

				# Is it each event's observed resource in each input place of the transition to fire?
				for rtype in e.eventResources:
					# Checking if the identifier belongs to the set of available identifiers in the 
					# input place of type 'rtype'
					if e.eventResources[rtype][0] not in tokenIdentifiers[rtype]:
						# DEVIATION #1 FOUND!
						deviation1controlFlowDeviations = deviation1controlFlowDeviations + 1
						# Indicate in the file of deviations what happened
						comment = "resource with id: " + str(e.eventResources[rtype][0]) + " is not available."
						fileDeviations.write(str(e.traceIdentifier) + "," + str(e.timestamp) + "," + str(e.activity) + "," "CONTROL-FLOW" + "," + comment + "\n")	
						deviationOccurred = True

				if deviationOccurred == True:
					break

				# SELECT BINDING
				# If all input places of the transition to fire have required observed resources (identifiers)
				# then we select a selected binding with these resources
				resourceIds = []
				for rtype in e.eventResources:
					rId = e.eventResources[rtype][0]
					resourceIds.append(rId)
				# Select the "Substitution" (BINDING) where all resource identifiers are included (NOTE: Perhaps to be improved)
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

				# DEVIATION 2: CHECK RULE OVER INPUT PLACES OF TRANSITIONS!
				# Check if the transition to fire has a label "rule" activated
				if(cpn.transition(selectedTransition).has_label("rule")):
					# If the transition has a label "rule", then it means we need to check
					# whether a defined priority rule for each input place of the transition is being complied
					for i in range(len(cpn.transition(selectedTransition).input())):
						p = str(cpn.transition(selectedTransition).input()[i][0])
						pMarking = list(cpn.place(p).tokens) # transform the multiset in a list
						pType = cpn.place(p).checker()
						chosenToken = None
						for token in cpn.place(p).tokens:
							if token[0] == e.eventResources[pType][0]: # look for the token value according to the id
								chosenToken = token
								break

						# rules are to be verified in the "modelFilename" (TODO: To improve this way)
						placeRuleCheckerModule = imp.load_source('checkPlaceRule', modelFilename)
						ruleComplied = placeRuleCheckerModule.checkPlaceRule(placeName=p, selectedResource=chosenToken, placeMarking=pMarking)
						if(ruleComplied == False):
							deviation2ruleViolations = deviation2ruleViolations + 1
							comment = "resource with id: " + str(e.eventResources[pType][0]) + " does not have priority over other resources of the same class"
							fileDeviations.write(str(e.traceIdentifier) + "," + str(e.timestamp) + "," + str(e.activity) + "," "RULE-VIOLATION" + "," + comment + "\n")	
							deviationOccurred = True
							break
						#end_if
					#end_for
				#end_if <end of rule checking>

				if deviationOccurred == True:
					break

				# <<<< FIRE TRANSITION WITH SELECTED BINDING! >>>>
				#input(str("Fire: " + e.activity + "(" + selectedTransition + ") with resources: " + str(resourceIds)))
				#print(selectedTransition)
				#print(selectedBinding)
				#print(cpn.place("p6").tokens)
				cpn.transition(selectedTransition).fire(selectedBinding)
				#cpn.draw("run.png")
				
				# DEVIATION 3: CHECK IF RESOURCES CHANGED AS EXPECTED..
				# Now, we need to see whether each token in the output place has exactly the whole value of a resource
				for i in range(len(cpn.transition(selectedTransition).output())):
					p = str(cpn.transition(selectedTransition).output()[i][0]) # take output place
					outputType = cpn.place(p).checker() # take type of the output place
					for token in cpn.place(p).tokens:
						if token[0] == e.eventResources[outputType][0]:
							# Check whether resource with id token [0] has been modified as expected
							if(token != tuple(e.eventResources[outputType])):
								# DEVIATION #3 FOUND!
								# The whole tuple value of the resource in the place and in the event are different!
								deviation3resourcesCorruputed = deviation3resourcesCorruputed + 1
								comment = "resource with id: " + str(e.eventResources[outputType][0]) + " has observed state: " + str(tuple(e.eventResources[outputType])).replace(","," ") + " but expected state: " + str(token).replace(","," ") 
								fileDeviations.write(str(e.traceIdentifier) + "," + str(e.timestamp) + "," + str(e.activity) + "," "RESOURCE-CORRUPTED" + "," + comment + "\n")	
								deviationOccurred = True
								break
							#end_if
						#end_if
					#end_for
					if deviationOccurred == True:
						break
				#end_for

				if deviationOccurred == True:
					#cpn.draw("cpn.png")
					#exit()
					break

			# end_for <end of replaying events of a given trace>
			
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
		print("Control-flow deviations detected: " + str(deviation1controlFlowDeviations))
		print("Rule violations deviations detected: " + str(deviation2ruleViolations))
		print("Resource corruptions detected: " + str(deviation3resourcesCorruputed))
		print("")
		print("Event deviations written in file: " + eventDeviationsFilename)
		print("Non-fitting traces cloned to file: " + nonFittingTracesFilename)
		print("==========================================")
		print("")