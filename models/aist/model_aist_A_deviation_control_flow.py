# Template for Petri Net models

import snakes.plugins
snakes.plugins.load(["gv", "labels"], "snakes.nets", "nets")
from nets import *
from random import randint

# PATCH ==========================
# With this option, we are going
# to populate the given petri net
# with a certain number of resources
# randomly generated.
generateArtificialResources = True # Toggle value if this model is used for conformance checking
numberOfArtificialResources = 5
# ================================

# ====================================================================
# ====================================================================
# === WRITE HERE the SNAKE-based commands to create your Petri net ===
# NOTE: The PetriNetLoader will return the Petri net and type definitions, by importing this Python module.

randomBuyOrders = []
randomSellOrders = []

def generateRandomOrders():

	sellOrderCounter = 1
	buyOrderCounter = 1
	arrivalTime = 1

	for i in range(numberOfArtificialResources):
		buyOrderIdentifier = "b" + str(buyOrderCounter)
		buyOrderArrivalTime = arrivalTime
		buyOrderPrice = randint(20,40) # generating buy orders with price between 20 and 40 dollars per stock
		buyOrderQty = randint(1,5)  # generating buy orders with quantity with stock size between 1 and 5

		buyOrder = (buyOrderIdentifier, buyOrderArrivalTime, buyOrderPrice, buyOrderQty)

		buyOrderCounter = buyOrderCounter + 1
		arrivalTime = arrivalTime + 1

		sellOrderIdentifier = "s" + str(sellOrderCounter)
		sellOrderArrivalTime = arrivalTime
		sellOrderPrice = randint(20,40) # generating sell orders with price between 20 and 40 dollars per stock
		sellOrderQty = randint(1,5)  # generating sell orders with quantity with stock size between 1 and 5

		sellOrder = (sellOrderIdentifier, sellOrderArrivalTime, sellOrderPrice, sellOrderQty)

		sellOrderCounter = sellOrderCounter + 1
		arrivalTime = arrivalTime + 1

		randomBuyOrders.append(tuple(buyOrder))
		randomSellOrders.append(tuple(sellOrder))

	#end_for

def checkPlaceRule(placeName, selectedResource, placeMarking):
	if placeName == "p5":
		return buyPriorityRule(selectedResource, placeMarking)
	elif placeName == "p6":
		return sellPriorityRule(selectedResource, placeMarking)
	else:
		print("Error: No rule defined for this place")
		return False

def buyPriorityRule(buyOrder, orderBookBuySide):

	# This function returns true if buyOrder is the highest ranked order in the buy side of the order book, false otherwise
	orderPrice = buyOrder[2]
	orderArrivalTime = buyOrder[1]
	orderIdentifier = buyOrder[0]

	ishighestRankedBuyOrder = True # "He is innocent, till we demonstrate the opposite" For now, we believe he is the highest ranked order

	for i in range(len(orderBookBuySide)):
		nextBuyOrder = orderBookBuySide[i]
		if nextBuyOrder[0] != orderIdentifier: # check that we are not checking the same order
			if not( (orderPrice > nextBuyOrder[2]) or (orderPrice == nextBuyOrder[2] and orderArrivalTime <= nextBuyOrder[1])):
				# Priority rule, violated
				ishighestRankedBuyOrder = False
				break

	return ishighestRankedBuyOrder == True


def sellPriorityRule(sellOrder, orderBookSellSide):
	# This function returns true if sellOrder is the highest ranked order in the sell side of the order book, false otherwise

	# This function returns true if buyOrder is the highest ranked order in the buy side of the order book, false otherwise
	orderPrice = sellOrder[2]
	orderArrivalTime = sellOrder[1]
	orderIdentifier = sellOrder[0]

	ishighestRankedSellOrder = True # "He is innocent, till we demonstrate the opposite" For now, we believe he is the highest ranked order

	for i in range(len(orderBookSellSide)):
		nextSellOrder = orderBookSellSide[i]
		if nextSellOrder[0] != orderIdentifier: # check that we are not checking the same order
			if not( (orderPrice < nextSellOrder[2]) or (orderPrice == nextSellOrder[2] and orderArrivalTime <= nextSellOrder[1])):
				# Priority rule, violated
				ishighestRankedSellOrder = False
				break
				
	return ishighestRankedSellOrder == True

def tBuyOrderId(val) :
	return str(val[0]) == "b"

def tSellOrderId(val) :
	return str(val[0]) == "s"

# --- WRITE IN THIS METHOD THE PETRI NET ---
def buildPetriNet():

