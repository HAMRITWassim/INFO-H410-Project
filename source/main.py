from environment import BattleEnvironment, TYPES
from bot import get_heuristic_bot_action
from ai_expectiminimax import ExpectiminimaxAgent
import random
import copy

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

"""
def train_rl_agent(ai_type, bot_type, episodes=5000):
"""

"""
    Phase 1: Training the agent 
""" 
"""
    print(f"--- STARTING TRAINING FOR {episodes} EPISODES ---")
    
    # Initialize Environment and Agent
    env = BattleEnvironment(ai_type=ai_type, bot_type=bot_type)
    
    # can only use its OWN TYPE attack, heal, or defend
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

    print("--- TRAINING COMPLETE ---")
    return agent
"""

def evaluate_rl_agent(agent, env, num_matches=1000):
    """
    Phase 2: Evaluating the trained agent over multiple matches;
    """
    print(f"\n--- EVALUATING AGENT OVER {num_matches} MATCHES ---")
    win_count = 0
    loss_count = 0
    draw_count = 0

    for i in range(num_matches):
        env.reset()
        turn_number = 1

        while not env.is_game_over():
            state = env.get_state()
            
            # No random action (Epsilon = 0)
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
    print(f"Trained AI Winrate: {win_rate:.1f}%")
    return win_rate

def test_rl_agent(agent, env):
    """
    Phase 3: Testing the trained agent
    """
    print("\n--- BATTLE START (TESTING MODE) ---")
    env.reset()
    turn_number = 1

    while not env.is_game_over():
        print(f"\n=== TURN {turn_number} ===")
        state = env.get_state()
        
        # No random action (Epsilon = 0)
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

def play_test_match():
    """
    Main game loop to simulate a battle
    """
    print("--- BATTLE START ---")
    
    # 1. Initialize the environment
    env = BattleEnvironment(ai_type="Water", bot_type="Grass")
    turn_number = 1

    # 2. The Game Loop
    # Runs as long as neither player's HP has reached 0
    while not env.is_game_over():
        print(f"\n\n=== TURN {turn_number} ===")
        
        # Get the current state to feed to the decision makers
        state = env.get_state()
        
        # Display stats so we can track the battle in the console
        print(f"AI  (Fire)  - HP: {state['AI']['HP']}, Mana: {state['AI']['Mana']}")
        print(f"Bot (Grass) - HP: {state['Bot']['HP']}, Mana: {state['Bot']['Mana']}\n")

        # --- DECISION PHASE ---
        
        # BOT CHOICE (using heuristics)
        action_bot = get_heuristic_bot_action(state, env.bot_type, env.ai_type)
        
        # AI CHOICE

        # TODO: ALGORITHM IMPLEMENTATION

        # For now, it plays randomly to test the loop.
        ai_attack = f"Attack_{env.ai_type}"
        possible_actions = [ai_attack, "Heal", "Defend"]
        action_ai = random.choice(possible_actions)


        # --- EXECUTION PHASE ---
        
        # Send both actions to the game engine to handle priorities and damage
        env.execute_turn(action_ai, action_bot)
        
        turn_number += 1

    # 3. End of the battle
    print("\n--- BATTLE END ---")
    winner = env.get_winner()
    print(f"The winner is: {winner}!")


def choose_type(player_name):
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

# Run the simulation
if __name__ == "__main__":
    # 0. Choose the types
    print("=== SETUP MATCH ===")
    selected_ai_type = choose_type("AI")
    selected_bot_type = choose_type("Bot")

    print(f"\n--- AI TYPE: {selected_ai_type} ---")
    print(f"--- BOT TYPE: {selected_bot_type} ---\n")

    # 1. Initialize ExpectiminimaxAgent (no training)
    trained_agent = ExpectiminimaxAgent(ai_type=selected_ai_type, bot_type=selected_bot_type, max_depth=3)
    
    # 2. Evaluate the Agent
    eval_env = BattleEnvironment(ai_type=selected_ai_type, bot_type=selected_bot_type)
    evaluate_rl_agent(trained_agent, eval_env, num_matches=100)

    # 3. Test the Agent 
    test_env = BattleEnvironment(ai_type=selected_ai_type, bot_type=selected_bot_type)
    test_rl_agent(trained_agent, test_env)