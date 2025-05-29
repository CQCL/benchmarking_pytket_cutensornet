import sys
import json
import pickle
from pathlib import Path
from pytket import Circuit
from pytket.pauli import Pauli, QubitPauliString
from pytket.extensions.cutensornet.structured_state import MPS, simulate, SimulationAlgorithm, Config, CuTensorNetHandle
from time import time
import logging

orig_circ_dir = Path("challenge_files/attachments/circuit_suite/pytket_orig")
dagger_circ_dir = Path("challenge_files/attachments/dagger_circuits/pytket_orig")

# Capture inputs
args = sys.argv[1].split(" ")
gpu_id = int(args[0])
settings_dir = Path(args[1])
circname = args[2]

# Guarantee that the necessary directories exist
(settings_dir / "logs").mkdir(exist_ok=True)
(settings_dir / "saved_mps").mkdir(exist_ok=True)
(settings_dir / "metrics").mkdir(exist_ok=True)
(settings_dir / "shots").mkdir(exist_ok=True)
(settings_dir / "expvals").mkdir(exist_ok=True)
metric_file = settings_dir / "metrics" / (circname + ".txt")

# Create the configuration object
with open(settings_dir / "config.json", "r") as f:
  config_params = json.load(f)
cfg = Config(
  seed=1234,
  loglevel=20,
  logfile=str(settings_dir / "logs" / (circname+".log")),
  **config_params
)

# Load the circuit
with open(orig_circ_dir / (circname+".json"), "r") as f:
  circ = Circuit.from_dict(json.load(f))

# Simulate
start_time = time()
with CuTensorNetHandle(gpu_id) as libhandle:
  mps = simulate(libhandle, circ, SimulationAlgorithm.MPSxGate, cfg)
  sim_duration = time() - start_time

  # Save basic metric info
  with open(metric_file, "w") as f:
    f.write(f"fidelity_estimate={mps.fidelity}\n")
    f.write(f"simulation_time={sim_duration}\n")
    f.write(f"final_state_memory={mps.get_byte_size()}\n")

  # Save MPS
  with open(settings_dir / "saved_mps" / (circname+".pkl"), "wb") as f:
    pickle.dump(mps, f)

  # Run shots
  start_time = time()
  shots = [mps.sample() for _ in range(100)]
  shot_duration = time() - start_time
  with open(metric_file, "a") as f:
    f.write(f"shot_time={shot_duration}\n")
  with open(settings_dir / "shots" / (circname+".txt"), "w") as f:
    for shot_d in shots:
      shot_tups = sorted([(str(q), val) for q, val in shot_d.items()], key=lambda p: p[0])
      shot_str = "".join(str(tup[1]) for tup in shot_tups)
      f.write(f"{shot_str}\n")

  # Get expectation values
  def to_pauli_list(paulistr: str) -> list[Pauli]:
    pauli_list = list()
    for p in paulistr:
      match p:
        case "I": pauli_list.append(Pauli.I)
        case "X": pauli_list.append(Pauli.X)
        case "Y": pauli_list.append(Pauli.Y)
        case "Z": pauli_list.append(Pauli.Z)
        case "_": raise Exception(f"Not recognised Pauli: {p}")
    return pauli_list
  ordered_qubits = sorted(list(circ.qubits))
  with open("challenge_files/attachments/EXP_VAL.json", "r") as f:
    paulistr_full_dict = json.load(f)
  requested_paulistr = list(paulistr_full_dict[circname].keys())
  paulistr_to_pytket = {paulistr: QubitPauliString(ordered_qubits, to_pauli_list(paulistr)) for paulistr in requested_paulistr}
  # Now that we've gathered the expectation values that we want to obtain, calculate them
  start_time = time()
  this_expval_dict = dict()
  for paulistr, paulistr_pytket in paulistr_to_pytket.items():
    this_expval_dict[paulistr] = mps.expectation_value(paulistr_pytket)
  expval_duration = time() - start_time
  with open(metric_file, "a") as f:
    f.write(f"expectation_value_time={expval_duration}\n")
  with open(settings_dir / "expvals" / (circname+".json"), "w") as f:
    json.dump(this_expval_dict, f, indent=4)

  # Mirror fidelity
  with open(dagger_circ_dir / (circname+".json"), "r") as f:
    dagger_circ = Circuit.from_dict(json.load(f))
  for gate in dagger_circ.get_commands():
    mps.apply_gate(gate)
  zero_mps = MPS(libhandle, dagger_circ.qubits, Config())  # |0>
  mirror_fidelity = abs(mps.vdot(zero_mps)) ** 2
  with open(metric_file, "a") as f:
    f.write(f"mirror_fidelity={mirror_fidelity}\n")
