import snakes.plugins
snakes.plugins.load(["gv", "labels"], "snakes.nets", "nets")
from nets import *

def draw_transition(trans, attr):

	if trans.label("synchronization") != None:
		labelToDisplay = trans.label("activity") + "\n" + trans.label("synchronization")
	else:
		labelToDisplay = trans.label("activity")

	attr['label'] = labelToDisplay

def draw_net(petriNet, fileName):
	petriNet.draw(fileName, trans_attr=draw_transition)
