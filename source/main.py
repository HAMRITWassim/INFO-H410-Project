from environment import BattleEnvironment, TYPES
from bot import get_heuristic_bot_action
from ai_rl import QLearningAgent
from ai_mdp import ValueIterationAgent
from ai_expectiminimax import ExpectiminimaxAgent
import random
import copy
import time

def calculate_reward(old_state, new_state, is_game_over, winner):
    """
    Calculates the reward based on HP changes and match outcome
    """
    if is_game_over:
        if winner == "AI":
            return 100.0        # Big reward for winning
        
        if winner == "Bot":
            return -100.0       # Big penalty for losing
        
        return 0.0              # Draw

    # Intermediate reward
    damage_dealt = old_state["Bot"]["HP"] - new_state["Bot"]["HP"]
    damage_taken = old_state["AI"]["HP"] - new_state["AI"]["HP"]
    
    return float(damage_dealt - damage_taken)


def train_rl_agent(ai_type, bot_type, episodes=5000):
    """
    Phase 1 (RL): Training the Q-Learning agent 
    """
    print(f"\n--- STARTING RL TRAINING FOR {episodes} EPISODES ---")
    
    # Initialize Environment and Agent
    env = BattleEnvironment(ai_type=ai_type, bot_type=bot_type)
    
    # Can only use its OWN TYPE attack, heal, or defend
    legal_actions = [f"Attack_{env.ai_type}", "Heal", "Defend"]
    agent = QLearningAgent(legal_actions=legal_actions)

    win_count = 0

    for episode in range(episodes):
        env.reset()
        
        while not env.is_game_over():
            # 1. Observe current state
            # We use deepcopy so the old_state doesn't change when env updates
            old_state = copy.deepcopy(env.get_state())
            
            # 2. Choose actions
            action_ai = agent.choose_action(old_state, is_training=True)
            action_bot = get_heuristic_bot_action(old_state, env.bot_type, env.ai_type)
            
            # 3. Execute actions
            env.execute_turn(action_ai, action_bot, verbose=False)
            
            # 4. Observe new state and calculate reward
            new_state = env.get_state()
            is_over = env.is_game_over()
            if is_over:
                winner = env.get_winner()
            else:
                winner = None
            
            reward = calculate_reward(old_state, new_state, is_over, winner)
            
            # 5. Update Q-Table (Learn)
            agent.learn(old_state, action_ai, reward, new_state)

        if env.get_winner() == "AI":
            win_count += 1
            
        # Progress indicator
        if (episode + 1) % 1000 == 0:
            print(f"Episode {episode + 1}/{episodes} completed. AI Winrate: {(win_count/1000)*100:.1f}%")
            win_count = 0 # Reset win count for the next batch

    print("--- RL TRAINING COMPLETE ---")
    return agent


def setup_mdp_agent(ai_type, bot_type):
    """
    Phase 1 (MDP): Solving the MDP using Value Iteration
    """
    print(f"\n--- SOLVING MDP FOR {ai_type} vs {bot_type} ---")
    
    legal_actions = [f"Attack_{ai_type}", "Heal", "Defend"]
    agent = ValueIterationAgent(ai_type=ai_type, bot_type=bot_type, legal_actions=legal_actions)
    
    # State space must match the discretization in ai_mdp.py exactly
    hp_levels   = ["High", "Med", "Low"]
    mana_levels = ["High", "Low", "Empty"]
    potion_counts = [0, 1, 2, 3]
    
    all_states = []
    for ai_hp in hp_levels:
        for ai_mana in mana_levels:
            for ai_pots in potion_counts:
                for bot_hp in hp_levels:
                    for bot_mana in mana_levels:
                        all_states.append((ai_hp, ai_mana, ai_pots, bot_hp, bot_mana))
    
    agent.solve_mdp(all_states)
    print(f"--- MDP SOLVED ({len(all_states)} states) ---")
    return agent


def evaluate_agent(agent, env, num_matches=1000):
    """
    Phase 2: Evaluating any trained/solved agent over multiple matches.
    Works for RL, MDP, and Expectiminimax since they all share the 'choose_action' method
    """
    print(f"--- EVALUATING AGENT OVER {num_matches} MATCHES ---")
    win_count = 0
    loss_count = 0
    draw_count = 0

    for i in range(num_matches):
        env.reset()
        turn_number = 1

        while not env.is_game_over():
            state = env.get_state()
            
            # No random action (Epsilon = 0 during evaluation)
            action_ai = agent.choose_action(state, is_training=False)
            action_bot = get_heuristic_bot_action(state, env.bot_type, env.ai_type)
            
            env.execute_turn(action_ai, action_bot, verbose=False)
            turn_number += 1

            # Limit of 100 turns
            if turn_number > 100:
                break 

        winner = env.get_winner()
        if winner == "AI": 
            win_count += 1
        elif winner == "Bot": 
            loss_count += 1
        else: 
            draw_count += 1 

    win_rate = (win_count / num_matches) * 100
    print(f"Results: {win_count} Wins | {loss_count} Losses | {draw_count} Draws")
    print(f"Tested AI Winrate: {win_rate:.1f}%\n")
    return win_rate


