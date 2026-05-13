import random

class QLearningAgent:
    """
    Model-Free Reinforcement Learning Agent using Q-Learning
    """
    def __init__(self, legal_actions, alpha=0.1, gamma=0.9, epsilon=0.2):
        self.q_table = {}                # The "Brain" of the AI
        self.legal_actions = legal_actions
        
        # Hyperparameters
        self.alpha = alpha               # Learning Rate (how much new info overrides old)
        self.gamma = gamma               # Discount Factor (importance of future rewards)
        self.epsilon = epsilon           # Exploration Rate (chance to take a random action)

    # --- 1. STATE DISCRETIZATION ---
    
    def _discretize_hp(self, hp):
        """ Simplifying HP into 3 categories """
        if hp > 50:             
            return "High"       # [51 ; 100] -> HIGH
        
        elif hp > 20:           
            return "Medium"     # [21 ; 50] -> MEDIUM
        
        else:                   
            return "Low"        # [0 ; 20] -> LOW

    def _discretize_mana(self, mana):
        """ Simplifying Mana into 3 categories """
        if mana >= 20:
            return "High"       # Enough to Heal
        
        elif mana >= 10:
            return "Low"        # Enough to Attack
        
        else:
            return "Empty"      # No Mana

    def get_state_key(self, env_state):
        """
        Converts the complex environment state into a simple tuple string 
        that can be used as a key in our Q-Table dictionary.
        """
        ai = env_state["AI"]
        bot = env_state["Bot"]
        
        return (
            self._discretize_hp(ai["HP"]),
            self._discretize_mana(ai["Mana"]),
            ai["is_defending"],
            ai["Potions"],
            self._discretize_hp(bot["HP"]),
            self._discretize_mana(bot["Mana"]),
            bot["is_defending"],
            bot["Potions"]
        )

    # --- 2. DECISION MAKING ---

    def get_q_value(self, state_key, action):
        """Returns the Q-Value for a state-action pair, initializes it to 0.0 if unseen"""
        if state_key not in self.q_table:
            self.q_table[state_key] = {a: 0.0 for a in self.legal_actions}

        return self.q_table[state_key][action]
    
    def get_valid_actions(self, env_state):
        """
        Returns a list of actions the AI can currently afford to use.
        Prevents the AI from trying to attack without mana or heal without potions.
        """
        ai_mana = env_state["AI"]["Mana"]
        ai_potions = env_state["AI"]["Potions"]
        
        # Find the specific attack name (e.g., "Attack_Fire") from the legal actions list
        attack_action = [a for a in self.legal_actions if a.startswith("Attack")][0]
        
        valid_actions = ["Defend"] # Defending is always a valid option
        
        # Check if the AI has enough mana to attack
        if ai_mana >= 10: # COST_ATTACK is 10
            valid_actions.append(attack_action)
            
        # Check if the AI has enough mana AND potions to heal
        if ai_mana >= 20 and ai_potions > 0: # COST_HEAL is 20
            valid_actions.append("Heal")
            
        return valid_actions

    def choose_action(self, env_state, is_training=True):
        """
        Chooses an action based on the Epsilon-Greedy policy,
        but STRICTLY filters out invalid actions to avoid wasting turns.
        """
        state_key = self.get_state_key(env_state)
        valid_actions = self.get_valid_actions(env_state)
        
        # EXPLORATION: Take a random VALID action
        if is_training and random.random() < self.epsilon:
            return random.choice(valid_actions)
        
        # EXPLOITATION: Take the best known VALID action
        if state_key not in self.q_table:
            self.q_table[state_key] = {a: 0.0 for a in self.legal_actions}
            
        # Filter the Q-Table to only look at the scores of valid actions for this turn
        valid_q_values = {action: self.q_table[state_key][action] for action in valid_actions}
        
        best_action = max(valid_q_values, key=valid_q_values.get)
        return best_action

    # --- 3. LEARNING (BELLMAN EQUATION) ---

    def learn(self, old_env_state, action, reward, new_env_state):
        """
        Updates the Q-Table using the Bellman Equation.
        """
        old_state_key = self.get_state_key(old_env_state)
        new_state_key = self.get_state_key(new_env_state)
        
        # Current Q-Value
        old_q = self.get_q_value(old_state_key, action)
        
        # Maximum expected future reward from the new state
        if new_state_key not in self.q_table:
            self.q_table[new_state_key] = {a: 0.0 for a in self.legal_actions}

        max_next_q = max(self.q_table[new_state_key].values())
        
        # The Bellman Equation
        new_q = old_q + self.alpha * (reward + self.gamma * max_next_q - old_q)
        
        # Update the Q-Table
        self.q_table[old_state_key][action] = new_q


    