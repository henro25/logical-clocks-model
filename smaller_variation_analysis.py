import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

base_dir = os.path.join(os.getcwd(), "experiment_logs")

# Define the output folder on your Desktop for saving images.
desktop_dir = os.path.expanduser("~/Desktop")
output_images_dir = os.path.join(desktop_dir, "CustomVariationAnalysis")
if not os.path.exists(output_images_dir):
    os.makedirs(output_images_dir)

def save_and_close(fig, filename):
    filepath = os.path.join(output_images_dir, filename)
    fig.savefig(filepath)
    plt.close(fig)
    print(f"Saved plot to {filepath}")

def parse_log_file(filepath):
    """
    Parse a log file with expected format:
    <elapsed>\t<event_type>\tLogical Clock: <clock>\tQueue Length: <queue_length>\t<details>
    """
    data = []
    with open(filepath, 'r') as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) < 5:
                continue
            try:
                elapsed = float(parts[0])
                event_type = parts[1].strip()
                if "Logical Clock:" in parts[2]:
                    logical_clock = int(parts[2].split("Logical Clock:")[1].strip())
                else:
                    continue
                if "Queue Length:" in parts[3]:
                    queue_length = int(parts[3].split("Queue Length:")[1].strip())
                else:
                    continue
                details = parts[4].strip()
                data.append((elapsed, event_type, logical_clock, queue_length, details))
            except Exception:
                continue
    df = pd.DataFrame(data, columns=["elapsed", "event_type", "logical_clock", "queue_length", "details"])
    return df

