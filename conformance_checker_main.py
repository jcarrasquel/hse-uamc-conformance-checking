import sys
from petri_net_loader import *
import snakes.plugins
snakes.plugins.load(["gv", "labels"], "snakes.nets", "nets")
import random
from nets import *
from datetime import datetime, timedelta
import imp

# ================================
# === Conformance Checker Main ===
# Performs a conformance checking method
# The method is specified by the user, and must be implemented as python script in folder conformane_checking/
# Then, it invokes the specified method taking as paremeter an input Petri net model and an event log
# CALL EXAMPLE: python conformance_checker_main.py method_number "somewhere/models/mymodel.py" "somewhere/event_logs/my_log.xxx"
# method_number is one of the following options:

# OPTIONS OF IMPLEMENTED CONFORMANCE CHECKING METHODS

CPN_SIMPLE_REPLAY_TUPLES = 0; # paper AIST 2020

CPN_MOVETOKENS_REPLAY_ATOMICVALUES = 1; # journal work on progress...

NPN_MOVETOKENS_REPLAY_NETTOKENS_DIRECT = 2; # journal work on progress...

# === BEGIN MAIN ===
print("")
print("========== CONFORMANCE CHECKER v1.0 ==========")
print("National Research University Higher School of Economics, Moscow, Russia.")
print("Laboratory of Process-Aware Information Systems (PAIS Lab)")
print("University of Constantine 2. Abdelhamid Mehri, Constantine, Algeria.")
print("January 2020")
print("==============================================")
print("")

conformanceCheckingMethod = int(sys.argv[1])

modelFilename = sys.argv[2]

eventLogFilename = sys.argv[3]

petriNetLoader = PetriNetLoader()

petriNet, modelAttributes = petriNetLoader.load(MODEL_AS_PYTHON_SCRIPT, modelFilename)

print("PETRI NET MODEL: " + modelFilename)
print("EVENT LOG: " + eventLogFilename)

if conformanceCheckingMethod == CPN_SIMPLE_REPLAY_TUPLES: # AIST 2020
	
	print("CONFORMANCE METHOD: " + "CPN Simple Replay with Complex Tuples (AIST)")

	conformanceModule = imp.load_source('CPNSimpleReplayTuples', 'conformance_checking/cpn_simple_replay_tuples.py')

	initialPlaces = modelAttributes["INITIAL_PLACES"]

	colors = modelAttributes["COLOR_TYPES"]

	conformanceModule.CPNSimpleReplayTuples(petriNet, initialPlaces, colors, eventLogFilename, modelFilename)
#end_if

if conformanceCheckingMethod == CPN_MOVETOKENS_REPLAY_ATOMICVALUES: # JOURNAL PAPER IN PROGRESS...

	print("CONFORMANCE METHOD: " + "CPN Moving-Tokens Replay with Atomic Data Tokens")

	conformanceModule = imp.load_source('CPNJumpReplayAtomicDataTokens', 'conformance_checking/cpn_replay_simple.py')

	initialPlaces = modelAttributes["INITIAL_PLACES"]

	colors = modelAttributes["COLOR_TYPES"]

	conformanceModule.CPNJumpReplayAtomicDataTokens(petriNet, initialPlaces, colors, eventLogFilename, modelFilename)
#end_if

if conformanceCheckingMethod == NPN_MOVETOKENS_REPLAY_NETTOKENS_DIRECT: # JOURNAL PAPER IN PROGRESS...

	print("CONFORMANCE METHOD: " + "Nested Petri Nets - Moving-Tokens Replay with Net Tokens (Direct Approach)")

	conformanceModule = imp.load_source('CPNJumpReplayAtomicDataTokens', 'conformance_checking/npn_replay_direct.py')

	initialPlaces = modelAttributes["INITIAL_PLACES"]

	finalPlaces = modelAttributes["FINAL_PLACES"]

	agentClasses = modelAttributes["AGENT_TYPES"]

	agentTemplates = modelAttributes["AGENT_TEMPLATES"]

	conformanceModule.NPNDirectReplay(petriNet, initialPlaces, finalPlaces, agentClasses, eventLogFilename, modelFilename, agentTemplates)
#end_if

# ========= END MAIN =========