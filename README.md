##  Conformance Checking with Colored Petri Nets and Nested Petri Nets

### Authors:

- Khalil Mecheraoui - k_mecheraoui@esi.dz
- [Julio C. Carrasquel](https://www.hse.ru/staff/jcarrasquel) - jcarrasquel@hse.ru
- Irina A. Lomazova - ilomazova@hse.ru

*National Research University Higher School of Economics, Moscow, Russia.*<br>
*University of Constantine 2 — Abdelhamid Mehri, Constantine, Algeria.*

---
For quick testing, download the repository and execute any of the methods below. The methods have been tested with Python v3.5.
A method is invoked by the script `conformance_checker_main.py` using an integer value as a first argument (see examples below)
The next arguments are the Petri net model (coded using SNAKES) and an event log in CSV format.

### Conformance Checking Methods

- **Replay of CPNs with tuple-style tokens and complex arc expressions (AIST-2020)**

    - Command example: `python3 conformance_checker_main.py 0 models/aist/model_aist_0_correct_specification.py event_logs/aist/demo/eventlog_real_example0_deviation_ALL.csv` 

- **Replay of CPNs with atomic tokens using a** ***token jump heuristic***
    - Command example: `python3 conformance_checker_main.py 1 models/model_1_cpn_simple.py event_logs/eventlog_simple_incorrect.csv`

- **Replay of NPNs using a** ***token jump heuristic***
    - Command example: `python3 conformance_checker_main.py 2 models/model_3_npn_simple.py event_logs/eventlog_multiagentsystem_example.csv`

### Useful resources:

* Checking Conformance between Colored Petri Nets and Event Logs (AIST-2020) [[Slides]](https://drive.google.com/file/d/1UONWeWZKMFw6n9trU4hxREWnynPxsKaA/view) [[Paper]](https://drive.google.com/file/d/175HBPYy9jXDtSQ_SE4CeqyoG41KNkYdm/view) [[Talk]](https://www.youtube.com/watch?v=Qkr9D7KXHno)

---

### A General Note on our Research Project:

In this project, we research on novel conformance checking methods, which
use rich Petri net extension models, namely Colored Petri Nets and Nested Petri Nets.
Traditionally, standard conformance checking methods merely focus on the validation of system's control-flow
(e.g., whether systems comply certain causal dependences between activities). Tackling such limitation, we focus
on the development on more clever approaches that can validate correct processing of data resources, as well
as correct agent interaction. The mentioned Petri net extension models allow to formally specify such agent- and
data-related aspects that a system shall comply. Then, with our methods, we aim to sistematically compare these kinds of 
Petri net models (expected behavior) again event logs, which record the observed behavior of systems. 
