import copy
from environment import BattleEnvironment, COST_ATTACK, COST_HEAL

class ExpectiminimaxAgent:
    """
    Expectiminimax Agent
    - MAX Node (AI): Maximizes the heuristic score
    - MIN Node (Bot): Minimizes the heuristic score (assumes the Bot plays perfectly)
    - CHANCE Node (Game Engine): Calculates the expected value of random events
    """
    def __init__(self, ai_type, bot_type, max_depth=2):
        self.ai_type = ai_type
        self.bot_type = bot_type
        self.max_depth = max_depth

    def get_valid_actions(self, env_state, player="AI"):
        """
        Returns legal actions based on the specified player's current resources
        """
        mana = env_state[player]["Mana"]
        potions = env_state[player]["Potions"]
        
        # Build attack string
        if player == "AI":
            attack_action = f"Attack_{self.ai_type}"
        else:
            attack_action = f"Attack_{self.bot_type}"
            
        valid_actions = ["Defend"]
        
        if mana >= COST_ATTACK:
            valid_actions.append(attack_action)
            
        if mana >= COST_HEAL and potions > 0:
            valid_actions.append("Heal")
            
        return valid_actions

    def evaluate_state(self, env_state):
        """
        Heuristic function: Evaluates how favorable the current state is for the AI
        Positive -> Good for AI 
        Negative -> Good for Bot
        """
        ai = env_state["AI"]
        bot = env_state["Bot"]

        # Terminal states (Infinite scores for absolute win/loss)
        if ai["HP"] <= 0:
            return -10000.0
        
        if bot["HP"] <= 0:
            return 10000.0

        # Score calculation based on HP, Mana & Potions
        score = 0.0
        score += (ai["HP"] - bot["HP"]) * 2.5       # Most important metric
        score += (ai["Mana"] - bot["Mana"]) * 0.4   
        score += (ai["Potions"] - bot["Potions"]) * 15.0  # Emphasis on potion value
        
        return float(score)

    def choose_action(self, env_state, is_training=False):
        """
        Starts the tree search and returns the best immediate action
        """
        valid_actions = self.get_valid_actions(env_state, "AI")
        
        best_score = float('-inf')
        best_action = valid_actions[0]

        for action in valid_actions:
            # Proceed to the MIN node (Bot's turn)
            score = self._min_node(env_state, action, depth=1)
            
            if score > best_score:
                best_score = score
                best_action = action

        return best_action

    def _max_node(self, env_state, depth):
        """
        MAX Node: AI's turn to choose the action that maximizes the score
        """
        # Stop condition: max depth reached or game over
        if depth >= self.max_depth or env_state["AI"]["HP"] <= 0 or env_state["Bot"]["HP"] <= 0:
            return self.evaluate_state(env_state)

        valid_actions = self.get_valid_actions(env_state, "AI")
        best_score = float('-inf')

        for action in valid_actions:
            # Move down the tree to the MIN node
            score = self._min_node(env_state, action, depth)
            best_score = max(best_score, score)

        return best_score

    def _min_node(self, env_state, ai_action, depth):
        """
        MIN Node: Bot's turn. 
        The AI assumes the bot is smart and will choose the worst possible outcome for the AI
        """
        bot_valid_actions = self.get_valid_actions(env_state, "Bot")
        
        worst_score_for_ai = float('inf')

        for bot_action in bot_valid_actions:
            # After the bot has chosen, proceed to the CHANCE node
            score = self._chance_node(env_state, ai_action, bot_action, depth)
            worst_score_for_ai = min(worst_score_for_ai, score)

        return worst_score_for_ai

    def _chance_node(self, env_state, ai_action, bot_action, depth):
        """
        CHANCE Node: Calculates the Expected Value of the AI's attack 
        using the "remote controls" (no randomness)
        """
        # No Randomness for Defend or Heal
        if not ai_action.startswith("Attack"):
            sim_env = BattleEnvironment(ai_type=self.ai_type, bot_type=self.bot_type)
            sim_env.state = copy.deepcopy(env_state)
            
            sim_env.execute_turn(ai_action, bot_action, verbose=False)
            return self._max_node(sim_env.get_state(), depth + 1)

        scenarios = [
            {"prob": 0.75, "force_hit": True, "force_crit": False},  # Normal hit (75%)
            {"prob": 0.15, "force_hit": True, "force_crit": True},   # Critical hit (15%)
            {"prob": 0.10, "force_hit": False, "force_crit": False}  # Miss (10%)
        ]

        expected_value = 0.0

        for scenario in scenarios:
            sim_env = BattleEnvironment(ai_type=self.ai_type, bot_type=self.bot_type)
            sim_env.state = copy.deepcopy(env_state)
            
            # We inject our forced probabilities
            sim_env.execute_turn(
                ai_action, 
                bot_action, 
                verbose=False, 
                force_ai_hit=scenario["force_hit"], 
                force_ai_crit=scenario["force_crit"]
            )
            
            score = self._max_node(sim_env.get_state(), depth + 1)
            expected_value += scenario["prob"] * score

        return expected_value