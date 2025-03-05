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
   - Run the simulation for set duration 1 minute
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

## Experiment Observations
  - Contained in the following google doc: https://docs.google.com/document/d/1Uo3jai-KjTx62crjMNpiCi_Mf5y8zMYdeLYI5_HZhaI/edit?usp=sharing
  - All analysis images are in the github as well
---

## Experiment Analysis with Standard Config

- **Size of the jumps in the values for the logical clocks:**  
  Upon receiving a message, the clock is updated using the maximum of its current value and the received timestamp plus one. This contributes to the larger jumps, especially if the sending VM’s clock is significantly ahead. In the experiments, we saw mean jumps ranging from about 1.0 (indicating mostly internal events or well-synchronized exchanges) to values as high as 3.81 or more. For example, in Run 1, VM 0 (with a slow clock speed of 1 tick/sec) had a mean jump of 3.81 and a maximum jump of 19, indicating that messages from faster VMs caused dramatic increases in its clock. VMs with higher clock speeds tend to have smaller jumps on average (often close to 1.0), since they progress quickly on their own. In contrast, slower VMs receive messages from faster ones that force their clocks to “jump” more to catch up on synchronization. This contributes to the phenominem of VMs that are significantly slower tend to show higher mean jumps. A maximum jump value, which in some runs is as high as 19 or 16, indicates sporadic but dramatic updates when a very high clock value is received from the faster VMs. Having more sporadic updates also contributes to how slower VMs have a much larger variance in jump sizes. 

- **Drift in the values of the local logical clocks in the different machines:**  
  In runs where the clock speeds differ by a lot, the drift can become large over time. In different runs, the average drift between VMs varied. Runs where the speeds were closer (for example, in Run 2) showed lower drift compared to runs with a wider spread of clock speeds (for example, Run 5). It seems that drift tends to accumulate gradually when there are persistent differences in the internal tick rates (Run 5 for example). Even if occasional messages help synchronize the clocks, the underlying differences cause the gap to widen again as time moves forward. We also note the relationship between jumps and drifts: the jumps in logical clocks highlight moments when a VM’s logical clock is forced to synchronize with an incoming message, so the larger these gaps, the more pronounced the drift becomes. There is also an indirect relationship between drift and the message queue length. VMs that are slower and accumulate larger drift also tend to have higher queue lengths. This suggests that they are not processing incoming messages as quickly as they arrive, thereby reinforcing the timing drifts.

- **Impact of timing on gaps and message queue length:**  
    - The size of the jumps is directly related to the timing and synchronization of message exchanges. Larger gaps are seen when a slower VM suddenly receives an update from a faster one, therefore jumping to a higher value. This is clearly seen in runs where the slower VMs had significantly larger mean jumps. 
    - The length of the message queue can serve as a proxy for how overwhelmed a VM is in processing incoming messages.For instance, in Run 5, VM 1 had an average queue length of 9.66, suggesting that this VM (with a slower clock speed) was overwhelmed by incoming messages from faster peers.  Conversely, VMs with faster or more consistent processing showed near-zero queue lengths. High message queue lengths tend to occur in slower VMs, reflecting that they cannot process incoming messages as quickly as they arrive from faster machines. This is tied to the large jumps in clock values when these messages are finally processed.

---

## Experiment Analysis on smaller variation in clock cycle

- **Smaller jumps overall:**  
  We observe smaller jumps overall. With a narrower range in clock speeds, the difference between internal increments and message-induced updates becomes smaller. When all VMs operate in a tighter range, the logical clock values tend to increment by roughly one unit even after processing external messages. This results in mean clock jumps that are consistently near 1.0, as opposed to runs with larger disparities, where you observed jumps with mean values well above 3 and occasional maximum jumps reaching 16 or 19 (run 5 for example). We also observe that  when VMs have similar tick rates, the variation of the clock jumps drops, indicating that the synchronization behavior is more steady. 

- **Lower average drift:**  
  In terms of drift, we see that with a smaller variation in clock speeds, the overall drift between the VMs is significantly reduced. Since all machines are incrementing their clocks at nearly the same rate, the difference in their logical clock values remains small over time. Smaller variations mean that the VMs are more naturally synchronized. Even when messages are exchanged, the clocks are already closely aligned, so the update alters less of the internal incrementing. Additionally, since the rate of message sending and processing are better balanced across VMs as no single VM is overwhelmed by incoming messages, synchronization happens in a more timely fashion resulting in smaller drift as the slower VMs are consistently catching up with the faster VMs.

- **Lower average queue length:**  
  There is also less queue buildup. We see consistently low average queue lengths across the runs with smaller variation. The reason for this is also mentioned above as the VMs are able to process messages in a more synchronized, timely fashion, avoiding backlogs that could further exacerbate clock jumps and contribute to drifts when a large number of messages waiting to be processed.

---

## Experiment Analysis on smaller probability of the event being internal

- **Smaller and more frequent clock jumps:**  
  With a lower internal event probability, VMs send messages more often, so on average more updates happen. In runs with, for example, p_internal=0.1 or 0.2, the slower VMs are forced to catch up more frequently. This results in smaller average clock jumps and smaller maximum jumps compared to configurations with a higher internal event probability (such as the baseline p_internal=0.7), since the "time" elasped between sending messages from faster VMs is smaller when we have a smaller internal probability than when the probability is higher and most events are internal and the clock only increments by 1.

- **Drift behavior:**
  We observe that at small, 0.1 and 0.2, internal event probability, the drift metrics (both average and maximum) tend to be higher than at some mid-range probabilities. The drift values drop and then rise again across the probabilities (0.3–0.6), and at p_internal=0.7, the system exhibits smaller average and maximum drift compared to lower probabilities. Overall, it seems to follow that smaller internal event probabilities lead to larger drifts. This is most likely due to when internal event probability is small, a slow VM can be inundated by messages from faster peers. The slow VM will then have a huge backlog on its queue and will have to continue to process messages that are not recent. Therefore, although the slow VM ends up performing more updates, the updates are further and further back in "time" relative to system time as the sytem progresses. 

- **Longer message queue lengths:**
  We first observe high queue length at very low p_internal (0.1 or 0.2). As p_internal grows, fewer external messages are generated, so the queue length drops. By p_internal=0.7, the average queue length is near 1. A smaller internal probability means each VM sends messages more often, increasing the overall message volume. If some VMs are slower (or if the random event scheduling bunches messages), large queues form. In contrast, a larger internal probability means fewer sends, reducing the chance of backlogs.

*This notebook will be updated as the project evolves, with further experiments and analysis results to follow.*
