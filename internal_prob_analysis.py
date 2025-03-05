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
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) < 5:
                continue
            try:
                elapsed = float(parts[0])
                event_type = parts[1].strip()
                # Parse the logical clock value.
                if "Logical Clock:" in parts[2]:
                    logical_clock = int(parts[2].split("Logical Clock:")[1].strip())
                else:
                    continue
                # Parse the queue length.
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

def analyze_drift(vm_logs, num_points=200):
    """
    Interpolates the logical clock values for each VM onto a common time grid and computes:
      - Average drift: mean of all pairwise absolute differences at each time point.
      - Maximum drift: maximum absolute difference observed at any time point.
    Returns a dictionary with 'avg_drift' and 'max_drift' for the run.
    """
    # Gather overall time bounds from all VMs.
    all_times = []
    for df in vm_logs.values():
        all_times.extend(df["elapsed"].values)
    if not all_times:
        return {"avg_drift": None, "max_drift": None}
    common_start = min(all_times)
    common_end = max(all_times)
    common_times = np.linspace(common_start, common_end, num_points)
    
    # Interpolate each VM's logical clock onto the common time grid.
    interpolated = {}
    for vm_id, df in vm_logs.items():
        df_sorted = df.sort_values("elapsed")
        interp_values = np.interp(common_times, df_sorted["elapsed"].values, df_sorted["logical_clock"].values)
        interpolated[vm_id] = interp_values

    # Compute pairwise drift: for each time point, compute absolute differences between each pair.
    vm_ids = list(interpolated.keys())
    drift_values = []
    for i in range(len(vm_ids)):
        for j in range(i+1, len(vm_ids)):
            diff = np.abs(interpolated[vm_ids[i]] - interpolated[vm_ids[j]])
            drift_values.append(diff)
    if drift_values:
        # Stack all drift arrays along axis 0.
        all_drift = np.vstack(drift_values)
        avg_drift = np.mean(all_drift)
        max_drift = np.max(all_drift)
    else:
        avg_drift, max_drift = 0, 0
    
    # Plot drift over time for each VM pair.
    pair_index = 1
    for i in range(len(vm_ids)):
        for j in range(i+1, len(vm_ids)):
            diff = np.abs(interpolated[vm_ids[i]] - interpolated[vm_ids[j]])
            fig, ax = plt.subplots(figsize=(10,4))
            ax.plot(common_times, diff, marker="o", linestyle="-")
            ax.set_xlabel("Elapsed Time (s)")
            ax.set_ylabel("Drift (Absolute Difference)")
            ax.set_title(f"Drift between VM {vm_ids[i]} and VM {vm_ids[j]}")
            ax.grid(True)
            save_and_close(fig, f"drift_VM{vm_ids[i]}_VM{vm_ids[j]}.png")
            pair_index += 1

    return {"avg_drift": avg_drift, "max_drift": max_drift}

