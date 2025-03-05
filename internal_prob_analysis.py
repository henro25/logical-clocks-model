import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Define the output folder on the Desktop.
desktop_dir = os.path.expanduser("~/Desktop")
output_images_dir = os.path.join(desktop_dir, "LogicalClockAnalysisImages")
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
        for line_num, line in enumerate(f, start=1):
            parts = line.strip().split("\t")
            if len(parts) < 5:
                print(f"Warning: Line {line_num} in {filepath} has fewer than 5 fields: {line.strip()}")
                continue
            try:
                elapsed = float(parts[0])
                event_type = parts[1].strip()
                if "Logical Clock:" in parts[2]:
                    logical_clock = int(parts[2].split("Logical Clock:")[1].strip())
                else:
                    print(f"Warning: Unexpected format for logical clock on line {line_num}: {parts[2]}")
                    continue
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

def analyze_drift(vm_logs, num_points=200, termination_fraction=0.1):
    """
    Interpolates the logical clock values for each VM onto a common time grid and computes:
      - Overall average and maximum drift: mean and max of all pairwise absolute differences.
      - Terminating drift: average and maximum drift computed over the last termination_fraction of the timeline.
    Also, saves individual drift plots for each VM pair.
    Returns a dictionary with keys 'avg_drift', 'max_drift', 'term_avg_drift', and 'term_max_drift'.
    """
    # Gather overall time bounds from all VMs.
    all_times = []
    for df in vm_logs.values():
        all_times.extend(df["elapsed"].values)
    if not all_times:
        return {"avg_drift": None, "max_drift": None, "term_avg_drift": None, "term_max_drift": None}
    common_start = min(all_times)
    common_end = max(all_times)
    common_times = np.linspace(common_start, common_end, num_points)
    
    # Interpolate each VM's logical clock onto the common time grid.
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
            # Save an individual drift plot.
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

    # Determine indices for the termination phase (last termination_fraction of timeline).
    term_start_index = int((1 - termination_fraction) * num_points)
    term_times = common_times[term_start_index:]
    
    # Compute terminating drift for each pair over the final portion.
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

def analyze_run(run_directory):
    """
    For a given run directory, parse all .log files and compute:
      - Clock jump metrics, queue metrics.
      - Overall drift and terminating drift metrics.
    Also, saves individual plots (logical clock progression and queue lengths) to the Desktop.
    Returns a dictionary with aggregated metrics.
    """
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
    save_and_close(fig1, f"{run_name}_logical_clock_progression.png")

    # Save queue length plot.
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    for vm_id, df in vm_logs.items():
        ax2.plot(df["elapsed"], df["queue_length"], label=f"VM {vm_id}")
    ax2.set_xlabel("Elapsed Time (s)")
    ax2.set_ylabel("Queue Length")
    ax2.set_title(f"Queue Length Over Time in {run_name}")
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

# (Aggregation and plotting functions remain unchanged; they will now include the new terminating drift keys.)
def aggregate_experiment_results(base_dir="experiment_logs"):
    pattern = re.compile(r"prob_([0-9.]+)_run_\d+")
    results_by_prob = {}
    for entry in os.listdir(base_dir):
        full_path = os.path.join(base_dir, entry)
        if os.path.isdir(full_path):
            match = pattern.search(entry)
            if match:
                prob = float(match.group(1))
                run_metrics = analyze_run(full_path)
                if run_metrics is not None:
                    if prob not in results_by_prob:
                        results_by_prob[prob] = []
                    results_by_prob[prob].append(run_metrics)
                else:
                    print(f"No valid data in directory: {full_path}")
    return results_by_prob

