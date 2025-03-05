import os
import time
from vm_simulation import start_virtual_machines

def run_simulation(run_id, num_vms, run_time, base_port, internal_event_prob, output_dir):
    """
    Runs the simulation for a given run_id and internal event probability.
    Log files will be moved into a directory specified by output_dir.
    """
    # Create a unique directory name including probability and run id.
    dir_name = f"{output_dir}/prob_{internal_event_prob}_run_{run_id}"
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    
    print(f"[Run {run_id} | p_internal={internal_event_prob}] Starting simulation for {run_time} seconds on base port {base_port}...")
    vms = start_virtual_machines(num_vms, base_port, internal_event_prob)
    
    # Run simulation for run_time seconds.
    time.sleep(run_time)
    
    # Stop all VMs.
    for vm in vms:
        vm.stop()
    
    # Give logs a moment to flush.
    time.sleep(2)
    
    # Move each log file into the run directory.
    for vm_id in range(num_vms):
        log_filename = f"vm_{vm_id}.log"
        if os.path.exists(log_filename):
            os.rename(log_filename, os.path.join(dir_name, log_filename))
    
    print(f"[Run {run_id} | p_internal={internal_event_prob}] Completed simulation.")

def experiment():
    # Define internal event probabilities to test.
    probabilities = [0.1, 0.3, 0.5, 0.7]
    num_runs = 5         # Number of runs per probability
    num_vms = 3          # Number of virtual machines
    run_time = 60        # Run time per simulation in seconds (e.g., one minute)
    base_port_start = 5100  # Base port for the first simulation. Increment for separate runs if needed.
    
    # Create a top-level output directory for all experiment logs.
    output_dir = "experiment_logs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Loop over each probability.
    for prob in probabilities:
        # For each probability, run several simulations.
        for run_id in range(1, num_runs + 1):
            # We can also vary the base_port to avoid port conflicts.
            base_port = base_port_start + (run_id * 100)
            run_simulation(run_id, num_vms, run_time, base_port, prob, output_dir)
    
if __name__ == "__main__":
    experiment()
