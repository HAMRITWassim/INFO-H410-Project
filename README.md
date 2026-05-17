# AI Combat Simulator: A Comparative Analysis
### INFO-H410 - Techniques of Artificial Intelligence (ULB)

This repository contains a comparative study of three distinct AI techniques—**Expectiminimax**, **Markov Decision Processes (MDP)**, and **Reinforcement Learning (Q-Learning)**—applied to a stochastic, turn-based battle environment. The goal is for an AI agent to defeat a heuristic-based Bot by managing resources (HP, Mana, Potions) and accounting for elemental advantages and game stochasticity.

## Project Overview
The battle system features:
* **Stochastic Mechanics**: Attacks have a 10% chance to miss and a 15% chance to land a critical hit.
* **Elemental Affinity System**: A triangular interaction model (Fire, Water, Grass) that applies damage bonuses based on type advantages.
* **Tactical Actions**: Agents can choose between Attacking, Healing, or Defending.
* **Victory Condition**: Reduce the opponent's HP to 0 while maintaining your own survival.

## Execution Instructions

To reproduce the experimental results presented in the report or to watch the AI agents in action, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/HAMRITWassim/INFO-H410-Project.git
    ```
2.  **Navigate directly to the source directory:**
    ```bash
    cd ./INFO-H410-Project/source
    ```
3.  **Run the main script:**
    ```bash
    python main.py
    ```
4.  **Follow the CLI Prompts:**
    * Select the **AI Type** (1. Fire, 2. Water, or 3. Grass).
    * Select the **Bot Type** (1. Fire, 2. Water, or 3. Grass).

The program will then execute the evaluation of all three approaches in sequence, displaying real-time win rates and a final performance dashboard comparing execution times and accuracy.

## Implemented Approaches
* **Approach A: Expectiminimax**: Real-time adversarial search evaluating expected utility through a game tree with chance nodes.
* **Approach B: MDP (Value Iteration)**: Offline planning using the Bellman equation to find a global optimal policy across a discretized state space.
* **Approach C: Q-Learning**: Model-free reinforcement learning that learns through 5,000 episodes of trial and error.

## Repository Structure
* `source/main.py`: The unified entry point for the simulation.
* `source/environment.py`: The core game engine and transition logic.
* `source/ai_expectiminimax.py`: Implementation of the search-based agent.
* `source/ai_mdp.py`: Implementation of the Value Iteration agent.
* `source/ai_rl.py`: Implementation of the Q-Learning agent.
* `source/bot.py`: The heuristic-based opponent logic.

## Authors
* **Adam FAR**
* **Wassim HAMRIT**
* **Ibrahim OZEL**

---
*Developed as part of the INFO-H410 course at Université Libre de Bruxelles.*
