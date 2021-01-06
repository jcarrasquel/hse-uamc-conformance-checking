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
numberOfArtificialResources = 1   # NUMBER OF RESOURCES PER CLASS
# ================================

# Resources (atomic data tokens) automatically generated of class A
resourcesClassA = []	# BUYERS AND SELLERS IN A SINGLE CLASS

def generateResources():
	for i in range(numberOfArtificialResources):
		
		# Creating agent with identifier r_i
		newResourceAName = "r" + str(i + 1)
		newResourceA = buildAgentTypeA(newResourceAName)
		resourcesClassA.append(newResourceA)
		newResourceA.draw("model_3_npn_simple_" + newResourceAName + ".png")


# Function to validate if a resource is from a specific agent class 
# For example, resources of class "TYPE_A" have identifiers with prefix "a"
def tTypeAId(val) :
	# in this case, "val" is a WF-net. The identifier of this agent is encapsulated in the attribute "name"
	if isinstance(val, PetriNet):
		return str(val.name[0]) == "r"
	else:
		return str(val[0]) == "r"

# --- METHODS FOR CREATING THE AGENT NETS (TOKEN NETS) ---
# Each method allows to create a net token of a specific class. This net token has the internal structure of a WF-net
# In each method, we define the structure of a class of agents.
# You shall create as many functions as agent classes are required

def buildAgentTypeA(agentIdentifier):

	agentNet = PetriNet(agentIdentifier)
	
	for i in range(4):
		p = Place("s" + str(i+1))
		agentNet.add_place(p)
		if i == 0:
			p.label(mark = "SOURCE")
			p.add([dot])
		elif i == 3:
			p.label(mark = "SINK")
		else:
			p.label(mark = None)

	activityLabels = ["agent_loginreq", "agent_loginres", "agent_logout"]
	synchronizationLabels = [None, "λ1", "λ2"]
	
	for i in range(3):
		t = Transition("u" + str(i+1))
		agentNet.add_transition(t)
		t.label(activity=activityLabels[i])
		t.label(synchronization=synchronizationLabels[i])

	agentNet.add_input("s1", "u1", Value(dot))
	agentNet.add_output("s2", "u1", Value(dot))
	agentNet.add_input("s2", "u2", Value(dot))
	agentNet.add_output("s3", "u2", Value(dot))
	agentNet.add_input("s3", "u3", Value(dot))
	agentNet.add_output("s4", "u3", Value(dot))

	return agentNet

# --- END OF THE DEFINITION OF AGENT NETS ---


# --- WRITE IN THIS METHOD THE PETRI NET (HERE WE CREATE THE "SYSTEM NET" OF THE NESTED PETRI NET) ---
def buildPetriNet():

	TYPE_A = TypeCheck(tTypeAId)

	# A KEY-VALUE MAP USED TO RETRIEVE DIFFERENT INFORMATION RELATED TO THE MODEL
	petriNetAttributes = {};

	# Append to this map, an array of all agent types used in the model
	petriNetAttributes["AGENT_TYPES"] = [TYPE_A];
	petriNetAttributes["AGENT_TEMPLATES"] = {TYPE_A: buildAgentTypeA}
  
	petriNet = PetriNet('3_npn_simple')

	# For conformance checking, initial place p1 shall be empty
	# But for generating artificial behavior, we populate place p1 and p2 with artificially generated orders
	if generateArtificialResources == True:
		generateResources()
		petriNet.add_place(Place("p1", resourcesClassA, TYPE_A))
	else:
		petriNet.add_place(Place("p1", [], TYPE_A))

	#Append to this map, a key-value map indicating the initial place (value) for resources of a given type (key)
	petriNetAttributes["INITIAL_PLACES"] = {TYPE_A: "p1"}

	petriNet.add_place(Place("p2", [], TYPE_A))
	petriNet.add_place(Place("p3", [], TYPE_A))

	# final places
	petriNetAttributes["FINAL_PLACES"] = {TYPE_A: "p3"}

	activityLabels = ["system_login", "system_logout", "system_test"] # activities that the system net executes
	synchronizationLabels = ["λ1", "λ2", None]

	for i in range(3):
		t = Transition("t" + str(i+1))
		petriNet.add_transition(t)
		t.label(activity=activityLabels[i])
		t.label(synchronization=synchronizationLabels[i])

	petriNet.add_input("p1", "t1", Variable("x"))
	petriNet.add_output("p2", "t1", Variable("x"))

	petriNet.add_input("p2", "t2", Variable("x"))
	petriNet.add_output("p3", "t2", Variable("x"))

	petriNet.add_input("p2", "t3", Variable("x"))
	petriNet.add_output("p2", "t3", Variable("x"))

	#petriNet.draw("model_3_npn_simple_system.png")

	return petriNet, petriNetAttributes

# ====================================================================
# ====================================================================
