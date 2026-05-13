import random
from environment import *

def get_heuristic_bot_action(env_state, bot_type, ai_type):
    """
    Determines the bot's action based on a set of heuristic rules.
    The bot can ONLY use the attack matching its own type.
    """
    bot_hp = env_state["Bot"]["HP"]
    bot_mana = env_state["Bot"]["Mana"]
    bot_potions = env_state["Bot"]["Potions"]
    
    # The only attack available to the bot
    bot_attack = f"Attack_{bot_type}"

    # 1. Heal if HP is critically low, has Mana, AND has Potions
    if bot_hp <= (MAX_HP * 0.2) and bot_mana >= COST_HEAL and bot_potions > 0:
        return "Heal"

    # 2. Defend if not enough Mana to attack
    if bot_mana < COST_ATTACK:
        return "Defend"

    # 3. If its attack is super effective, prioritize it
    multiplier = TYPE_CHART[bot_type][ai_type]
    if multiplier == 1.2 and bot_mana >= COST_ATTACK:
        return bot_attack

    # 4. Default Behavior: Random valid action
    possible_actions = [bot_attack]
    if bot_mana >= COST_HEAL and bot_potions > 0:
        possible_actions.append("Heal")
    possible_actions.append("Defend")
    
    return random.choice(possible_actions)