def plot_aggregated_results(results_by_prob):
    probs = sorted(results_by_prob.keys())
    agg_metrics = {
        "mean_jump": [],
        "max_jump": [],
        "std_jump": [],
        "avg_queue": [],
        "avg_drift": [],
        "max_drift": [],
        "term_avg_drift": [],
        "term_max_drift": []
    }
    for prob in probs:
        runs = results_by_prob[prob]
        agg_metrics["mean_jump"].append(np.mean([r["mean_jump"] for r in runs]))
        agg_metrics["max_jump"].append(np.mean([r["max_jump"] for r in runs]))
        agg_metrics["std_jump"].append(np.mean([r["std_jump"] for r in runs]))
        agg_metrics["avg_queue"].append(np.mean([r["avg_queue"] for r in runs]))
        agg_metrics["avg_drift"].append(np.mean([r["avg_drift"] for r in runs]))
        agg_metrics["max_drift"].append(np.mean([r["max_drift"] for r in runs]))
        agg_metrics["term_avg_drift"].append(np.mean([r["term_avg_drift"] for r in runs]))
        agg_metrics["term_max_drift"].append(np.mean([r["term_max_drift"] for r in runs]))
    
    # Plot aggregated metrics; here we add two additional plots for terminating drift.
    fig3, ax3 = plt.subplots(figsize=(10, 5))
    ax3.plot(probs, agg_metrics["mean_jump"], marker="o", linestyle="-")
    ax3.set_xlabel("Internal Event Probability")
    ax3.set_ylabel("Mean Clock Jump")
    ax3.set_title("Mean Clock Jump vs. Internal Event Probability")
    ax3.grid(True)
    save_and_close(fig3, "Aggregated_Mean_Clock_Jump.png")
    
    fig4, ax4 = plt.subplots(figsize=(10, 5))
    ax4.plot(probs, agg_metrics["max_jump"], marker="o", linestyle="-", color="red")
    ax4.set_xlabel("Internal Event Probability")
    ax4.set_ylabel("Max Clock Jump")
    ax4.set_title("Max Clock Jump vs. Internal Event Probability")
    ax4.grid(True)
    save_and_close(fig4, "Aggregated_Max_Clock_Jump.png")
    
    fig5, ax5 = plt.subplots(figsize=(10, 5))
    ax5.plot(probs, agg_metrics["avg_queue"], marker="o", linestyle="-", color="green")
    ax5.set_xlabel("Internal Event Probability")
    ax5.set_ylabel("Average Queue Length")
    ax5.set_title("Average Queue Length vs. Internal Event Probability")
    ax5.grid(True)
    save_and_close(fig5, "Aggregated_Avg_Queue_Length.png")
    
    fig6, ax6 = plt.subplots(figsize=(10, 5))
    ax6.plot(probs, agg_metrics["avg_drift"], marker="o", linestyle="-", color="purple")
    ax6.set_xlabel("Internal Event Probability")
    ax6.set_ylabel("Average Drift")
    ax6.set_title("Average Drift vs. Internal Event Probability")
    ax6.grid(True)
    save_and_close(fig6, "Aggregated_Avg_Drift.png")
    
    fig7, ax7 = plt.subplots(figsize=(10, 5))
    ax7.plot(probs, agg_metrics["max_drift"], marker="o", linestyle="-", color="orange")
    ax7.set_xlabel("Internal Event Probability")
    ax7.set_ylabel("Max Drift")
    ax7.set_title("Max Drift vs. Internal Event Probability")
    ax7.grid(True)
    save_and_close(fig7, "Aggregated_Max_Drift.png")
    
    fig8, ax8 = plt.subplots(figsize=(10, 5))
    ax8.plot(probs, agg_metrics["term_avg_drift"], marker="o", linestyle="-", color="brown")
    ax8.set_xlabel("Internal Event Probability")
    ax8.set_ylabel("Terminating Avg Drift")
    ax8.set_title("Terminating Average Drift vs. Internal Event Probability")
    ax8.grid(True)
    save_and_close(fig8, "Aggregated_Term_Avg_Drift.png")
    
    fig9, ax9 = plt.subplots(figsize=(10, 5))
    ax9.plot(probs, agg_metrics["term_max_drift"], marker="o", linestyle="-", color="magenta")
    ax9.set_xlabel("Internal Event Probability")
    ax9.set_ylabel("Terminating Max Drift")
    ax9.set_title("Terminating Max Drift vs. Internal Event Probability")
    ax9.grid(True)
    save_and_close(fig9, "Aggregated_Term_Max_Drift.png")

def main():
    base_dir = "experiment_logs" 
    results_by_prob = aggregate_experiment_results(base_dir)
    print("Aggregated Results by Internal Event Probability:")
    for prob, runs in sorted(results_by_prob.items()):
        print(f"Probability {prob}: {runs}")
    plot_aggregated_results(results_by_prob)

if __name__ == "__main__":
    main()
