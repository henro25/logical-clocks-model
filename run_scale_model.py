import os
import time
import threading
from vm_simulation import start_virtual_machines

def run_simulation(run_id, num_vms=3, run_time=60):
    # Choose a unique base port for this simulation run.
    base_port = 5100 + (run_id * 100)
    
    # Create a subdirectory for this run's log files.
    dir_name = f"run_{run_id}"
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    
    print(f"[Run {run_id}] Starting simulation for {run_time} seconds on base port {base_port}...")
    vms = start_virtual_machines(num_vms, base_port)
    
    time.sleep(run_time)
    
    # Stop all VMs.
    for vm in vms:
        vm.stop()
    
    # Give a moment for all logs to be flushed.
    time.sleep(2)
    
    # Move each unique log file into the run directory.
    for vm_id in range(num_vms):
        log_filename = f"vm_{vm_id}_{base_port}.log"
        if os.path.exists(log_filename):
            os.rename(log_filename, os.path.join(dir_name, log_filename))
    
    print(f"[Run {run_id}] Completed simulation.")

def main():
    num_runs = 5
    threads = []
    for run_id in range(1, num_runs + 1):
        t = threading.Thread(target=run_simulation, args=(run_id, 3, 5))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

if __name__ == "__main__":
    main()
