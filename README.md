# 🌐 Nexus Network Simulator (Phase 3)

**Developer:** Amir Khedri  
**Course:** Computer Networks - Phase 3  
**University:** University of Isfahan  

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![GUI](https://img.shields.io/badge/Interface-Tkinter-green.svg)
![Protocol](https://img.shields.io/badge/Protocols-OSPF%20%2F%20RIP%20%2F%20BGP-orange.svg)

## 📖 Project Overview
**Nexus** is a comprehensive **Network Routing Simulator** designed to visualize how packets traverse a network topology. It implements core routing algorithms from scratch—including **Link-State (OSPF)**, **Distance-Vector (RIP)**, and **Path-Vector (BGP)**—without relying on operating system sockets.

The project features an advanced **Graphical User Interface (GUI)** that allows users to manipulate network topologies, toggle links on/off, inject packets, and watch them travel node-by-node in real-time based on the calculated routing tables.

## ✨ Key Features

### 🧠 Routing Algorithms (Logic)
* **Link-State (OSPF):**
    * Implements **LSA Flooding** to build a synchronized Link-State Database (LSDB).
    * Runs **Dijkstra’s Algorithm** to calculate the Shortest Path Tree (SPT).
    * Supports **OSPF Areas** (Area 0 vs. Area 1) with Summary LSAs for inter-area routing.
* **Distance-Vector (RIP):** Uses the Bellman-Ford equation to exchange distance vectors and converge based on hop counts.
* **Border Gateway Protocol (BGP):** Simulates inter-AS routing using Path Vectors to prevent loops.

### 🖥️ Interactive Simulation (GUI)
* **Live Topology:** Visualizes Routers, Links, and Costs on a 2D canvas.
* **Packet Animation:** Animates packets moving along calculated paths; handles packet loss if routes are down.
* **Dynamic Changes:** Allows users to **break links** or **change costs** mid-simulation to see how protocols reconverge.
* **Inspection:** Click on any router to view its full **Routing Table** and neighbor relationships.

## 🛠️ Usage

### Running the Simulator
1.  Clone the repository:
    ```bash
    git clone https://github.com/amirkhedri/Nexus-Routing-Sim.git
    ```
2.  Run the main application:
    ```bash
    python main_gui.py
    ```

### How to Test
1.  **Configure:** On the left sidebar, select a **Scenario** (e.g., "Complex") and a **Protocol** (e.g., "Link-State OSPF").
2.  **Run:** Click **"⚡ RUN CONVERGENCE"**. The log will show LSA flooding and table calculation.
3.  **Inspect:** Click a router node (circles) to see its Routing Table on the right.
4.  **Send Packet:** Enter Source `A` and Destination `F` in the "ACTIONS" panel and click **SEND**. Watch the green packet travel.
5.  **Break Links:** Click **"❌ Toggle Link"**, type `A-B`, and re-run convergence to see the route change.

## 🏗️ Architecture

```mermaid
graph TD
    User["👤 User Interaction"] -->|1. Config & Actions| GUI["🖥️ Nexus GUI (Tkinter)"]
    
    subgraph "Simulation Engine (network_logic.py)"
        GUI -->|2. Trigger| Simulator["⚙️ NetworkSimulator"]
        Simulator -->|Manage| RouterList["📚 Virtual Routers"]
        
        RouterList -->|Flooding| LSDB["🗃️ Link-State DB"]
        LSDB -->|Dijkstra| Algo{"🧮 Routing Algo"}
        
        Algo -- OSPF/RIP/BGP --> Table["📋 Forwarding Table"]
    end
    
    subgraph "Visual Layer"
        Table -->|Next Hop| PacketAnim["📦 Packet Animation"]
        Simulator -->|Topology Data| Canvas["🎨 Dynamic Canvas"]
    end
    
    PacketAnim --> GUI
    Canvas --> GUI
