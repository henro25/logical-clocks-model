import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

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

# def analyze_run(run_directory):
#     vm_logs = {}
#     for filename in os.listdir(run_directory):
#         full_path = os.path.join(run_directory, filename)
#         if os.path.isfile(full_path) and filename.endswith(".log"):
#             vm_id = filename.split("_")[1]
#             df = parse_log_file(full_path)
#             if df.empty:
#                 print(f"Warning: No data parsed from {full_path}")
#             else:
#                 vm_logs[vm_id] = df
    
#     if not vm_logs:
#         print(f"No valid log files found in {run_directory}")
#         return
    
#     # Plot logical clock progression for each VM.
#     plt.figure(figsize=(12, 6))
#     for vm_id, df in vm_logs.items():
#         plt.plot(df["elapsed"], df["logical_clock"], label=f"VM {vm_id} Logical Clock")
#     plt.xlabel("Elapsed Time (s)")
#     plt.ylabel("Logical Clock")
#     plt.title(f"Logical Clock Progression in {run_directory}")
#     plt.legend()
#     plt.show()

#     # Plot queue lengths for each VM.
#     plt.figure(figsize=(12, 6))
#     for vm_id, df in vm_logs.items():
#         plt.plot(df["elapsed"], df["queue_length"], label=f"VM {vm_id} Queue Length")
#     plt.xlabel("Elapsed Time (s)")
#     plt.ylabel("Queue Length")
#     plt.title(f"Queue Length Over Time in {run_directory}")
#     plt.legend()
#     plt.show()

#     # Analyze clock jumps and queue lengths: compute differences between consecutive logical clock values.
#     for vm_id, df in vm_logs.items():
#         df["clock_jump"] = df["logical_clock"].diff().fillna(0)
#         avg_jump = df["clock_jump"].abs().mean()
#         avg_queue = df["queue_length"].mean()
#         print(f"VM {vm_id} average clock jump: {avg_jump:.2f}")
#         print(f"VM {vm_id} average queue length: {avg_queue:.2f}")

#     return vm_logs

# if __name__ == "__main__":
#     # Only process directories that start with "run_"
#     run_dirs = [d for d in os.listdir() if d.startswith("run_") and os.path.isdir(d)]
#     for run in run_dirs:
#         print(f"\nAnalyzing {run}")
#         analyze_run(run)
def load_run_data(run_directory):
    vm_logs = {}
    for filename in os.listdir(run_directory):
        full_path = os.path.join(run_directory, filename)
        if os.path.isfile(full_path) and filename.endswith(".log"):
            vm_id = filename.split("_")[1]  # Assumes filename like "vm_<id>*.log"
            df = parse_log_file(full_path)
            if not df.empty:
                vm_logs[vm_id] = df
            else:
                print(f"Warning: No data parsed from {full_path}")
    return vm_logs
def analyze_clock_jumps(vm_logs):
    print("\n=== Clock Jump Analysis ===")
    jump_stats = {}
    for vm_id, df in vm_logs.items():
        df = df.sort_values("elapsed")
        # Compute jump as difference between consecutive logical clock values.
        df["clock_jump"] = df["logical_clock"].diff().fillna(0)
        mean_jump = df["clock_jump"].abs().mean()
        max_jump = df["clock_jump"].abs().max()
        std_jump = df["clock_jump"].std()
        jump_stats[vm_id] = {
            "mean_jump": mean_jump,
            "max_jump": max_jump,
            "std_jump": std_jump
        }
        print(f"VM {vm_id}: mean jump = {mean_jump:.2f}, max jump = {max_jump}, std = {std_jump:.2f}")
        # Plot clock jumps over time.
        plt.figure(figsize=(10, 4))
        plt.plot(df["elapsed"], df["clock_jump"], marker="o", linestyle="-")
        plt.xlabel("Elapsed Time (s)")
        plt.ylabel("Clock Jump")
        plt.title(f"VM {vm_id} Clock Jump over Time")
        plt.grid(True)
        plt.show()
    return jump_stats

