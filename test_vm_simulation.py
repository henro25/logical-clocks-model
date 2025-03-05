import os
import time
import socket
import threading
import random
import queue
import pytest
import builtins  # to get the original open

from vm_simulation import VirtualMachine, start_virtual_machines

# ----- Helper to override file creation to use a temporary directory -----
@pytest.fixture
def temp_open(tmp_path, monkeypatch):
    # Save the original open so we can call it inside fake_open.
    original_open = builtins.open

    def fake_open(filename, mode):
        # Replace any path so that the file is created in tmp_path.
        base = tmp_path / os.path.basename(filename)
        return original_open(base, mode)
    
    monkeypatch.setattr(builtins, "open", fake_open)
    return tmp_path

# ----- Test that the log file is created -----
def test_log_file_creation(temp_open):
    vm = VirtualMachine(0, peers=[], clock_rate=1, base_port=5000)
    # Allow a little time for the init log to be written.
    time.sleep(0.1)
    vm.stop()
    # Check that the log file exists in the temporary directory.
    log_path = temp_open / "vm_0.log"
    assert log_path.exists(), "Log file was not created."

# ----- Test that processing a message updates the logical clock correctly -----
def test_logical_clock_update(temp_open):
    vm = VirtualMachine(1, peers=[], clock_rate=1, base_port=5000)
    initial_clock = vm.logical_clock
    # Process a message with a timestamp that is higher than the current clock.
    vm.process_message(10)
    # Per Lamport's rule, logical_clock should become max(initial,10)+1.
    assert vm.logical_clock == max(initial_clock, 10) + 1, "Logical clock not updated correctly."
    vm.stop()
    
    # Verify that the log contains a "Receive" event.
    log_path = temp_open / "vm_1.log"
    content = log_path.read_text()
    assert "Receive" in content, "Receive event not logged."

# ----- Test that an error in send_message (e.g. connecting to an unreachable VM) is logged -----
def test_send_message_error(temp_open):
    vm = VirtualMachine(2, peers=[], clock_rate=1, base_port=5000)
    # Attempt to send to an unlikely port (e.g. VM id 999 which isn't running).
    vm.send_message(999, 5)
    time.sleep(0.1)  # Give a moment for the error to be logged.
    vm.stop()
    log_path = temp_open / "vm_2.log"
    content = log_path.read_text()
    assert "Send Error" in content, "Send error was not logged."

# ----- Test that the server loop receives a message and processing it updates the clock -----
def test_server_receives_message(temp_open):
    base_port = 5000
    vm = VirtualMachine(3, peers=[], clock_rate=1, base_port=base_port)
    # Create a client socket to send a valid timestamp to the VM's server.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(("localhost", base_port + 3))
        s.sendall(b"7")
    # Allow some time for the server thread to accept and queue the message.
    time.sleep(1)
    if not vm.queue.empty():
        ts = vm.queue.get_nowait()
        vm.process_message(ts)
        # Expected clock becomes max(0,7)+1 = 8.
        assert vm.logical_clock == 8, "Logical clock not synchronized after processing received message."
    else:
        pytest.fail("Server did not receive any message.")
    vm.stop()

# ----- Test that an internal event is logged (forcing a non-message event) -----
def test_internal_event(monkeypatch, temp_open):
    # Force random.randint to always return a value that triggers an internal event.
    monkeypatch.setattr(random, "randint", lambda a, b: 4)
    vm = VirtualMachine(4, peers=[], clock_rate=1, base_port=5000)
    # Run the VM's main loop in a thread for a short period.
    thread = threading.Thread(target=vm.run, daemon=True)
    thread.start()
    time.sleep(1.5)
    vm.stop()
    log_path = temp_open / "vm_4.log"
    content = log_path.read_text()
    assert "Internal" in content, "Internal event not logged as expected."
