import socket
import threading
import queue
import time
import random

class VirtualMachine:
    def __init__(self, vm_id, peers):
        self.vm_id = vm_id
        self.logical_clock = 0
        self.clock_rate = random.randint(1, 6)  # Random clock ticks per second
        self.peers = peers  # List of peer VM addresses
        self.queue = queue.Queue()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP socket
        self.socket.bind(("localhost", 5000 + vm_id))  # Unique port per VM
        self.running = True
        self.log_file = open(f"vm_{vm_id}.log", "w")

    def log_event(self, event_type, details):
        timestamp = time.time()
        log_entry = f"{timestamp}, VM {self.vm_id}, {event_type}, Logical Clock: {self.logical_clock}, {details}\n"
        self.log_file.write(log_entry)
        self.log_file.flush()

    def handle_message(self):
        while self.running:
            try:
                msg, _ = self.socket.recvfrom(1024)
                received_timestamp = int(msg.decode())
                self.logical_clock = max(self.logical_clock, received_timestamp) + 1
                self.log_event("Receive", f"From Network, Queue Size: {self.queue.qsize()}")
            except BlockingIOError:
                pass  # No message, continue loop

    def send_message(self, target_vm):
        self.logical_clock += 1
        self.socket.sendto(str(self.logical_clock).encode(), ("localhost", 5000 + target_vm))
        self.log_event("Send", f"To VM {target_vm}")

    def run(self):
        threading.Thread(target=self.handle_message, daemon=True).start()
        while self.running:
            time.sleep(1 / self.clock_rate)  # Simulate different machine speeds

            if not self.queue.empty():
                self.handle_message()
            else:
                event = random.randint(1, 10)
                if event == 1:
                    self.send_message(random.choice(self.peers))
                elif event == 2:
                    self.send_message(random.choice(self.peers))
                elif event == 3:
                    for peer in self.peers:
                        self.send_message(peer)
                else:
                    self.logical_clock += 1
                    self.log_event("Internal Event", "No external communication")

    def stop(self):
        self.running = False
        self.socket.close()
        self.log_file.close()

def start_virtual_machines(num_vms):
    vms = []
    for i in range(num_vms):
        peers = [j for j in range(num_vms) if j != i]  # Connect to all other VMs
        vm = VirtualMachine(i, peers)
        vms.append(vm)
        threading.Thread(target=vm.run, daemon=True).start()
    
    return vms

if __name__ == "__main__":
    num_vms = 3 
    vms = start_virtual_machines(num_vms)

    # Run simulation for 10 seconds
    time.sleep(10)

    # Stop all VMs
    for vm in vms:
        vm.stop()