#	BUY_ORDER_IDENTIFIERS = []
#	SELL_ORDER_IDENTIFIERS = []

	#for i in range(numberOfUniqueIds):
	#	BUY_ORDER_IDENTIFIERS.append("b" + str(i + 1))
	#	SELL_ORDER_IDENTIFIERS.append("s" + str(i + 1))

	# UPDATING THE DOMAIN (set of possible values) OF OUR "COLOR TYPES"
	TYPE_BUYER = CrossProduct(TypeCheck(tBuyOrderId), tNumber, tNumber, tNumber)
	TYPE_SELLER = CrossProduct(TypeCheck(tSellOrderId), tNumber, tNumber, tNumber)

	# === A KEY-VALUE MAP USED TO RETRIEVE DIFFERENT INFORMATION RELATED TO THE MODEL ===
	petriNetAttributes = {};

	# Append to this map, an array of all color types used in the model
	petriNetAttributes["COLOR_TYPES"] = [TYPE_BUYER, TYPE_SELLER];

	petriNet = PetriNet('A_deviation_control_flow')

	#petriNet.add_place(Place("p1", [("b1",1,20.0,4),("b2",2,20.0,4)], TYPE_BUYER))
	#petriNet.add_place(Place("p2", [("s1",3,20.0,4),("s2",4,20.0,4)], TYPE_SELLER))
	#petriNet.add_place(Place("p1", [], TYPE_BUYER))
	#petriNet.add_place(Place("p2", [], TYPE_SELLER))

	# For conformance checking, initial places p1 and p2 shall be empty
	# But for generating artificial behavior, we populate places p1 and p2 with randomly generated orders
	if generateArtificialResources == True:
		generateRandomOrders()
		petriNet.add_place(Place("p1", randomBuyOrders, TYPE_BUYER))
		petriNet.add_place(Place("p2", randomSellOrders, TYPE_SELLER))
	else:
		petriNet.add_place(Place("p1", [], TYPE_BUYER))
		petriNet.add_place(Place("p2", [], TYPE_SELLER))

	#Append to this map, a key-value map indicating the initial place (value) for resources of a given type (key)
	petriNetAttributes["INITIAL_PLACES"] = {TYPE_BUYER: "p1", TYPE_SELLER: "p2"}

	petriNet.add_place(Place("p3", [], TYPE_BUYER))
	petriNet.add_place(Place("p4", [], TYPE_SELLER))

	# Order book buy and sell sides
	petriNet.add_place(Place("p5", [], TYPE_BUYER)) # Order book buy side
	# When a transition with an activated "rule" label fires, the prority rule of this place will be invoked

	petriNet.add_place(Place("p6", [], TYPE_SELLER)) # Order book sell side
	# When a transition with an activated "rule" label fires, the prority rule of this place will be invoked

	petriNet.add_place(Place("p7", [], TYPE_BUYER))
	petriNet.add_place(Place("p8", [], TYPE_SELLER))

	activityLabels = ["submit buy order", "submit sell order", "new buy order", "new sell order", "trade1", "trade2", "trade3",
	"discard buy order", "discard sell order", "discard buy order", "discard sell order"]

	for i in range(11):
		if generateArtificialResources == True:
			# For the case of artificial generation of behavior, control a bit more the trade activity using a guard
			if i+1 == 10:
				t = Transition("t" + str(i+1), Expression("q1 > 0"))
			elif i+1 == 11:
				t = Transition("t" + str(i+1), Expression("q2 > 0"))
			elif i+1 == 6:
				t = Transition("t" + str(i+1), Expression("(pr1 > pr2 or (pr1 == pr2 and ts1 >= ts2)) and q1 > q2"))
			elif i+1 == 7:
				t = Transition("t" + str(i+1), Expression("(pr1 > pr2 or (pr1 == pr2 and ts1 >= ts2)) and q2 > q1"))
			elif i+1 == 5:
				t = Transition("t" + str(i+1), Expression("(pr1 > pr2 or (pr1 == pr2 and ts1 >= ts2)) and q2 == q1"))
			else:
				# If the model is for conformance checking, do not add guards on transitions (CPN definition in AIST Paper)
				t = Transition("t" + str(i+1))
		else:
			t = Transition("t" + str(i+1))
		#end_if
		
		petriNet.add_transition(t)
		t.label(activity=activityLabels[i])
		if(i + 1 == 5 or i + 1 == 6 or i + 1 == 7):
			# For trade transitions, activate a mark, that a priority rule needs to be checked on input places
			t.label(rule = True)
		#end_if
	#end_for

	# input/output of t1 - submit buy order
	petriNet.add_input("p1", "t1", Tuple([Variable("o1"), Variable("ts1"), Variable("pr1"), Variable("q1")]))
	petriNet.add_output("p3", "t1", Tuple([Variable("o1"), Variable("ts1"), Variable("pr1"), Variable("q1")]))

	# input/output of t3 - new buy order
	petriNet.add_input("p3", "t3", Tuple([Variable("o1"), Variable("ts1"), Variable("pr1"), Variable("q1")]))
	petriNet.add_output("p5", "t3", Tuple([Variable("o1"), Variable("ts1"), Variable("pr1"), Variable("q1")]))

	# input/output of t2 - submit sell order
	petriNet.add_input("p2", "t2", Tuple([Variable("o2"), Variable("ts2"), Variable("pr2"), Variable("q2")]))
	petriNet.add_output("p4", "t2", Tuple([Variable("o2"), Variable("ts2"), Variable("pr2"), Variable("q2")]))

	# input/output of t4 - new sell order
	petriNet.add_input("p4", "t4", Tuple([Variable("o2"), Variable("ts2"), Variable("pr2"), Variable("q2")]))
	petriNet.add_output("p6", "t4", Tuple([Variable("o2"), Variable("ts2"), Variable("pr2"), Variable("q2")]))

	# input/output of t5 - trade1
	petriNet.add_input("p5", "t5", Tuple([Variable("o1"), Variable("ts1"), Variable("pr1"), Variable("q1")]))
	petriNet.add_input("p6", "t5", Tuple([Variable("o2"), Variable("ts2"), Variable("pr2"), Variable("q2")]))
	petriNet.add_output("p7", "t5", Tuple([Variable("o1"), Variable("ts1"), Variable("pr1"), Value(0)]))
	petriNet.add_output("p8", "t5", Tuple([Variable("o2"), Variable("ts2"), Variable("pr2"), Value(0)]))

	# input/output of t6 - trade2
	petriNet.add_input("p5", "t6", Tuple([Variable("o1"), Variable("ts1"), Variable("pr1"), Variable("q1")]))
	petriNet.add_input("p6", "t6", Tuple([Variable("o2"), Variable("ts2"), Variable("pr2"), Variable("q2")]))
	petriNet.add_output("p5", "t6", Tuple([Variable("o1"), Variable("ts1"), Variable("pr1"), Expression("q1-q2")]))
	petriNet.add_output("p8", "t6", Tuple([Variable("o2"), Variable("ts2"), Variable("pr2"), Value(0)]))

	# input/output of t7 - trade3
	petriNet.add_input("p5", "t7", Tuple([Variable("o1"), Variable("ts1"), Variable("pr1"), Variable("q1")]))
	petriNet.add_input("p6", "t7", Tuple([Variable("o2"), Variable("ts2"), Variable("pr2"), Variable("q2")]))
	petriNet.add_output("p6", "t7", Tuple([Variable("o2"), Variable("ts2"), Variable("pr2"), Expression("q2-q1")]))
	petriNet.add_output("p7", "t7", Tuple([Variable("o1"), Variable("ts1"), Variable("pr1"), Value(0)]))

	# input/output of t8 - discard buy order
	petriNet.add_input("p5", "t8", Tuple([Variable("o1"), Variable("ts1"), Variable("pr1"), Variable("q1")]))
	petriNet.add_output("p7", "t8", Tuple([Variable("o1"), Variable("ts1"), Variable("pr1"), Value(0)]))

	# input/output of t9 - discard sell order
	petriNet.add_input("p6", "t9", Tuple([Variable("o2"), Variable("ts2"), Variable("pr2"), Variable("q2")]))
	petriNet.add_output("p8", "t9", Tuple([Variable("o2"), Variable("ts2"), Variable("pr2"), Value(0)]))

	# ===== INCORRECT BEHAVIOR ======
	# Sometimes, the execution of discard buy and sell orders have no effect. Orders may stay on the order book and trade (not good)

	# input/output of t8 - discard buy order
	petriNet.add_input("p5", "t10", Tuple([Variable("o1"), Variable("ts1"), Variable("pr1"), Variable("q1")]))
	petriNet.add_output("p5", "t10", Tuple([Variable("o1"), Variable("ts1"), Variable("pr1"), Value(0)]))

	# input/output of t9 - discard sell order
	petriNet.add_input("p6", "t11", Tuple([Variable("o2"), Variable("ts2"), Variable("pr2"), Variable("q2")]))
	petriNet.add_output("p6", "t11", Tuple([Variable("o2"), Variable("ts2"), Variable("pr2"), Value(0)]))	

	# petriNet.draw("model_aist_B_deviation_control_flow.png")

	return petriNet, petriNetAttributes

# ====================================================================
# ====================================================================