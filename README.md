Speed Test Network

Overview

This project is a client-server application designed to evaluate and compare the performance of TCP and UDP protocols for file transfers. The system measures download speeds and analyzes how the two protocols share the network. It was developed for the Intro to Nets 2024 Hackathon, version 1.0, titled "Speed Test."

Features

Client-Server Architecture:

Server handles TCP and UDP file transfers simultaneously.

Client initiates tests and manages the measurement of speeds.

Multi-Threaded Design:

The client creates multiple threads for simultaneous TCP and UDP transfers in the speed testing phase.

Protocol Comparison:

Measures and logs the performance of TCP and UDP file transfers.

Interactive Client States:

Initializing: The client collects user parameters.

Searching for a Server: The client discovers the server.

Speedtesting: Executes the speed test using multiple threads.

Prerequisites

Python 3.8+ installed

Knowledge of networking concepts, especially TCP and UDP protocols.

