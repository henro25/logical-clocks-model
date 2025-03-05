import socket
import threading
import queue
import time
import random

class VirtualMachine:
    def __init__(self, vm_id, peers, clock_rate, base_port, internal_prob=0.7):
        self.vm_id = vm_id
        self.logical_clock = 0
        self.clock_rate = clock_rate
        self.peers = peers  # List of peer VM IDs
        self.running = True
        self.base_port = base_port
        self.start_time = time.time()
        self.queue = queue.Queue()
        self.internal_event_prob = internal_prob
        
        # Create a lock to guard logging operations.
        self.log_lock = threading.Lock()
        
        # Create a TCP server socket for receiving messages.
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("localhost", base_port + vm_id))
        self.server_socket.listen()
        self.server_socket.settimeout(1.0)  # Timeout for accept so we can check self.running
        
        self.log_file = open(f"vm_{vm_id}.log", "w")
        
        # Log and print the clock speed.
        init_msg = f"Starting VM {vm_id} with clock speed: {self.clock_rate} ticks/sec\n"
        print(init_msg)
        # comment out logging init to prevent data race
        # self.log_event("Init\t", init_msg)
        
        # Start a thread to accept incoming TCP connections.
        self.server_thread = threading.Thread(target=self.server_loop, daemon=True)
        self.server_thread.start()

    def log_event(self, event_type, details):
        with self.log_lock:
            # If the log file is closed, skip logging.
            if self.log_file.closed:
                return
            try:
                elapsed = time.time() - self.start_time
                queue_length = self.queue.qsize()
                # Log the elapsed time, event type, logical clock, current queue length, and additional details.
                log_entry = f"{elapsed:.3f}\t{event_type}\tLogical Clock: {self.logical_clock}\tQueue Length: {queue_length}\t{details}\n"
                self.log_file.write(log_entry)
                self.log_file.flush()
            except Exception:
                # If logging fails, ignore the error.
                pass

    def server_loop(self):
        # Continuously accept connections and push received messages into the queue.
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                # Read the incoming message
                data = conn.recv(1024)
                if data:
                    try:
                        received_timestamp = int(data.decode())
                        # Put the received timestamp into the queue
                        self.queue.put(received_timestamp)
                    except ValueError:
                        pass
                conn.close()
            except socket.timeout:
                continue
            except Exception as e:
                print(f"VM {self.vm_id} server error: {e}")
                continue

    def process_message(self, received_timestamp):
        # Update the logical clock as per Lamport's rule and log the event.
        self.logical_clock = max(self.logical_clock, received_timestamp) + 1
        self.log_event("Receive", "From Network")

    def send_message(self, target_vm, timestamp):
        # Create a new TCP socket for sending the message.
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                # Connect using the same base_port as used by the server.
                s.connect(("localhost", self.base_port + target_vm))
                s.sendall(str(timestamp).encode())
            # Note: Logging is handled by the caller to avoid duplicate log entries.
        except Exception as e:
            self.log_event("Send Error", f"To VM {target_vm}: {e}")

    def run(self):
        while self.running:
            # Sleep to simulate tick rate.
            time.sleep(1 / self.clock_rate)

            # Process one message if available.
            if not self.queue.empty():
                try:
                    received_timestamp = self.queue.get_nowait()
                    self.process_message(received_timestamp)
                    # If a message was processed, skip the random event this tick.
                    continue
                except queue.Empty:
                    pass

            # Otherwise, perform a random event.
            # event = random.randint(1, 10)
            # if event == 1:
            #     # Send to first peer.
            #     if len(self.peers) >= 1:
            #         self.logical_clock += 1
            #         current_timestamp = self.logical_clock
            #         self.send_message(self.peers[0], current_timestamp)
            #         self.log_event("Send", f"To VM {self.peers[0]}")
            # elif event == 2:
            #     # Send to second peer.
            #     if len(self.peers) >= 2:
            #         self.logical_clock += 1
            #         current_timestamp = self.logical_clock
            #         self.send_message(self.peers[1], current_timestamp)
            #         self.log_event("Send", f"To VM {self.peers[1]}")
            # elif event == 3:
            #     # Send to all peers as one event.
            #     self.logical_clock += 1
            #     current_timestamp = self.logical_clock
            #     for peer in self.peers:
            #         self.send_message(peer, current_timestamp)
            #     self.log_event("Send All", f"To VMs {self.peers}")
            # else:
            #     # Internal event.
            #     self.logical_clock += 1
            #     self.log_event("Internal", "No external communication")
            # event generation for smaller internal probabilities
            r = random.random()
            p_internal = self.internal_event_prob
            p_send_each = (1 - p_internal) / 3

            if r < p_internal:
                # Internal event.
                self.logical_clock += 1
                self.log_event("Internal", "No external communication")
            elif r < p_internal + p_send_each:
                # Send to first peer.
                if len(self.peers) >= 1:
                    self.logical_clock += 1
                    current_timestamp = self.logical_clock
                    self.send_message(self.peers[0], current_timestamp)
                    self.log_event("Send", f"To VM {self.peers[0]}")
                else:
                    # Fallback: internal event.
                    self.logical_clock += 1
                    self.log_event("Internal", "Fallback event")
            elif r < p_internal + 2 * p_send_each:
                # Send to second peer.
                if len(self.peers) >= 2:
                    self.logical_clock += 1
                    current_timestamp = self.logical_clock
                    self.send_message(self.peers[1], current_timestamp)
                    self.log_event("Send", f"To VM {self.peers[1]}")
                else:
                    # Fallback: internal event.
                    self.logical_clock += 1
                    self.log_event("Internal", "Fallback event")
            else:
                # Send to all peers.
                self.logical_clock += 1
                current_timestamp = self.logical_clock
                for peer in self.peers:
                    self.send_message(peer, current_timestamp)
                self.log_event("Send All", f"To VMs {self.peers}")

    def stop(self):
        self.running = False
        self.server_socket.close()
        self.log_file.close()

def start_virtual_machines(num_vms, base_port, internal_prob=0.7):
    vms = []
    # Generate unique clock speeds (distinct integers between 1 and 6)
    available_speeds = random.sample(range(1, 7), num_vms)
    for i in range(num_vms):
        peers = [j for j in range(num_vms) if j != i]  # All other VM IDs.
        vm = VirtualMachine(i, peers, available_speeds[i], base_port, internal_prob=internal_prob)
        vms.append(vm)
        threading.Thread(target=vm.run, daemon=True).start()
    return vms

if __name__ == "__main__":
    num_vms = 3  # Three virtual machines
    vms = start_virtual_machines(num_vms, 5000)

    # Run simulation for 5 seconds
    time.sleep(5)

    # Stop all VMs
    for vm in vms:
        vm.stop()
