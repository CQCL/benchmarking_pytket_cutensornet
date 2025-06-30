from pathlib import Path
import json

################################
## Preparing the METRICS file ##
################################

with open("templates/METRICS.csv", "r") as f:
  lines = list(f.readlines())
  header = lines[0]
  circnames = [l.split(",")[0] for l in lines[1:]]

with open("METRICS.csv", "w") as fout:
  fout.write(header)
  for c in circnames:
    line = c + ","

    found_at = list()
    for subdir in Path("settings").iterdir():
      path_to_circ = subdir / "metrics" / (c + ".txt")
      if path_to_circ.exists():
        found_at.append(path_to_circ)
    assert len(found_at) <= 1
    was_run = len(found_at) == 1

    # Mirror fidelity
    if was_run:
      with open(found_at[0], "r") as fin:
        for inp_line in fin.readlines():
          if "mirror_fidelity" in inp_line:
            value = inp_line.split("=")[-1].strip()
            line += value
    line += ","

    # Fidelity estimate
    if was_run:
      with open(found_at[0], "r") as fin:
        for inp_line in fin.readlines():
          if "fidelity_estimate" in inp_line:
            value = inp_line.split("=")[-1].strip()
            line += value
    line += ","

    # Total runtime, simulation time, preprocessing time, shot time
    if was_run:
      with open(found_at[0], "r") as fin:
        for inp_line in fin.readlines():
          if "simulation_time" in inp_line:
            value = inp_line.split("=")[-1].strip()
            simulation_time = float(value)
          if "shot_time" in inp_line:
            value = inp_line.split("=")[-1].strip()
            shot_time = float(value)
      total_time = simulation_time + shot_time
      line += f"{total_time},{simulation_time},0.0,{shot_time},"
    else:
      line += ",,,,"

    # Expectation value time
    if was_run:
      with open(found_at[0], "r") as fin:
        for inp_line in fin.readlines():
          if "expectation_value_time" in inp_line:
            value = inp_line.split("=")[-1].strip()
            line += value
    line += ","

    # Other time
    if was_run:
      line += "0.0"
    line += ","

    # Final state memory
    if was_run:
      with open(found_at[0], "r") as fin:
        for inp_line in fin.readlines():
          if "final_state_memory" in inp_line:
            value = int(inp_line.split("=")[-1].strip())
            line += str(value / 2**20)

    line += "\n"
    fout.write(line)


################################
## Preparing the SHOTS file ##
################################

shots_dict = {c: list() for c in circnames}

for c in circnames:
  found_at = list()
  for subdir in Path("settings").iterdir():
    path_to_circ = subdir / "shots" / (c + ".txt")
    if path_to_circ.exists():
      found_at.append(path_to_circ)
  assert len(found_at) <= 1
  was_run = len(found_at) == 1

  if was_run:
    with open(found_at[0], "r") as f:
      shots = list(f.readlines())
      shots = [s.strip() for s in shots]
    shots_dict[c] = shots

with open("SHOTS.json", "w") as f:
  json.dump(shots_dict, f, indent=4)


################################
## Preparing the EXP_VAL file ##
################################

with open("templates/EXP_VAL.json", "r") as f:
  expval_dict = json.load(f)

for c, paulistr in expval_dict.items():
  found_at = list()
  for subdir in Path("settings").iterdir():
    path_to_circ = subdir / "expvals" / (c + ".json")
    if path_to_circ.exists():
      found_at.append(path_to_circ)
  assert len(found_at) <= 1
  was_run = len(found_at) == 1

  if was_run:
    with open(found_at[0], "r") as f:
      c_expvals = json.load(f)
    assert set(c_expvals.keys()) == set(paulistr.keys())
    expval_dict[c] = c_expvals

with open("EXP_VAL.json", "w") as f:
  json.dump(expval_dict, f, indent=4)
