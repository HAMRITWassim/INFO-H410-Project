import random
from environment import TYPE_CHART, BASE_DAMAGE

class ValueIterationAgent:
    """
    Model-Based Agent that solves the MDP using Value Iteration.
    It computes the optimal policy by anticipating all possible outcomes.
    """
    def __init__(self, ai_type, bot_type, legal_actions, gamma=0.9, theta=0.001):
        self.ai_type = ai_type
        self.bot_type = bot_type
        self.damage_multiplier = TYPE_CHART[self.ai_type][self.bot_type]
        self.legal_actions = legal_actions
        self.gamma = gamma    # Discount factor: importance of future rewards
        self.theta = theta    # Convergence threshold

        self.values = {}      # V(s): The expected utility of each state
        self.policy = {}      # pi(s): The best action for each state


    def _get_state_key(self, env_state):
        """
        The real game state is too precise (HP between 0-100, etc.).
        We cannot have a table for every possible value (state explosion).
        Therefore, we DISCRETIZE: grouping values into categories.

        HP  : High (>50), Med (20-50), Low (<=20)
        Mana: High (>=20 -> can Attack AND Heal)
              Low  (>=10 -> can only Attack)
              Empty (< 10 -> cannot perform special actions)

        It is crucial that these thresholds match the costs in 
        environment.py (COST_ATTACK=10, COST_HEAL=20), otherwise
        the agent might attempt actions it cannot afford!
        """
        def discretize_hp(hp):
            if hp > 50: return "High"
            elif hp > 20: return "Med"
            else: return "Low"

        def discretize_mana(mana):
            if mana >= 20: return "High"   # can attack AND heal
            elif mana >= 10: return "Low"  # can only attack
            else: return "Empty"           # cannot attack

        ai = env_state["AI"]
        bot = env_state["Bot"]
        return (
            discretize_hp(ai["HP"]),
            discretize_mana(ai["Mana"]),
            min(ai["Potions"], 3),          # number of potions (0 to 3) 
            discretize_hp(bot["HP"]),
            discretize_mana(bot["Mana"]),
        )

    def _get_valid_actions(self, state):
        """
        Check which actions are TRULY feasible in this state.
        This fixes a bug in earlier versions where the MDP proposed 
        actions the AI could not afford in mana, leading to 
        "FAILED: NOT ENOUGH MANA" wasted turns.

        Defend is always possible.
        Attack requires mana >= 10 (COST_ATTACK).
        Heal requires mana >= 20 (COST_HEAL) AND at least one potion.
        """
        ai_hp, ai_mana, ai_pots, bot_hp, bot_mana = state

        valid = ["Defend"]  # defend is always possible

        # Attack costs 10 mana
        if ai_mana in ("Low", "High"):
            attack_action = [a for a in self.legal_actions if a.startswith("Attack")][0]
            valid.append(attack_action)

        # Heal costs 20 mana and needs a potion
        if ai_mana == "High" and ai_pots > 0:
            valid.append("Heal")

        return valid

    def _get_transitions(self, state, action):
        """
        This is the heart of the MDP: modeling what can happen 
        when taking an action in a given state.

        Each transition returns (next_state, probability, reward).
        The sum of probabilities must equal 1.0 for each action.
        """
        ai_hp, ai_mana, ai_pots, bot_hp, bot_mana = state

        # ---- helpers ----
        def hp_after_damage(hp_level, damage_level):
            hp_map = {"High": 75, "Med": 35, "Low": 10}
            
            # base damage * type multiplier * precision
            base_expected = BASE_DAMAGE * self.damage_multiplier * 0.9
            
            if damage_level == "Normal":
                actual_damage = base_expected

            else: # Crit
                actual_damage = base_expected * 1.5 # CRIT_MULTIPLIER

            new_hp = hp_map[hp_level] - actual_damage
            
            if new_hp > 50: return "High"
            elif new_hp > 20: return "Med"
            elif new_hp > 0: return "Low"
            else: return "Dead"

        def mana_after_attack(mana_level):
            mana_map = {"High": 35, "Low": 15, "Empty": 0}
            new_mana = mana_map[mana_level] - 10  # COST_ATTACK = 10
            if new_mana >= 20: return "High"
            elif new_mana >= 10: return "Low"
            else: return "Empty"

        def mana_after_defend(mana_level):
            mana_map = {"High": 35, "Low": 15, "Empty": 0}
            new_mana = min(50, mana_map[mana_level] + 15)  # REGEN_DEFEND = 15
            if new_mana >= 20: return "High"
            elif new_mana >= 10: return "Low"
            else: return "Empty"

        def bot_attacks_back(ai_hp, bot_mana):
            # Estimate damage the bot inflicts this turn
            if bot_mana == "Empty":
                return ai_hp  # bot defends, no damage
            # bot attacks (assume neutral type for simplicity)
            # expected damage ~18 (BASE_DAMAGE * 0.9 miss factor)
            hp_map = {"High": 75, "Med": 35, "Low": 10}
            new_hp = hp_map[ai_hp] - 18
            if new_hp > 50: return "High"
            elif new_hp > 20: return "Med"
            elif new_hp > 0: return "Low"
            else: return "Dead" # ai is dead 

        outcomes = []

        
        if action.startswith("Attack"):

            new_ai_mana = mana_after_attack(ai_mana)

            # --- MISS (10%) ---
            # AI wastes mana, bot still attacks back
            miss_ai_hp = bot_attacks_back(ai_hp, bot_mana)
            if miss_ai_hp == "Dead":
                outcomes.append((state, 0.10, -100.0))  # we die
            else:
                miss_state = (miss_ai_hp, new_ai_mana, ai_pots, bot_hp, bot_mana)
                outcomes.append((miss_state, 0.10, -10.0))

            # --- HIT NORMAL (75.5% = 0.9 * 0.85) ---
            new_bot_hp_normal = hp_after_damage(bot_hp, "Normal")
            if new_bot_hp_normal == "Dead" or (bot_hp == "Low"):
                # Killing blow
                outcomes.append((state, 0.765, 100.0))
            else:
                hit_ai_hp = bot_attacks_back(ai_hp, bot_mana)
                if hit_ai_hp == "Dead":
                    outcomes.append((state, 0.765, -100.0))
                else:
                    hit_state = (hit_ai_hp, new_ai_mana, ai_pots, new_bot_hp_normal, bot_mana)
                    reward = 15.0 + (20.0 if bot_hp == "Med" and new_bot_hp_normal == "Low" else 0)
                    outcomes.append((hit_state, 0.765, reward))

            # --- CRIT HIT (13.5% = 0.9 * 0.15) ---
            new_bot_hp_crit = hp_after_damage(bot_hp, "Crit")
            if new_bot_hp_crit == "Dead" or (bot_hp in ("Low", "Med")):
                outcomes.append((state, 0.135, 100.0))
            else:
                crit_ai_hp = bot_attacks_back(ai_hp, bot_mana)
                if crit_ai_hp == "Dead":
                    outcomes.append((state, 0.135, -100.0))
                else:
                    crit_state = (crit_ai_hp, new_ai_mana, ai_pots, new_bot_hp_crit, bot_mana)
                    outcomes.append((crit_state, 0.135, 25.0))

       
        elif action == "Heal":
            new_ai_mana = "Empty" if ai_mana == "High" else ai_mana  # -20 mana
            # mana after COST_HEAL=20: High(35)->Low, Low(15)->impossible (filtered)
            mana_map = {"High": 35, "Low": 15}
            raw = mana_map.get(ai_mana, 0) - 20
            if raw >= 20: new_ai_mana = "High"
            elif raw >= 10: new_ai_mana = "Low"
            else: new_ai_mana = "Empty"

            new_ai_pots = max(0, ai_pots - 1)

            # HP after heal: +35, capped at 100
            hp_map_val = {"High": 75, "Med": 35, "Low": 10}
            new_raw_hp = min(100, hp_map_val[ai_hp] + 35)
            if new_raw_hp > 50: healed_hp = "High"
            elif new_raw_hp > 20: healed_hp = "Med"
            else: healed_hp = "Low"

            # Bot still attacks during heal turn
            after_bot = bot_attacks_back(healed_hp, bot_mana)
            if after_bot == "Dead":
                outcomes.append((state, 1.0, -100.0))
            else:
                heal_state = (after_bot, new_ai_mana, new_ai_pots, bot_hp, bot_mana)
                # Reward: survival bonus proportional to how critical the situation was
                survival_reward = 30.0 if ai_hp == "Low" else 15.0 if ai_hp == "Med" else 5.0
                outcomes.append((heal_state, 1.0, survival_reward))

        else:  # Defend
            new_ai_mana = mana_after_defend(ai_mana)
            # Defending halves damage received (DEFEND_MULTIPLIER = 0.5)
            hp_map_val = {"High": 75, "Med": 35, "Low": 10}
            if bot_mana == "Empty":
                after_bot = ai_hp  # bot also defends/rests, no damage
            else:
                # around half damage
                new_raw = hp_map_val[ai_hp] - 9  # 18/2
                if new_raw > 50: after_bot = "High"
                elif new_raw > 20: after_bot = "Med"
                elif new_raw > 0: after_bot = "Low"
                else: after_bot = "Dead"

            if after_bot == "Dead":
                outcomes.append((state, 1.0, -100.0))
            else:
                defend_state = (after_bot, new_ai_mana, ai_pots, bot_hp, bot_mana)
                # Small reward for mana generation; penalise stalling
                outcomes.append((defend_state, 1.0, 3.0))

        return outcomes

    def solve_mdp(self, all_states):
        """
        The Value Iteration Algorithm. We start with V(s) = 0 for all states and we
        updates V(s) using the Bellman Equation until convergence.
        """

        # Initialization: all values start at 0
        for s in all_states:
            self.values[s] = 0.0

        # Main loop: repeat until convergence
        while True:
            delta = 0
            new_values = self.values.copy() # copy to avoid interference during the sweep

            for s in all_states:
                valid_actions = self._get_valid_actions(s)
                action_utilities = []

                for a in valid_actions:
                    # Bellman Equation for action a in state s
                    avg_utility = sum(
                        prob * (reward + self.gamma * self.values.get(next_s, 0.0))
                        for next_s, prob, reward in self._get_transitions(s, a)
                    )
                    action_utilities.append(avg_utility)

                # Store the value of the BEST action
                new_values[s] = max(action_utilities)
                # Track the largest change to determine convergence
                delta = max(delta, abs(new_values[s] - self.values[s]))


            # If no value changed by more than theta, it is stable
            self.values = new_values
            if delta < self.theta:
                break

        # Policy extraction
        # choose the best action for each state based on the calculated values.
        for s in all_states:
            valid_actions = self._get_valid_actions(s)
            best_action = None
            max_util = -float('inf')
            for a in valid_actions:
                util = sum(
                    prob * (reward + self.gamma * self.values.get(next_s, 0.0))
                    for next_s, prob, reward in self._get_transitions(s, a)
                )
                if util > max_util:
                    max_util = util
                    best_action = a
            self.policy[s] = best_action

    def choose_action(self, env_state, is_training=False):
        """
        Returns the optimal action from the pre-computed policy,
        falling back to a random VALID action if the state is unseen.
        """
        state_key = self._get_state_key(env_state)

        # Fallback: filter to valid actions based on real env state
        ai_mana = env_state["AI"]["Mana"]
        ai_pots = env_state["AI"]["Potions"]
        attack_action = [a for a in self.legal_actions if a.startswith("Attack")][0]
        valid = ["Defend"]
        if ai_mana >= 10: valid.append(attack_action)
        if ai_mana >= 20 and ai_pots > 0: valid.append("Heal")

        # if the policy action is invalid so it pick a random valid action
        action = self.policy.get(state_key)
        if action not in valid:
            action = random.choice(valid)
        return action