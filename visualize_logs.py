import os
import glob
import pandas as pd
import matplotlib.pyplot as plt

def parse_log_file(filename):
    # Each log line is tab-delimited: elapsed time, event, "Logical Clock: X", details
    times = []
    clocks = []
    with open(filename, "r") as f:
        for line in f:
            parts = line.strip().split("\t")
            parts = [p for p in parts if p] # Remove empty strings
            if len(parts) >= 3:
                try:
                    elapsed = float(parts[0])
                    
                    if parts[1] == "Init":
                        clock_str = parts[3].split(":")[-1].split()[0]
                    else:
                        # parts[2] is in the format "Logical Clock: X"
                        clock_str = parts[2].split(":")[1].strip()
                    
                    clock_val = int(clock_str)
                    times.append(elapsed)
                    clocks.append(clock_val)
                except Exception as e:
                    continue
    return times, clocks

def visualize_logs():
    # Get all vm_*.log files in the current directory.
    log_files = glob.glob("vm_*.log")
    if not log_files:
        print("No log files found!")
        return

    plt.figure(figsize=(10, 6))
    for log_file in log_files:
        times, clocks = parse_log_file(log_file)
        vm_label = os.path.splitext(os.path.basename(log_file))[0]
        plt.plot(times[1:], clocks[1:], marker='o', label=vm_label + " running " + str(clocks[0]) + " ticks/sec")

    plt.xlabel("Elapsed Time (seconds)")
    plt.ylabel("Logical Clock Value")
    plt.title("Logical Clock Progression Over Time")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    visualize_logs()
