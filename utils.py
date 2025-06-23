import sys
from pathlib import Path


def get_metric(metric_name: str, metric_file: Path) -> float:
  with open(metric_file, "r") as f:
    ls = f.readlines()
    fid = [float(l.split(f"{metric_name}=")[1]) for l in ls if metric_name in l]
    if len(fid) == 1:
      return fid[0]
    elif len(fid) == 0:
      return -1.0
    else:
      raise Exception(f"Something went wrong, there are multiple {metric_name} for {metric_file}: {fid}")


if __name__ == "__main__":
  option = sys.argv[1]
  match option:
    case "--order-by-fidelity":
      path = Path(sys.argv[2]) / "metrics"
      circ_with_fidelity = list()  # A list of tuples
      for filepath in path.iterdir():
        circname = str(filepath).split("/")[-1].split(".txt")[0]
        mirror_fidelity = get_metric("mirror_fidelity", filepath)
        sim_time = get_metric("simulation_time", filepath)
        circ_with_fidelity.append((circname, mirror_fidelity, sim_time))
      circ_with_fidelity.sort(key=lambda p: p[1])
      for circ, fid, t in circ_with_fidelity:
        print(f"{circ}: {fid} (sim: {round(t,2)}s)")
    case "--get-fidelity":
      circ_list = Path(sys.argv[2])
      metric_path = Path(sys.argv[3]) / "metrics"
      with open(circ_list, "r") as f:
        lines = f.readlines()
      circs = list(map(lambda s: s[:-1], lines))
      circ_with_fidelity = list()  # A list of tuples
      for filepath in metric_path.iterdir():
        circname = str(filepath).split("/")[-1].split(".txt")[0]
        if circname in circs:
          mirror_fidelity = get_metric("mirror_fidelity", filepath)
          sim_time = get_metric("simulation_time", filepath)
          circ_with_fidelity.append((circname, mirror_fidelity, sim_time))
      circ_with_fidelity.sort(key=lambda p: p[1])
      for circ, fid, t in circ_with_fidelity:
        print(f"{circ}: {fid} (sim: {round(t,2)}s)")
    case "--find-band":
      min = float(sys.argv[2])
      max = float(sys.argv[3])
      for settings_subdir in Path("settings").iterdir():
        for metrics_file in (settings_subdir / "metrics").iterdir():
          with open(metrics_file, "r") as f:
            lines = f.readlines()
            mirror_fid_line = lines[-1].strip()
            if "mirror_fidelity" not in mirror_fid_line:  # For t_injection circuits
              continue
            mirror_fidelity = float(mirror_fid_line.split("=")[-1])
            if mirror_fidelity >= min and mirror_fidelity < max:
              circname = str(metrics_file).split("/")[-1].split(".txt")[0]
              print(circname)
    case _:
      print(f"Unrecognised option {option}")
