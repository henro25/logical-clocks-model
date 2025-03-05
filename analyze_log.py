import os
import pandas as pd
import matplotlib.pyplot as plt

def parse_log_file(filepath):
    # Each log entry is expected to have five tab-separated fields:
    # elapsed, event_type, "Logical Clock: <clock>", "Queue Length: <queue_length>", and details.
    data = []
    with open(filepath, 'r') as f:
        for line_num, line in enumerate(f, start=1):
            # Remove trailing newline and split on tab
            parts = line.strip().split("\t")
            if len(parts) < 5:
                print(f"Warning: Line {line_num} in {filepath} has fewer than 5 fields: {line.strip()}")
                continue
            try:
                elapsed = float(parts[0])
                event_type = parts[1].strip()
                
                # Expecting "Logical Clock: <value>"
                if "Logical Clock:" in parts[2]:
                    logical_clock = int(parts[2].split("Logical Clock:")[1].strip())
                else:
                    print(f"Warning: Unexpected format for logical clock on line {line_num}: {parts[2]}")
                    continue
                
                # Expecting "Queue Length: <value>"
                if "Queue Length:" in parts[3]:
                    queue_length = int(parts[3].split("Queue Length:")[1].strip())
                else:
                    print(f"Warning: Unexpected format for queue length on line {line_num}: {parts[3]}")
                    continue

                details = parts[4].strip()
                data.append((elapsed, event_type, logical_clock, queue_length, details))
            except Exception as e:
                print(f"Error parsing line {line_num} in {filepath}: {line.strip()}\nError: {e}")
                continue

    df = pd.DataFrame(data, columns=["elapsed", "event_type", "logical_clock", "queue_length", "details"])
    print(f"Parsed {len(df)} rows from {filepath}")
    if not df.empty:
        print(df.head())
    return df

def analyze_run(run_directory):
    vm_logs = {}
    for filename in os.listdir(run_directory):
        full_path = os.path.join(run_directory, filename)
        if os.path.isfile(full_path) and filename.endswith(".log"):
            vm_id = filename.split("_")[1]
            df = parse_log_file(full_path)
            if df.empty:
                print(f"Warning: No data parsed from {full_path}")
            else:
                vm_logs[vm_id] = df
    
    if not vm_logs:
        print(f"No valid log files found in {run_directory}")
        return
    
    # Plot logical clock progression for each VM.
    plt.figure(figsize=(12, 6))
    for vm_id, df in vm_logs.items():
        plt.plot(df["elapsed"], df["logical_clock"], label=f"VM {vm_id} Logical Clock")
    plt.xlabel("Elapsed Time (s)")
    plt.ylabel("Logical Clock")
    plt.title(f"Logical Clock Progression in {run_directory}")
    plt.legend()
    plt.show()

    # Plot queue lengths for each VM.
    plt.figure(figsize=(12, 6))
    for vm_id, df in vm_logs.items():
        plt.plot(df["elapsed"], df["queue_length"], label=f"VM {vm_id} Queue Length")
    plt.xlabel("Elapsed Time (s)")
    plt.ylabel("Queue Length")
    plt.title(f"Queue Length Over Time in {run_directory}")
    plt.legend()
    plt.show()

    # Analyze clock jumps and queue lengths: compute differences between consecutive logical clock values.
    for vm_id, df in vm_logs.items():
        df["clock_jump"] = df["logical_clock"].diff().fillna(0)
        avg_jump = df["clock_jump"].abs().mean()
        avg_queue = df["queue_length"].mean()
        print(f"VM {vm_id} average clock jump: {avg_jump:.2f}")
        print(f"VM {vm_id} average queue length: {avg_queue:.2f}")

    return vm_logs

if __name__ == "__main__":
    # Only process directories that start with "run_"
    run_dirs = [d for d in os.listdir() if d.startswith("run_") and os.path.isdir(d)]
    for run in run_dirs:
        print(f"\nAnalyzing {run}")
        analyze_run(run)
