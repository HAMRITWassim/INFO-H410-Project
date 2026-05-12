import random

# GAME CONSTANTS
TYPES = ["Fire", "Water", "Grass"]
ACTIONS = ["Attack_Fire", "Attack_Water", "Attack_Grass", "Heal", "Defend"]

MAX_HP = 100
MAX_MANA = 50

# Costs and effects
COST_ATTACK = 10
COST_HEAL = 20
REGEN_DEFEND = 15
HEAL_AMOUNT = 35
BASE_DAMAGE = 20

# Probabilities
PROBA_MISS = 0.10      # 10% chance to miss
PROBA_CRIT = 0.15      # 15% chance for a critical hit
CRIT_MULTIPLIER = 1.5
DEFEND_MULTIPLIER = 0.5 # Damage taken is halved when defending

# Type advantage chart (Attacker -> Defender)
TYPE_CHART = {
    "Fire": {"Grass": 2.0, "Water": 0.5, "Fire": 1.0},
    "Water": {"Fire": 2.0, "Grass": 0.5, "Water": 1.0},
    "Grass": {"Water": 2.0, "Fire": 0.5, "Grass": 1.0}
}

class BattleEnvironment:
    """
    Simulates the turn-based battle environment between the AI and the Bot
    """
    def __init__(self, ai_type="Fire", bot_type="Grass"):
        self.ai_type = ai_type
        self.bot_type = bot_type
        self.reset()



    def reset(self):
        """Resets the environment for a new battle"""
        self.state = {
            "AI": {"HP": MAX_HP, "Mana": MAX_MANA, "is_defending": False},
            "Bot": {"HP": MAX_HP, "Mana": MAX_MANA, "is_defending": False}
        }
        return self.get_state()



    def get_state(self):
        """Returns the current state of the battle"""
        return self.state



    def is_game_over(self):
        """Checks if the battle is over (one of the players has 0 HP)"""
        return self.state["AI"]["HP"] <= 0 or self.state["Bot"]["HP"] <= 0



    def get_winner(self):
        """Returns the winner of the battle"""
        if self.state["AI"]["HP"] <= 0 and self.state["Bot"]["HP"] > 0:
            return "Bot"
        
        elif self.state["Bot"]["HP"] <= 0 and self.state["AI"]["HP"] > 0:
            return "AI"
        
        else:
            return "Draw"



    def execute_turn(self, action_ai, action_bot):
        """Executes the actions for both players in a single turn"""

        # Reset defending stance at the beginning of the turn
        self.state["AI"]["is_defending"] = False
        self.state["Bot"]["is_defending"] = False

        # Phase 1: Priority moves (Defend and Heal happen before attacks)
        self.process_action("AI", "Bot", action_ai, is_priority_phase=True)
        self.process_action("Bot", "AI", action_bot, is_priority_phase=True)

        # Phase 2: Attack moves
        self.process_action("AI", "Bot", action_ai, is_priority_phase=False)
        self.process_action("Bot", "AI", action_bot, is_priority_phase=False)



    def process_action(self, attacker, defender, action, is_priority_phase):
        """Processes a single action based on the current phase."""
        if self.state[attacker]["HP"] <= 0:
            return # A defeated player cannot act
        

        # PRIORITY PHASE (Defend and Heal)
        if is_priority_phase:
            if action == "Defend":
                self.state[attacker]["is_defending"] = True
                self.state[attacker]["Mana"] = min(MAX_MANA, self.state[attacker]["Mana"] + REGEN_DEFEND)

                print(f"[{attacker}] Defend (+{REGEN_DEFEND} Mana)")
                
            elif action == "Heal":
                if self.state[attacker]["Mana"] >= COST_HEAL:
                    self.state[attacker]["HP"] = min(MAX_HP, self.state[attacker]["HP"] + HEAL_AMOUNT)
                    self.state[attacker]["Mana"] -= COST_HEAL

                    print(f"[{attacker}] Heal (+{HEAL_AMOUNT} HP, -{COST_HEAL} Mana)")

                else:
                    print(f"[{attacker}] Heal (FAILED: NOT ENOUGH MANA)")

            return

        # ATTACK PHASE
        if action.startswith("Attack"):
            
            if self.state[attacker]["Mana"] < COST_ATTACK:
                print(f"[{attacker}] {action} (FAILED: NOT ENOUGH MANA)")
                return 
            
            self.state[attacker]["Mana"] -= COST_ATTACK

            # Attack misses
            if random.random() < PROBA_MISS:
                print(f"[{attacker}] {action} (-{COST_ATTACK} Mana) -> (MISSED)")
                return 

            # Calculate base damage
            attack_type = action.split("_")[1]
            damage = BASE_DAMAGE
            
            # Apply type advantage multiplier
            if defender == "Bot":
                defender_type = self.bot_type

            else:
                defender_type = self.ai_type

            damage *= TYPE_CHART[attack_type][defender_type]

            # Critical hit
            crit_tag = ""
            if random.random() < PROBA_CRIT:
                damage *= CRIT_MULTIPLIER
                crit_tag = " (CRITICAL HIT)"

            # Apply defense reduction if the defender is defending
            def_tag = ""
            if self.state[defender]["is_defending"]:
                damage *= DEFEND_MULTIPLIER
                def_tag = " (DEFENDED)"

            damage = int(damage)
            
            # Apply final damage to the defender
            self.state[defender]["HP"] = max(0, self.state[defender]["HP"] - damage)
            
            # Final clean log print
            print(f"[{attacker}] {action} (-{COST_ATTACK} Mana) -> [{defender}] loses {damage} HP{crit_tag}{def_tag}")