import os
import glob
import pandas as pd
import matplotlib.pyplot as plt

def parse_log_file(filename):
    """
    Parse a log file where each line is tab-delimited:
    elapsed time, event, "Logical Clock: X", details
    """
    times = []
    clocks = []
    with open(filename, "r") as f:
        for line in f:
            parts = line.strip().split("\t")
            # Remove any empty strings from splitting.
            parts = [p for p in parts if p]
            if len(parts) >= 3:
                try:
                    elapsed = float(parts[0])
                    # parts[2] should be in the format "Logical Clock: X"
                    clock_str = parts[2].split(":")[1].strip()
                    clock_val = int(clock_str)
                    times.append(elapsed)
                    clocks.append(clock_val)
                except Exception:
                    continue
    return times, clocks

def visualize_run(run_dir):
    log_files = glob.glob(os.path.join(run_dir, "vm_*.log"))
    if not log_files:
        print(f"No log files found in {run_dir}")
        return

    plt.figure(figsize=(10, 6))
    for log_file in log_files:
        times, clocks = parse_log_file(log_file)
        vm_label = os.path.splitext(os.path.basename(log_file))[0]
        plt.plot(times, clocks, marker='o', label=vm_label)
    plt.xlabel("Elapsed Time (seconds)")
    plt.ylabel("Logical Clock Value")
    plt.title(f"Logical Clock Progression - {run_dir}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def visualize_all_runs():
    run_dirs = sorted(glob.glob("run_*"))
    if not run_dirs:
        print("No simulation runs found!")
        return

    for run_dir in run_dirs:
        visualize_run(run_dir)

if __name__ == "__main__":
    visualize_all_runs()
