# Template for Petri Net models

import snakes.plugins
snakes.plugins.load(["gv", "labels"], "snakes.nets", "nets")
from nets import *

# ====================================================================
# ====================================================================
# === WRITE HERE the SNAKE-based commands to create your Petri net ===
# NOTE: The PetriNetLoader will return the Petri net and type definitions, by importing this Python module.

# -- WRITE COLOR TYPES. CONVENTION: TYPE_NAME---
TYPE_A = tString
TYPE_B = tString

# --- RETURN TO THE PETRI NET LOADER WITH ALL COLOR TYPES ---
# --- Note: This function is irrelevant for generating artificial logs, but it may be important for conformance checking
def getColorTypes():
	colorTypes = [TYPE_A, TYPE_B]
	return colorTypes

# --- WRITE IN THIS METHOD THE PETRI NET ---
def buildPetriNet():	

	petriNet = PetriNet('my Colored Petri Net')

	# === CORRECT BEHAVIOR (based on model 1) ===

	petriNet.add_place(Place("p1", ["b1","b2","b3","b4","b5"], TYPE_A))
	petriNet.add_place(Place("p2", ["s1","s2","s3","s4","s5"], TYPE_B))
	petriNet.add_place(Place("p3", [], TYPE_A))
	petriNet.add_place(Place("p4", [], TYPE_B))
	petriNet.add_place(Place("p5", [], TYPE_A))
	petriNet.add_place(Place("p6", [], TYPE_B))
	petriNet.add_place(Place("p7", [], TYPE_A))
	petriNet.add_place(Place("p8", [], TYPE_B))

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
	petriNet.add_output("p7", "t4", Variable("x"))

	petriNet.add_input("p4", "t5", Variable("y"))
	petriNet.add_output("p8", "t5", Variable("y"))

	# === INCORRECT BEHAVIOR (now this model will do something more that according to model 1 should not be allowed ===

	t6 = Transition("t6")
	t7 = Transition("t7")
	t8 = Transition("t8")

	petriNet.add_place(Place("p9", [], TYPE_A))
	petriNet.add_place(Place("p10", [], TYPE_B))

	petriNet.add_transition(t6)
	petriNet.add_transition(t7)
	petriNet.add_transition(t8)
	t6.label(activity="cancelA")
	t7.label(activity="cancelB")
	t8.label(activity="trade")

	petriNet.add_input("p3", "t6", Variable("x"))
	petriNet.add_output("p9", "t6", Variable("x"))

	petriNet.add_input("p4", "t7", Variable("y"))
	petriNet.add_output("p10", "t7", Variable("y"))

	petriNet.add_input("p9", "t8", Variable("x"))
	petriNet.add_input("p10", "t8", Variable("y"))
	petriNet.add_output("p5", "t8", Variable("x"))
	petriNet.add_output("p6", "t8", Variable("y"))

	petriNet.draw("models/model_2_cpn_simple_incorrect.png")

	return petriNet

# ====================================================================
# ====================================================================