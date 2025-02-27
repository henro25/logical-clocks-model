# logical-clocks-model

This project simulates a small, asynchronous distributed system with multiple virtual machines (VMs) that operate at different clock speeds. Each VM maintains a logical clock updated per Lamport’s rules during internal events, message sends, and message receives.

## Overview

- **Multiple VMs:** Each VM has its own tick rate (randomly between 1 and 6 ticks/sec) and logical clock.
- **Logical Clocks:** Clocks are incremented on every tick and updated on message receipt using:  
  `new_clock = max(local_clock, received_clock) + 1`
- **Message Passing:** VMs communicate over UDP sockets with dedicated message queues.
- **Logging:** Each VM logs events (internal, send, receive) with system time, logical clock value, and message queue size.

## Project Structure

- **`vm_simulation.py`**: Implements the VM class, initialization, and simulation loop.
- **`analyze_logs.py`**: Script to process and visualize log data.
- **`logs/`**: Directory for generated log files.
- **`notebook.md`**: Our engineering notebook that contains project overview, design decisions, and hypotheses.

## Getting Started

1. **Clone the Repository:**
    ```bash
    git clone https://github.com/henro25/logical-clocks-model.git
    cd logical-clocks-model
    ```
2. **Run the Simulation:**
    ```bash
    python vm_simulation.py
    ```
3. **Analyze Results:**
    ```bash
    python analyze_logs.py
    ```

## Dependencies

1. Python 3.x (Standard libraries: socket, threading, queue, time, random)
2. Optional: pandas, matplotlib for analysis