def analyze_clock_drift(vm_logs):
    # To get a god's eye view, we can merge the data on elapsed time.
    # We do this by resampling the data to 1-second bins (or using interpolation).
    print("\n=== Clock Drift Analysis ===")
    merged = None
    for vm_id, df in vm_logs.items():
        # Set elapsed time as index and then reindex based on a common timeline.
        df_sorted = df.sort_values("elapsed").set_index("elapsed")
        # Use interpolation to fill in missing times.
        common_index = np.arange(df_sorted.index.min(), df_sorted.index.max(), 0.5)
        df_interp = df_sorted.reindex(common_index).interpolate(method="linear")
        df_interp = df_interp.reset_index().rename(columns={"index": "elapsed"})
        df_interp = df_interp[["elapsed", "logical_clock"]].rename(columns={"logical_clock": f"logical_clock_{vm_id}"})
        if merged is None:
            merged = df_interp
        else:
            merged = pd.merge_asof(merged.sort_values("elapsed"), 
                                   df_interp.sort_values("elapsed"), 
                                   on="elapsed", direction="nearest", tolerance=0.5)
    # Drop rows with NaN values.
    merged.dropna(inplace=True)
    print("Merged Data (first 5 rows):")
    print(merged.head())
    # Compute pairwise differences (drift) between VMs.
    vm_ids = list(vm_logs.keys())
    for i in range(len(vm_ids)):
        for j in range(i+1, len(vm_ids)):
            col_i = f"logical_clock_{vm_ids[i]}"
            col_j = f"logical_clock_{vm_ids[j]}"
            merged[f"drift_{vm_ids[i]}_{vm_ids[j]}"] = (merged[col_i] - merged[col_j]).abs()
            avg_drift = merged[f"drift_{vm_ids[i]}_{vm_ids[j]}"].mean()
            print(f"Average drift between VM {vm_ids[i]} and VM {vm_ids[j]}: {avg_drift:.2f}")
            plt.figure(figsize=(10, 4))
            plt.plot(merged["elapsed"], merged[f"drift_{vm_ids[i]}_{vm_ids[j]}"], marker="o", linestyle="-")
            plt.xlabel("Elapsed Time (s)")
            plt.ylabel("Drift (Absolute Difference)")
            plt.title(f"Drift between VM {vm_ids[i]} and VM {vm_ids[j]}")
            plt.grid(True)
            plt.show()
    return merged

def analyze_clock_drift_interp(vm_logs, num_points=200):
    """
    Interpolates the logical clock values for each VM onto a common time grid and computes
    the average drift between each pair of VMs.
    """
    import numpy as np
    import matplotlib.pyplot as plt

    # Gather all elapsed times to determine common bounds.
    all_times = []
    for df in vm_logs.values():
        all_times.extend(df["elapsed"].values)
    common_start = min(all_times)
    common_end = max(all_times)
    
    # Create a common time grid.
    common_times = np.linspace(common_start, common_end, num_points)
    
    # Interpolate each VM's logical clock values on the common time grid.
    interpolated = {}
    for vm_id, df in vm_logs.items():
        interp_values = np.interp(common_times, df["elapsed"].values, df["logical_clock"].values)
        interpolated[vm_id] = interp_values
        # Plot the interpolated logical clock progression.
        plt.figure(figsize=(10, 4))
        plt.plot(common_times, interp_values, marker="o", linestyle="-", label=f"VM {vm_id}")
        plt.xlabel("Elapsed Time (s)")
        plt.ylabel("Logical Clock")
        plt.title(f"Interpolated Logical Clock for VM {vm_id}")
        plt.legend()
        plt.grid(True)
        plt.show()
    
    # Compute pairwise drift between VMs.
    vm_ids = list(interpolated.keys())
    for i in range(len(vm_ids)):
        for j in range(i+1, len(vm_ids)):
            vm_i = vm_ids[i]
            vm_j = vm_ids[j]
            drift = np.abs(interpolated[vm_i] - interpolated[vm_j])
            avg_drift = np.mean(drift)
            print(f"Average drift between VM {vm_i} and VM {vm_j}: {avg_drift:.2f}")
            plt.figure(figsize=(10, 4))
            plt.plot(common_times, drift, marker="o", linestyle="-")
            plt.xlabel("Elapsed Time (s)")
            plt.ylabel("Drift (Absolute Difference)")
            plt.title(f"Drift between VM {vm_i} and VM {vm_j}")
            plt.grid(True)
            plt.show()
