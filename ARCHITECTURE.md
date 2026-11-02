# 🏗️ Project Aura: System Architecture & Verification Plan

This document outlines the Model-Based Systems Engineering (MBSE) approach used in Project Aura, focusing on early architectural verification and interface consistency.

## 1. System Requirements (Top-Level)
- **REQ-01:** The system shall ingest live TLE data from external APIs (Celestrak/Space-Track).
- **REQ-02:** The system shall propagate orbits using high-fidelity numerical models (Orekit/SGP4).
- **REQ-03:** The system shall calculate Probability of Collision (Pc) using Covariance Matrices.
- **REQ-04:** The system shall autonomously flag High-Risk conjunctions (Pc > 1e-4) and simulate Collision Avoidance Maneuvers (CAM).
- **REQ-05:** The system shall preserve network topology (NA-CAM) during orbital maneuvers.

## 2. Logical Subsystems & Interfaces
- **Data Ingestion Module:** Fetches TLEs and parses them into a standardized JSON payload.
- **Propagation Engine (Orekit):** Consumes TLEs, outputs 3D State Vectors (X, Y, Z) and Covariance Matrices.
- **Threat Analyzer:** Evaluates TCA (Time of Closest Approach) and calculates Pc.
- **Network Analyzer (NA-CAM):** Monitors inter-satellite link distances. Interfaces with the Threat Analyzer to ensure maneuvers do not break communication links.
- **User Interface (Streamlit):** Consumes JSON outputs from the backend for 3D visualization and telemetry display.

## 3. Architectural Verification (Pre-Implementation)
Following MBSE principles, the system architecture is verified before physical deployment using:
- **Digital Twin Simulation:** A 3D kinematic simulation of the constellation to verify missing interactions (e.g., optical link failure during CAM).
- **Monte Carlo Analysis:** Running 80,000+ samples to validate the robustness of the Pc calculation against positional uncertainty.
- **Fault Injection:** Simulating "Zero Ground Control" scenarios to verify the autonomous decision-making logic.

## 4. The "Bigger Picture" (Verification vs. Validation)
While the model verifies that the algorithms (like SGP4/Orekit) behave as expected, physical verification (integration with live ground stations) remains essential for final validation. The current architecture provides a credible, simulation-driven foundation.