def test_agent(agent, env):
    """
    Phase 3: Testing the agent 
    """
    print("\n--- BATTLE START (TESTING MODE) ---")
    env.reset()
    turn_number = 1

    while not env.is_game_over():
        print(f"\n=== TURN {turn_number} ===")
        state = env.get_state()
        
        action_ai = agent.choose_action(state, is_training=False)
        action_bot = get_heuristic_bot_action(state, env.bot_type, env.ai_type)
        
        env.execute_turn(action_ai, action_bot, verbose=True)
        turn_number += 1

        print("-" * 45)
        print(f"AI  ({env.ai_type})  - HP: {state['AI']['HP']:>3} | Mana: {state['AI']['Mana']:>2} | Potions: {state['AI']['Potions']}")
        print(f"Bot ({env.bot_type}) - HP: {state['Bot']['HP']:>3} | Mana: {state['Bot']['Mana']:>2} | Potions: {state['Bot']['Potions']}")

        if turn_number > 100:
            print("\nLIMIT REACHED, NO WINNER!")
            return
            
    print("\n--- BATTLE END ---")
    print(f"The winner is: {env.get_winner()}!")


def choose_type(player_name):
    """
    Interface to select the element type
    """
    print(f"\nChoose {player_name} type:")
    print("1. Fire")
    print("2. Water")
    print("3. Grass")
    
    while True:
        try:
            choice = int(input("Enter 1, 2, or 3: "))
            if choice == 1:
                return "Fire"
            elif choice == 2:
                return "Water"
            elif choice == 3:
                return "Grass"
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
        except ValueError:
            print("Invalid input. Please enter a number.")


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    # 0. Choose the types
    print("=== SETUP MATCH ===")
    selected_ai_type = choose_type("AI")
    selected_bot_type = choose_type("Bot")

    print(f"\n--- AI TYPE: {selected_ai_type} ---")
    print(f"--- BOT TYPE: {selected_bot_type} ---")

    # Base environment for evaluations
    eval_env = BattleEnvironment(ai_type=selected_ai_type, bot_type=selected_bot_type)

    # ---------------------------------------------------------
    # APPROACH 1: EXPECTIMINIMAX (Adversarial Search)
    # ---------------------------------------------------------
    print("\n" + "="*40)
    print("APPROACH 1: EXPECTIMINIMAX")
    print("="*40)

    # Instantiation (no training needed)
    expecti_agent = ExpectiminimaxAgent(ai_type=selected_ai_type, bot_type=selected_bot_type, max_depth=3)

    # Record evaluation time
    start_time = time.time()

    # We use 100 matches instead of 1000 because tree search evaluates in real-time
    expecti_winrate = evaluate_agent(expecti_agent, eval_env, num_matches=100)

    expecti_eval_time = time.time() - start_time
    expecti_time_per_match = (expecti_eval_time / 100) * 1000 # in ms

    # ---------------------------------------------------------
    # APPROACH 2: VALUE ITERATION (Markov Decision Process)
    # ---------------------------------------------------------
    print("\n" + "="*40)
    print("APPROACH 2: VALUE ITERATION (MDP)")
    print("="*40)

    # Record resolution time
    start_time = time.time()

    mdp_agent = setup_mdp_agent(ai_type=selected_ai_type, bot_type=selected_bot_type)

    mdp_prep_time = time.time() - start_time
    

    # Record evaluation time
    start_time = time.time()

    mdp_winrate = evaluate_agent(mdp_agent, eval_env, num_matches=1000)

    mdp_eval_time = time.time() - start_time
    mdp_time_per_match = (mdp_eval_time / 1000) * 1000  #in ms

    # ---------------------------------------------------------
    # APPROACH 3: Q-LEARNING (Reinforcement Learning)
    # ---------------------------------------------------------
    print("\n" + "="*40)
    print("APPROACH 3: Q-LEARNING")
    print("="*40)

    # Record training time
    start_time = time.time()

    rl_agent = train_rl_agent(ai_type=selected_ai_type, bot_type=selected_bot_type, episodes=5000)

    rl_prep_time = time.time() - start_time

    # Record evaluation time
    start_time = time.time()

    rl_winrate = evaluate_agent(rl_agent, eval_env, num_matches=1000)

    rl_eval_time = time.time() - start_time
    rl_time_per_match = (rl_eval_time / 1000) * 1000 # in ms

    # ---------------------------------------------------------
    # FINAL DASHBOARD
    # ---------------------------------------------------------
    print("\n" + "!"*50)
    print(f"FINAL RESULTS: AI ({selected_ai_type}) vs BOT ({selected_bot_type})")
    print("!"*50)
    
    print("\n--- 1. EXPECTIMINIMAX ---")
    print(f"Winrate          : {expecti_winrate}%")
    print(f"Preparation Time : 0.00 seconds (No training needed)")
    print(f"Avg Time/Match   : {expecti_time_per_match:.2f} ms")

    print("\n--- 2. MARKOV DECISION PROCESS (VALUE ITERATION) ---")
    print(f"Winrate          : {mdp_winrate}%")
    print(f"Preparation Time : {mdp_prep_time:.2f} seconds (Solving MDP)")
    print(f"Avg Time/Match   : {mdp_time_per_match:.2f} ms")

    print("\n--- 3. Q-LEARNING ---")
    print(f"Winrate          : {rl_winrate}%")
    print(f"Preparation Time : {rl_prep_time:.2f} seconds (5000 episodes)")
    print(f"Avg Time/Match   : {rl_time_per_match:.2f} ms")
    print("!"*50)
    