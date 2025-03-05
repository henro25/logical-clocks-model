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
- **`analyze_logs.py`**: Script to process, visualize and summarize log data for multiple runs.
- **`experiment_logs/`**: Directory for generated experiment log files.
- **`StandardConfigAnalysisImages/`**: Directory for generated analysis images for logs of runs under standard configurations.
- **`LogicalClockAnalysisImages/`**: Directory for generated analysis images for logs of runs under smaller internal probability experiments.
- **`CustomVariationAnalysis/`**: Directory for generated analysis images for logs of runs under smaller clock cycle variation experiments.
- **`notebook.md`**: Our engineering notebook that contains project overview, design decisions, and hypotheses.
- **`internal_prob_analysis.py`**: Script to process, visualize and summarize experiments ran on different smaller internal event probabilities.
- **`run_scale_model.py`**: Script to run baseline model multiple times.
- **`smaller_prob_experiements.py`**: Script to run experiments over different smaller internal event probabilities.
- **`test_vm_simulation.py`**: Tests for the VM class.
- **`visualize_logs.py`**: Script to visualize log data for single run.
- **`smaller_variation_analysis.py`**: Script to visualize log data for smaller clock cycle variation experiments.
- **`smaller_variation_experiments.py`**: Script to run experiments over different small ranges of clock variation.

## Getting Started

1. **Clone the Repository:**
    ```bash
    git clone https://github.com/henro25/logical-clocks-model.git
    cd logical-clocks-model
    ```
2. **Create Virtual Environment and Install Requirements:
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
3. **Run the Simulation:**
    ```bash
    python vm_simulation.py
    ```
4. **Analyze Results:**
    ```bash
    python analyze_logs.py
    ```