def analyze_drift(vm_logs, num_points=200, termination_fraction=0.1):
    """
    For a given dictionary of vm_logs (one per VM), interpolate each VM's logical clock
    onto a common time grid and compute:
      - Overall average and maximum drift: mean and max of all pairwise absolute differences.
      - Terminating drift: average and maximum drift computed over the final termination_fraction of the timeline.
    Also saves individual drift plots for each VM pair.
    Returns a dictionary with keys: 'avg_drift', 'max_drift', 'term_avg_drift', and 'term_max_drift'.
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
    
    # Interpolate each VM's logical clock.
    interpolated = {}
    for vm_id, df in vm_logs.items():
        df_sorted = df.sort_values("elapsed")
        interp_values = np.interp(common_times, df_sorted["elapsed"].values, df_sorted["logical_clock"].values)
        interpolated[vm_id] = interp_values

    # Compute pairwise drift for each VM pair.
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
            save_and_close(fig, f"drift_VM{vm_ids[i]}_VM{vm_ids[j]}.png")
    if drift_values:
        all_drift = np.vstack(drift_values)
        overall_avg_drift = np.mean(all_drift)
        overall_max_drift = np.max(all_drift)
    else:
        overall_avg_drift, overall_max_drift = 0, 0

    # Calculate terminating drift (using final termination_fraction of time points).
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

def analyze_run(run_directory):
    """
    For a given run directory (e.g., "custom_var_run_1_range_1-3"), parse log files,
    compute clock jump metrics, queue metrics, and drift metrics (including terminating drift).
    Also saves individual plots (logical clock progression and queue lengths).
    Returns a dictionary with aggregated metrics.
    """
    vm_logs = {}
    for filename in os.listdir(run_directory):
        full_path = os.path.join(run_directory, filename)
        if os.path.isfile(full_path) and filename.endswith(".log"):
            # Assumes filename like "vm_<id>.log"
            vm_id = filename.split("_")[1]
            df = parse_log_file(full_path)
            if df.empty:
                print(f"Warning: No data parsed from {full_path}")
            else:
                vm_logs[vm_id] = df

    if not vm_logs:
        print(f"No valid log files found in {run_directory}")
        return None

    run_name = os.path.basename(run_directory)

    # Save logical clock progression plot.
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    for vm_id, df in vm_logs.items():
        ax1.plot(df["elapsed"], df["logical_clock"], label=f"VM {vm_id}")
    ax1.set_xlabel("Elapsed Time (s)")
    ax1.set_ylabel("Logical Clock")
    ax1.set_title(f"Logical Clock Progression in {run_name}")
    ax1.legend()
    save_and_close(fig1, f"{run_name}_logical_clock.png")

    # Save queue length plot.
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    for vm_id, df in vm_logs.items():
        ax2.plot(df["elapsed"], df["queue_length"], label=f"VM {vm_id}")
    ax2.set_xlabel("Elapsed Time (s)")
    ax2.set_ylabel("Queue Length")
    ax2.set_title(f"Queue Length in {run_name}")
    ax2.legend()
    save_and_close(fig2, f"{run_name}_queue_length.png")

    # Compute clock jump metrics.
    metrics = {"mean_jump": [], "max_jump": [], "std_jump": [], "avg_queue": []}
    for vm_id, df in vm_logs.items():
        df = df.sort_values("elapsed")
        df["clock_jump"] = df["logical_clock"].diff().fillna(0)
        mean_jump = df["clock_jump"].abs().mean()
        max_jump = df["clock_jump"].abs().max()
        std_jump = df["clock_jump"].std()
        avg_queue = df["queue_length"].mean()
        print(f"{run_name} - VM {vm_id} mean jump: {mean_jump:.2f}, max jump: {max_jump:.2f}, avg queue: {avg_queue:.2f}")
        metrics["mean_jump"].append(mean_jump)
        metrics["max_jump"].append(max_jump)
        metrics["std_jump"].append(std_jump)
        metrics["avg_queue"].append(avg_queue)
    jump_metrics = {
        "mean_jump": np.mean(metrics["mean_jump"]),
        "max_jump": np.mean(metrics["max_jump"]),
        "std_jump": np.mean(metrics["std_jump"]),
        "avg_queue": np.mean(metrics["avg_queue"]),
    }

    # Compute overall and terminating drift metrics.
    drift_metrics = analyze_drift(vm_logs)
    print(f"{run_name} - Overall avg drift: {drift_metrics['avg_drift']:.2f}, Overall max drift: {drift_metrics['max_drift']:.2f}")
    print(f"{run_name} - Terminating avg drift: {drift_metrics['term_avg_drift']:.2f}, Terminating max drift: {drift_metrics['term_max_drift']:.2f}")

    run_metrics = {**jump_metrics, **drift_metrics}
    return run_metrics

def aggregate_custom_variation_results(base_dir):
    """
    Scan through the base_dir for run directories with the pattern:
    custom_var_run_<run_id>_range_<min>-<max>
    Group results by the range string (e.g., "1-3") and aggregate metrics.
    Returns a dictionary mapping each range (string) to a list of run metrics.
    """
    pattern = re.compile(r"custom_var_run_\d+_range_([0-9]+-[0-9]+)")
    results_by_range = {}
    for entry in os.listdir(base_dir):
        full_path = os.path.join(base_dir, entry)
        if os.path.isdir(full_path):
            match = pattern.search(entry)
            if match:
                range_str = match.group(1)
                run_metrics = analyze_run(full_path)
                if run_metrics is not None:
                    if range_str not in results_by_range:
                        results_by_range[range_str] = []
                    results_by_range[range_str].append(run_metrics)
                else:
                    print(f"No valid data in directory: {full_path}")
    return results_by_range

def plot_aggregated_custom_results(results_by_range):
    """
    For each metric, compute the average across runs for each custom variation range,
    and save aggregated plots.
    """
    # Sort by range key (numerically by the minimum value).
    ranges = sorted(results_by_range.keys(), key=lambda s: int(s.split("-")[0]))
    agg_metrics = {
        "mean_jump": [], "max_jump": [], "avg_queue": [],
        "avg_drift": [], "max_drift": [], "term_avg_drift": [], "term_max_drift": []
    }
    
    for rng in ranges:
        runs = results_by_range[rng]
        agg_metrics["mean_jump"].append(np.mean([r["mean_jump"] for r in runs]))
        agg_metrics["max_jump"].append(np.mean([r["max_jump"] for r in runs]))
        agg_metrics["avg_queue"].append(np.mean([r["avg_queue"] for r in runs]))
        agg_metrics["avg_drift"].append(np.mean([r["avg_drift"] for r in runs]))
        agg_metrics["max_drift"].append(np.mean([r["max_drift"] for r in runs]))
        agg_metrics["term_avg_drift"].append(np.mean([r["term_avg_drift"] for r in runs]))
        agg_metrics["term_max_drift"].append(np.mean([r["term_max_drift"] for r in runs]))
    
    # Plot aggregated metrics.
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(ranges, agg_metrics["mean_jump"], marker="o", linestyle="-")
    ax1.set_xlabel("Clock Speed Range (min-max)")
    ax1.set_ylabel("Mean Clock Jump")
    ax1.set_title("Mean Clock Jump vs. Clock Speed Range")
    ax1.grid(True)
    save_and_close(fig1, "Aggregated_Mean_Clock_Jump_Custom.png")
    
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    ax2.plot(ranges, agg_metrics["max_jump"], marker="o", linestyle="-", color="red")
    ax2.set_xlabel("Clock Speed Range (min-max)")
    ax2.set_ylabel("Max Clock Jump")
    ax2.set_title("Max Clock Jump vs. Clock Speed Range")
    ax2.grid(True)
    save_and_close(fig2, "Aggregated_Max_Clock_Jump_Custom.png")
    
    fig3, ax3 = plt.subplots(figsize=(10, 5))
    ax3.plot(ranges, agg_metrics["avg_queue"], marker="o", linestyle="-", color="green")
    ax3.set_xlabel("Clock Speed Range (min-max)")
    ax3.set_ylabel("Average Queue Length")
    ax3.set_title("Average Queue Length vs. Clock Speed Range")
    ax3.grid(True)
    save_and_close(fig3, "Aggregated_Avg_Queue_Custom.png")
    
    fig4, ax4 = plt.subplots(figsize=(10, 5))
    ax4.plot(ranges, agg_metrics["avg_drift"], marker="o", linestyle="-", color="purple")
    ax4.set_xlabel("Clock Speed Range (min-max)")
    ax4.set_ylabel("Average Drift")
    ax4.set_title("Average Drift vs. Clock Speed Range")
    ax4.grid(True)
    save_and_close(fig4, "Aggregated_Avg_Drift_Custom.png")
    
    fig5, ax5 = plt.subplots(figsize=(10, 5))
    ax5.plot(ranges, agg_metrics["max_drift"], marker="o", linestyle="-", color="orange")
    ax5.set_xlabel("Clock Speed Range (min-max)")
    ax5.set_ylabel("Max Drift")
    ax5.set_title("Max Drift vs. Clock Speed Range")
    ax5.grid(True)
    save_and_close(fig5, "Aggregated_Max_Drift_Custom.png")
    
    fig6, ax6 = plt.subplots(figsize=(10, 5))
    ax6.plot(ranges, agg_metrics["term_avg_drift"], marker="o", linestyle="-", color="brown")
    ax6.set_xlabel("Clock Speed Range (min-max)")
    ax6.set_ylabel("Terminating Avg Drift")
    ax6.set_title("Terminating Average Drift vs. Clock Speed Range")
    ax6.grid(True)
    save_and_close(fig6, "Aggregated_Term_Avg_Drift_Custom.png")
    
    fig7, ax7 = plt.subplots(figsize=(10, 5))
    ax7.plot(ranges, agg_metrics["term_max_drift"], marker="o", linestyle="-", color="magenta")
    ax7.set_xlabel("Clock Speed Range (min-max)")
    ax7.set_ylabel("Terminating Max Drift")
    ax7.set_title("Terminating Max Drift vs. Clock Speed Range")
    ax7.grid(True)
    save_and_close(fig7, "Aggregated_Term_Max_Drift_Custom.png")

def main():
    results_by_range = aggregate_custom_variation_results(base_dir)
    print("Aggregated Results by Clock Speed Range:")
    for rng, runs in sorted(results_by_range.items()):
        print(f"Range {rng}: {runs}")
    plot_aggregated_custom_results(results_by_range)

if __name__ == "__main__":
    main()
