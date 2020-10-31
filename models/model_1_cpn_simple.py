# Template for Petri Net models

import snakes.plugins
snakes.plugins.load(["gv", "labels"], "snakes.nets", "nets")
from nets import *

# ====================================================================
# ====================================================================
# === WRITE HERE the SNAKE-based commands to create your Petri net ===
# NOTE: The PetriNetLoader will return the Petri net and type definitions, by importing this Python module.

# PATCH ==========================
# With this option, we are going to populate the given petri net with 
# a certain number of resources randomly generated (option just for artificial log generation, not conformance)
generateArtificialResources = False # This model will be used for conformance checking, not for generation
numberOfArtificialResources = 3 # NUMBER OF RESOURCES PER CLASS
# ================================

# Resources (atomic data tokens) automatically generated
resourcesClassA = []
resourcesClassB = []

def generateResources():
	for i in range(numberOfArtificialResources):

		newResourceA = "a" + str(i + 1)
		newResourceB = "b" + str(i + 1)

		resourcesClassA.append(newResourceA)
		resourcesClassB.append(newResourceB)


# Function to validate if a resource is from a specific color class 
# For example, resources of class "TYPE_A" have identifiers with prefix "a"
def tTypeAId(val) :
	return str(val[0]) == "a"

def tTypeBId(val) :
	return str(val[0]) == "b"

# --- WRITE IN THIS METHOD THE PETRI NET ---
def buildPetriNet():

	TYPE_A = TypeCheck(tTypeAId)
	TYPE_B = TypeCheck(tTypeBId)

	# A KEY-VALUE MAP USED TO RETRIEVE DIFFERENT INFORMATION RELATED TO THE MODEL
	petriNetAttributes = {};

	# Append to this map, an array of all color types used in the model
	petriNetAttributes["COLOR_TYPES"] = [TYPE_A, TYPE_B];

	petriNet = PetriNet('1_cpn_simple')

	# For conformance checking, initial places p1 and p2 shall be empty
	# But for generating artificial behavior, we populate places p1 and p2 with artificially generated orders
	if generateArtificialResources == True:
		generateResources()
		petriNet.add_place(Place("p1", resourcesClassA, TYPE_A))
		petriNet.add_place(Place("p2", resourcesClassB, TYPE_B))
	else:
		petriNet.add_place(Place("p1", [], TYPE_A))
		petriNet.add_place(Place("p2", [], TYPE_B))

	#Append to this map, a key-value map indicating the initial place (value) for resources of a given type (key)
	petriNetAttributes["INITIAL_PLACES"] = {TYPE_A: "p1", TYPE_B: "p2"}

	petriNet.add_place(Place("p3", [], TYPE_A))
	petriNet.add_place(Place("p4", [], TYPE_B))
	petriNet.add_place(Place("p5", [], TYPE_A))
	petriNet.add_place(Place("p6", [], TYPE_B))

	activityLabels = ["submitA", "submitB", "trade", "cancelA", "cancelB"]
	for i in range(5):
		t = Transition("t" + str(i+1))
		petriNet.add_transition(t)
		t.label(activity=activityLabels[i])

	petriNet.add_input("p1", "t1", Variable("x"))
	petriNet.add_output("p3", "t1", Variable("x"))

	petriNet.add_input("p2", "t2", Variable("y"))
	petriNet.add_output("p4", "t2", Variable("y"))

	petriNet.add_input("p3", "t3", Variable("x"))
	petriNet.add_input("p4", "t3", Variable("y"))
	petriNet.add_output("p5", "t3", Variable("x"))
	petriNet.add_output("p6", "t3", Variable("y"))

	petriNet.add_input("p3", "t4", Variable("x"))
	petriNet.add_output("p5", "t4", Variable("x"))

	petriNet.add_input("p4", "t5", Variable("y"))
	petriNet.add_output("p6", "t5", Variable("y"))

	#petriNet.draw("model_1_cpn_simple.png")

	return petriNet, petriNetAttributes

# ====================================================================
# ====================================================================