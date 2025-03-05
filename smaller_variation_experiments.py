import os
import time
import threading
import random
from vm_simulation import VirtualMachine

def start_virtual_machines_custom_variation(num_vms, base_port, min_speed, max_speed):
    """
    Start VMs with clock speeds randomly selected from a custom small range.
    For example, using min_speed=1 and max_speed=3 will assign speeds in {1,2,3}.
    """
    vms = []
    # Ensure we have enough distinct speeds in the range for the number of VMs.
    available_speeds = random.sample(range(min_speed, max_speed + 1), num_vms)
    for i in range(num_vms):
        peers = [j for j in range(num_vms) if j != i]
        vm = VirtualMachine(i, peers, available_speeds[i], base_port)
        vms.append(vm)
        threading.Thread(target=vm.run, daemon=True).start()
    return vms

def run_simulation_custom_variation(run_id, num_vms, run_time, base_port, min_speed, max_speed):
    # Create a directory for this run's logs.
    dir_name = f"custom_var_run_{run_id}_range_{min_speed}-{max_speed}"
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    
    print(f"[Run {run_id}] Starting simulation with clock speeds in range {min_speed}-{max_speed} for {run_time} seconds on base port {base_port}...")
    vms = start_virtual_machines_custom_variation(num_vms, base_port, min_speed, max_speed)
    
    time.sleep(run_time)
    
    for vm in vms:
        vm.stop()
    
    time.sleep(2)
    
    # Move log files to the run directory.
    for vm_id in range(num_vms):
        log_filename = f"vm_{vm_id}.log"
        if os.path.exists(log_filename):
            os.rename(log_filename, os.path.join(dir_name, log_filename))
    
    print(f"[Run {run_id}] Completed simulation.")

def main():
    num_runs = 5       # Number of runs
    num_vms = 3        # Number of virtual machines
    run_time = 60      # Run time per simulation in seconds
    base_port_start = 5100  # Starting base port
    
    
    for run_id in range(1, num_runs + 1):
        min_speed = random.randint(1, 4)
        max_speed = min_speed + 2
        base_port = base_port_start + (run_id * 100)
        run_simulation_custom_variation(run_id, num_vms, run_time, base_port, min_speed, max_speed)

if __name__ == "__main__":
    main()