def analyze_run(run_directory):
    """
    For a given run directory, parse all .log files and compute:
      - Mean clock jump, maximum clock jump, standard deviation of jumps.
      - Average queue length.
      - Drift metrics (average and maximum drift between VMs).
    Also, save individual graphs for each VM (logical clock progression and queue length over time)
    to the Desktop folder.
    Returns a dictionary with aggregated metrics over VMs in this run.
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

    # Use only the base name of run_directory for filenames.
    run_name = os.path.basename(run_directory)

    # Save logical clock progression plot for this run.
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    for vm_id, df in vm_logs.items():
        ax1.plot(df["elapsed"], df["logical_clock"], label=f"VM {vm_id} Logical Clock")
    ax1.set_xlabel("Elapsed Time (s)")
    ax1.set_ylabel("Logical Clock")
    ax1.set_title(f"Logical Clock Progression in {run_name}")
    ax1.legend()
    save_and_close(fig1, f"{run_name}_logical_clock_progression.png")

    # Save queue length plot for this run.
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    for vm_id, df in vm_logs.items():
        ax2.plot(df["elapsed"], df["queue_length"], label=f"VM {vm_id} Queue Length")
    ax2.set_xlabel("Elapsed Time (s)")
    ax2.set_ylabel("Queue Length")
    ax2.set_title(f"Queue Length Over Time in {run_name}")
    ax2.legend()
    save_and_close(fig2, f"{run_name}_queue_length.png")

    # Compute clock jumps and queue lengths metrics.
    metrics = {"mean_jump": [], "max_jump": [], "std_jump": [], "avg_queue": []}
    for vm_id, df in vm_logs.items():
        df = df.sort_values("elapsed")
        df["clock_jump"] = df["logical_clock"].diff().fillna(0)
        mean_jump = df["clock_jump"].abs().mean()
        max_jump = df["clock_jump"].abs().max()
        std_jump = df["clock_jump"].std()
        avg_queue = df["queue_length"].mean()
        print(f"Run {run_name} - VM {vm_id} average clock jump: {mean_jump:.2f}")
        print(f"Run {run_name} - VM {vm_id} average queue length: {avg_queue:.2f}")
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

    # Analyze drift for the run.
    drift_metrics = analyze_drift(vm_logs)
    print(f"Run {run_name} - Average drift: {drift_metrics['avg_drift']:.2f}, Max drift: {drift_metrics['max_drift']:.2f}")
    
    # Combine metrics
    run_metrics = {**jump_metrics, **drift_metrics}
    return run_metrics

def aggregate_experiment_results(base_dir="experiment_logs"):
    """
    Walk through the experiment directories (names like "prob_{p}_run_{run_id}")
    and aggregate the metrics by internal event probability.
    Returns a dictionary mapping probability (as float) to a list of run metrics.
    """
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
    """
    For each metric, compute the average (and optionally std) across runs for each probability,
    and then save the plots to the Desktop.
    """
    probs = sorted(results_by_prob.keys())
    agg_metrics = {"mean_jump": [], "max_jump": [], "std_jump": [], "avg_queue": [], "avg_drift": [], "max_drift": []}
    
    for prob in probs:
        runs = results_by_prob[prob]
        agg_metrics["mean_jump"].append(np.mean([r["mean_jump"] for r in runs]))
        agg_metrics["max_jump"].append(np.mean([r["max_jump"] for r in runs]))
        agg_metrics["std_jump"].append(np.mean([r["std_jump"] for r in runs]))
        agg_metrics["avg_queue"].append(np.mean([r["avg_queue"] for r in runs]))
        agg_metrics["avg_drift"].append(np.mean([r["avg_drift"] for r in runs]))
        agg_metrics["max_drift"].append(np.mean([r["max_drift"] for r in runs]))
    
    # Plot Mean Clock Jump vs Internal Event Probability.
    fig3, ax3 = plt.subplots(figsize=(10, 5))
    ax3.plot(probs, agg_metrics["mean_jump"], marker="o", linestyle="-")
    ax3.set_xlabel("Internal Event Probability")
    ax3.set_ylabel("Mean Clock Jump")
    ax3.set_title("Mean Clock Jump vs. Internal Event Probability")
    ax3.grid(True)
    save_and_close(fig3, "Aggregated_Mean_Clock_Jump.png")
    
    # Plot Max Clock Jump vs Internal Event Probability.
    fig4, ax4 = plt.subplots(figsize=(10, 5))
    ax4.plot(probs, agg_metrics["max_jump"], marker="o", linestyle="-", color="red")
    ax4.set_xlabel("Internal Event Probability")
    ax4.set_ylabel("Max Clock Jump")
    ax4.set_title("Max Clock Jump vs. Internal Event Probability")
    ax4.grid(True)
    save_and_close(fig4, "Aggregated_Max_Clock_Jump.png")
    
    # Plot Average Queue Length vs Internal Event Probability.
    fig5, ax5 = plt.subplots(figsize=(10, 5))
    ax5.plot(probs, agg_metrics["avg_queue"], marker="o", linestyle="-", color="green")
    ax5.set_xlabel("Internal Event Probability")
    ax5.set_ylabel("Average Queue Length")
    ax5.set_title("Average Queue Length vs. Internal Event Probability")
    ax5.grid(True)
    save_and_close(fig5, "Aggregated_Avg_Queue_Length.png")
    
    # Plot Average Drift vs Internal Event Probability.
    fig6, ax6 = plt.subplots(figsize=(10, 5))
    ax6.plot(probs, agg_metrics["avg_drift"], marker="o", linestyle="-", color="purple")
    ax6.set_xlabel("Internal Event Probability")
    ax6.set_ylabel("Average Drift")
    ax6.set_title("Average Drift vs. Internal Event Probability")
    ax6.grid(True)
    save_and_close(fig6, "Aggregated_Avg_Drift.png")
    
    # Plot Max Drift vs Internal Event Probability.
    fig7, ax7 = plt.subplots(figsize=(10, 5))
    ax7.plot(probs, agg_metrics["max_drift"], marker="o", linestyle="-", color="orange")
    ax7.set_xlabel("Internal Event Probability")
    ax7.set_ylabel("Max Drift")
    ax7.set_title("Max Drift vs. Internal Event Probability")
    ax7.grid(True)
    save_and_close(fig7, "Aggregated_Max_Drift.png")

def main():
    base_dir = "experiment_logs"  # Ensure this directory contains your experiment run directories.
    results_by_prob = aggregate_experiment_results(base_dir)
    
    print("Aggregated Results by Internal Event Probability:")
    for prob, runs in sorted(results_by_prob.items()):
        print(f"Probability {prob}: {runs}")
    
    plot_aggregated_results(results_by_prob)

if __name__ == "__main__":
    main()
