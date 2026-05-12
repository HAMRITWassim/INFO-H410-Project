from environment import BattleEnvironment, TYPES
from bot import get_heuristic_bot_action
import random

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
        
        # BOT CHOISE (using heuristics)
        action_bot = get_heuristic_bot_action(state, env.bot_type, env.ai_type)
        
        # AI CHOICE

        # TODO: ALGO IMPLEMENTATION

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

# Run the simulation
if __name__ == "__main__":
    play_test_match()