def analyze_drift(vm_logs, num_points=200, termination_fraction=0.1):
    """
    Interpolates the logical clock values for each VM onto a common time grid and computes:
      - Overall average and maximum drift: mean and max of all pairwise absolute differences.
      - Terminating drift: average and maximum drift computed over the final termination_fraction of the timeline.
    Also, saves individual drift plots for each VM pair.
    Returns a dictionary with keys:
      'avg_drift', 'max_drift', 'term_avg_drift', 'term_max_drift'.
    """
    # Gather overall time bounds.
    all_times = []
    for df in vm_logs.values():
        all_times.extend(df["elapsed"].values)
    if not all_times:
        return {"avg_drift": None, "max_drift": None, "term_avg_drift": None, "term_max_drift": None}
    common_start = min(all_times)
    common_end = max(all_times)
    common_times = np.linspace(common_start, common_end, num_points)
    
    # Interpolate logical clocks.
    interpolated = {}
    for vm_id, df in vm_logs.items():
        df_sorted = df.sort_values("elapsed")
        interp_values = np.interp(common_times, df_sorted["elapsed"].values, df_sorted["logical_clock"].values)
        interpolated[vm_id] = interp_values

    # Compute pairwise drift for each pair.
    vm_ids = list(interpolated.keys())
    drift_values = []
    for i in range(len(vm_ids)):
        for j in range(i+1, len(vm_ids)):
            diff = np.abs(interpolated[vm_ids[i]] - interpolated[vm_ids[j]])
            drift_values.append(diff)
            # Save individual drift plot.
            fig, ax = plt.subplots(figsize=(10,4))
            ax.plot(common_times, diff, marker="o", linestyle="-")
            ax.set_xlabel("Elapsed Time (s)")
            ax.set_ylabel("Drift (Absolute Difference)")
            ax.set_title(f"Drift between VM {vm_ids[i]} and VM {vm_ids[j]}")
            ax.grid(True)
            plt.show()
    if drift_values:
        all_drift = np.vstack(drift_values)
        overall_avg_drift = np.mean(all_drift)
        overall_max_drift = np.max(all_drift)
    else:
        overall_avg_drift, overall_max_drift = 0, 0

    # Determine termination phase indices.
    term_start_index = int((1 - termination_fraction) * num_points)
    term_drift_values = []
    for diff in drift_values:
        term_diff = diff[term_start_index:]
        term_drift_values.append(term_diff)
    if term_drift_values:
        all_term_drift = np.vstack(term_drift_values)
        term_avg_drift = np.mean(all_term_drift)
        term_max_drift = np.max(all_term_drift)
    else:
        term_avg_drift, term_max_drift = 0, 0

    return {"avg_drift": overall_avg_drift, 
            "max_drift": overall_max_drift, 
            "term_avg_drift": term_avg_drift, 
            "term_max_drift": term_max_drift}


def analyze_queue_vs_jumps(vm_logs):
    print("\n=== Queue Length vs Clock Jump Analysis ===")
    for vm_id, df in vm_logs.items():
        df = df.sort_values("elapsed")
        # Ensure we have computed clock_jump
        if "clock_jump" not in df.columns:
            df["clock_jump"] = df["logical_clock"].diff().fillna(0)
        # Scatter plot of queue length vs. absolute clock jump.
        plt.figure(figsize=(8, 5))
        plt.scatter(df["queue_length"], df["clock_jump"].abs(), alpha=0.6)
        plt.xlabel("Queue Length")
        plt.ylabel("Absolute Clock Jump")
        plt.title(f"VM {vm_id}: Queue Length vs Clock Jump")
        plt.grid(True)
        plt.show()
        # Compute correlation coefficient.
        if df["queue_length"].std() > 0 and df["clock_jump"].abs().std() > 0:
            corr = np.corrcoef(df["queue_length"], df["clock_jump"].abs())[0, 1]
            print(f"VM {vm_id} correlation between queue length and clock jump: {corr:.2f}")
        else:
            print(f"VM {vm_id} has insufficient variation to compute correlation.")

def main():
    # Specify the run directory you want to analyze.
    run_directory = input("Enter the run directory to analyze (e.g., run_1): ").strip()
    base_directory = os.path.join(os.getcwd(), "experiment_logs/", run_directory)
    if not os.path.isdir(base_directory):
        print(f"Directory {base_directory} does not exist.")
        return
    vm_logs = load_run_data(base_directory)
    if not vm_logs:
        print("No log data found.")
        return

    # Analyze clock jumps.
    analyze_clock_jumps(vm_logs)
    # Analyze clock drift across VMs.
    analyze_clock_drift_interp(vm_logs)
    drift_results = analyze_drift(vm_logs)
    print("Overall Drift:")
    print(f"Avg drift: {drift_results['avg_drift']:.2f}, Max drift: {drift_results['max_drift']:.2f}")
    print("Terminating Drift (last 10%):")
    print(f"Avg terminating drift: {drift_results['term_avg_drift']:.2f}, Max terminating drift: {drift_results['term_max_drift']:.2f}")
    # Analyze impact of queue length on clock jumps.
    analyze_queue_vs_jumps(vm_logs)

if __name__ == "__main__":
    main()