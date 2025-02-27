# Engineering Notebook: Modeling an Asynchronous Distributed System

**Date:** 2025-02-27  
**Authors:** Henry Huang and Bridget Ma

---

## Overview

In this project, we are building a simulation of a small, asynchronous distributed system running on a single machine. The system models multiple virtual machines (VMs), each with a unique clock rate and logical clock. Key aspects of the system include:

- **Asynchronous Operation:** Each VM runs at a different speed, determined randomly between 1 and 6 ticks per second.
- **Logical Clocks:** VMs maintain a logical clock updated on each event (tick, send, or receive) using Lamport's clock rules.
- **Message Passing:** VMs communicate via network sockets, and each VM maintains a network queue for incoming messages.
- **Logging:** Every event (internal, send, receive) is logged with details such as system time, logical clock value, and message queue size.
- **Experimentation:** The model will be run under various configurations to observe clock drift, message delays, and event ordering.

---

## Initial Outline

1. **System Components & Design**
   - **Virtual Machine (VM) Class:**
     - Attributes: `vm_id`, `logical_clock`, `clock_rate`, `peers`, `queue`, `socket`, `log_file`
     - Methods: 
       - `run()`: Main loop, ticking at the defined rate.
       - `handle_message()`: Process incoming messages and update the logical clock.
       - `send_message()`: Send messages to peer VMs.
       - `log_event()`: Log events (send, receive, internal).
   - **Communication Setup:**
     - Establish socket connections between VMs.
     - Ensure each VM can listen for and send messages concurrently.
   - **Logging:**
     - Record event details to individual log files for each VM.
     - Use log data for later analysis of clock behavior and message ordering.

2. **Implementation Strategy**
   - Use Python with modules: `socket`, `threading`, `queue`, `time`, and `random`.
   - Initialize VMs with unique clock speeds and ports.
   - Create a simulation loop where each tick can either trigger an internal event or a message event based on a random number.
   - Update the logical clock based on local ticks or message reception using:  
     `new_clock = max(local_clock, received_clock) + 1`
   - Analyze logs to visualize clock drift and event ordering.

3. **Experimentation & Analysis**
   - Run the simulation for set durations (e.g., 1 minute, 5 minutes).
   - Modify parameters: clock rate ranges, probabilities for message sending vs. internal events.
   - Record and compare results to understand how different configurations affect the system behavior.
   - Use visualizations (e.g., timeline plots) to illustrate logical clock progression.

---

## Hypothesis

- **Logical Clock Divergence:**  
  Given that each VM operates at a different clock rate, we expect that the logical clocks will diverge over time. Faster ticking VMs (e.g., 6 ticks/sec) will show a higher logical clock value compared to slower ones (e.g., 2 ticks/sec) if no message events occur.

- **Impact of Message Passing:**  
  When a slower VM sends a message to a faster VM, the receiving VM will update its logical clock to `max(local_clock, received_clock) + 1`, potentially causing a noticeable jump. This mechanism preserves the causality of events but may create non-uniform increments in logical clock values.

- **Effect of Internal vs. External Events:**  
  By adjusting the probabilities of internal events versus message sends, we hypothesize that:
  - A higher rate of internal events will lead to more uniform clock increments.
  - Increased message passing will introduce more variability, showcasing significant clock jumps and possible synchronization effects between VMs.

- **Observational Significance:**  
  Analyzing the logs and clock behavior will provide insights into:
  - The importance of synchronization mechanisms in distributed systems.
  - How independent processes can maintain causality without a global clock.
  - The trade-offs between event ordering precision and system performance in asynchronous networks.

---

*This notebook will be updated as the project evolves, with further experiments and analysis results to follow.*
