import imp

# The class PetriNetLoader is responsible for returning Petri net objects
# The Petri net object, is either constructed by a series of commands from a Python script,
# or it is loaded from an input text file (e.g., in PNML format)

MODEL_AS_INPUT_FILE = 1

MODEL_AS_PYTHON_SCRIPT = 2

class PetriNetLoader:

	# Returns a Petri net object
	# if option = MODEL_AS_INPUT_FILE, it loads a Petri net from an input file called "source".
	# if option = MODEL_AS_PYTHON_SCRIPT, it loads a Petri net from a python script called "source".
	def load(self,option, source):
		if option == MODEL_AS_INPUT_FILE:
			# TODO For future work :-)
			pass
		elif option == MODEL_AS_PYTHON_SCRIPT:
			
			print("Loading Petri net model from file: " + source)
			
			petriNetModule = imp.load_source('buildPetriNet', source)
			
			petriNet = petriNetModule.buildPetriNet() # taking Petri net from file

			print("Petri net successfully loaded!")
			
		else:
			print("Invalid option when loading a Petri net...")
			return None

		return petriNet