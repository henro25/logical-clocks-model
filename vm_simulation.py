import socket
import multiprocessing
import queue
import time
import random
import os

class VirtualMachine(multiprocessing.Process):
    def __init__(self, vm_id, peers, clock_rate, base_port, internal_prob=0.7):
        super().__init__()
        self.vm_id = vm_id
        self.logical_clock = 0
        self.clock_rate = clock_rate
        self.peers = peers
        self.base_port = base_port
        self.internal_event_prob = internal_prob

        self.running = multiprocessing.Value('b', True)  # Shared boolean flag
        self.queue = multiprocessing.Queue()  # Cross-process queue
        self.queue_size = multiprocessing.Value('i', 0)  # Track queue length manually
        self.server_socket = None  # Delayed creation

    def setup_server(self):
        """Initializes the server socket after process starts."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("localhost", self.base_port + self.vm_id))
        self.server_socket.listen()
        self.server_socket.settimeout(1.0)  # Prevent blocking indefinitely

    def log_event(self, event_type, details):
        """Logs an event to the VM's log file."""
        elapsed = time.time() - self.start_time
        with open(f"vm_{self.vm_id}.log", "a") as log_file:
            log_entry = f"{elapsed:.3f}\t{event_type}\tLogical Clock: {self.logical_clock}\tQueue Length: {self.queue_size.value}\t{details}\n"
            log_file.write(log_entry)

    def server_loop(self):
        """Handles incoming messages from other VMs."""
        while self.running.value:
            try:
                conn, addr = self.server_socket.accept()
                data = conn.recv(1024)
                if data:
                    try:
                        received_timestamp = int(data.decode())
                        self.queue.put(received_timestamp)
                        with self.queue_size.get_lock():  # Safely update queue size
                            self.queue_size.value += 1
                    except ValueError:
                        pass
                conn.close()
            except (socket.timeout, BlockingIOError):
                continue  # Avoid crash on empty queue

    def process_message(self, received_timestamp):
        """Updates the logical clock using Lamport’s rule."""
        self.logical_clock = max(self.logical_clock, received_timestamp) + 1
        self.log_event("Receive", "From Network")
        with self.queue_size.get_lock():
            self.queue_size.value -= 1  # Decrease queue count safely

    def send_message(self, target_vm, timestamp):
        """Sends a message to a target VM."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(("localhost", self.base_port + target_vm))
                s.sendall(str(timestamp).encode())
        except Exception as e:
            self.log_event("Send Error", f"To VM {target_vm}: {e}")

    def run(self):
        """Main execution loop for the VM process."""
        self.start_time = time.time()  # Start time tracking
        self.setup_server()  # Create server socket after process starts

        print(f"Starting VM {self.vm_id} with clock speed: {self.clock_rate} ticks/sec")
        
        server_process = multiprocessing.Process(target=self.server_loop, daemon=True)
        server_process.start()

        while self.running.value:
            time.sleep(1 / self.clock_rate)

            # Process received messages
            while not self.queue.empty():
                try:
                    received_timestamp = self.queue.get_nowait()
                    self.process_message(received_timestamp)
                except queue.Empty:
                    break

            # Decide the next event
            r = random.random()
            p_internal = self.internal_event_prob
            p_send_each = (1 - p_internal) / 3

            if r < p_internal:
                self.logical_clock += 1
                self.log_event("Internal", "No external communication")
            elif r < p_internal + p_send_each and len(self.peers) >= 1:
                self.logical_clock += 1
                self.send_message(self.peers[0], self.logical_clock)
                self.log_event("Send", f"To VM {self.peers[0]}")
            elif r < p_internal + 2 * p_send_each and len(self.peers) >= 2:
                self.logical_clock += 1
                self.send_message(self.peers[1], self.logical_clock)
                self.log_event("Send", f"To VM {self.peers[1]}")
            else:
                self.logical_clock += 1
                for peer in self.peers:
                    self.send_message(peer, self.logical_clock)
                self.log_event("Send All", f"To VMs {self.peers}")

        server_process.terminate()
        server_process.join()

    def stop(self):
        """Stops the VM and cleans up resources."""
        self.running.value = False
        if self.server_socket:
            self.server_socket.close()


def start_virtual_machines(num_vms, base_port, internal_prob=0.7):
    """Spins up multiple Virtual Machines in separate processes."""
    vms = []

    available_speeds = random.sample(range(1, 7), num_vms)
    for i in range(num_vms):
        peers = [j for j in range(num_vms) if j != i]  # All other VMs as peers
        vm = VirtualMachine(i, peers, available_speeds[i], base_port, internal_prob)
        vms.append(vm)
        vm.start()  # Start the VM process

    return vms


if __name__ == "__main__":
    num_vms = 3  # Number of virtual machines
    vms = start_virtual_machines(num_vms, 5000)

    # Run simulation for 60 seconds
    time.sleep(60)

    # Stop all VMs
    for vm in vms:
        vm.stop()
        vm.terminate()
        vm.join()
