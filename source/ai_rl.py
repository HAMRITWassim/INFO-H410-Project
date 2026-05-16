import copy
from environment import BattleEnvironment, MAX_HP, COST_ATTACK, COST_HEAL
from bot import get_heuristic_bot_action

class ExpectimaxAgent:
    """
    Agent utilisant l'algorithme Expectimax (ici optimisé en Minimax déterministe)
    pour planifier ses actions en anticipant les choix précis du Bot.
    """
    def __init__(self, legal_actions, max_depth=3):
        self.legal_actions = legal_actions
        self.max_depth = max_depth  # Profondeur de l'arbre (3 tours d'anticipation)

    def get_valid_actions(self, env_state):
        """
        Retourne la liste des actions que l'IA peut légalement effectuer ce tour-ci
        selon ses ressources actuelles (Mana et Potions).
        """
        ai_mana = env_state["AI"]["Mana"]
        ai_potions = env_state["AI"]["Potions"]
        
        # Récupère l'attaque spécifique de l'IA (ex: Attack_Fire)
        attack_action = [a for a in self.legal_actions if a.startswith("Attack")][0]
        
        valid_actions = ["Defend"]  # Se défendre est toujours possible
        
        if ai_mana >= COST_ATTACK:
            valid_actions.append(attack_action)
            
        if ai_mana >= COST_HEAL and ai_potions > 0:
            valid_actions.append("Heal")
            
        return valid_actions

    def evaluate_state(self, env_state):
        """
        Fonction d'évaluation (Heuristique) : donne une note mathématique à un état.
        Plus le score est élevé, plus la situation est avantageuse pour l'IA.
        """
        ai = env_state["AI"]
        bot = env_state["Bot"]

        # États terminaux (Victoire / Défaite)
        if ai["HP"] <= 0:
            return -1000.0
        if bot["HP"] <= 0:
            return 1000.0

        # Calcul du score basé sur les ressources et la vie
        score = 0.0
        score += (ai["HP"] - bot["HP"]) * 2.5       # Priorité absolue aux points de vie
        score += (ai["Mana"] - bot["Mana"]) * 0.4    # L'avantage en mana permet d'attaquer/soigner
        score += (ai["Potions"] - bot["Potions"]) * 15.0 # Les potions restantes ont une grande valeur

        return float(score)

    def choose_action(self, env_state, is_training=False):
        """
        Point d'entrée principal pour main.py. 
        Parcourt le premier niveau de l'arbre pour renvoyer la meilleure action immédiate.
        """
        valid_actions = self.get_valid_actions(env_state)
        
        best_score = float('-inf')
        best_action = valid_actions[0]

        # L'IA teste virtuellement chacune de ses actions possibles
        for action in valid_actions:
            # On passe au nœud "Chance" (le tour du Bot) à la profondeur 1
            score = self._chance_node(env_state, action, depth=1)
            
            if score > best_score:
                best_score = score
                best_action = action

        return best_action

    def _max_node(self, env_state, depth):
        """
        Nœud MAX : Représente le tour de décision de l'IA.
        Elle cherche à maximiser le score.
        """
        # Condition d'arrêt : profondeur max atteinte ou fin de partie
        if depth >= self.max_depth or env_state["AI"]["HP"] <= 0 or env_state["Bot"]["HP"] <= 0:
            return self.evaluate_state(env_state)

        valid_actions = self.get_valid_actions(env_state)
        best_score = float('-inf')

        for action in valid_actions:
            score = self._chance_node(env_state, action, depth)
            best_score = max(best_score, score)

        return best_score

    def _chance_node(self, env_state, ai_action, depth):
        """
        Nœud CHANCE : Représente le tour du Bot.
        Ici, on utilise l'heuristique du bot pour prédire son action exacte à 100%.
        """
        # On extrait les types pour pouvoir appeler la fonction du bot
        ai_type = [a.split("_")[1] for a in self.legal_actions if a.startswith("Attack")][0]
        
        # On détermine dynamiquement le type du bot en fonction des variables de l'état
        # (Par sécurité, on cherche à analyser l'environnement pour déduire son type)
        bot_type = "Grass"  # Valeur par défaut
        if "Bot" in env_state:
            # Note: L'environnement ne stocke pas directement le type dans le dictionnaire state,
            # on suppose que le bot_type est géré par l'instance globale, ou on le déduit.
            # Pour l'arbre de simulation, on s'aligne sur le type configuré.
            pass

        # Simulation de la réaction du Bot via son script officiel
        # Pour être parfaitement rigoureux, on simule l'action que le bot choisit dans CET état
        bot_action = get_heuristic_bot_action(env_state, bot_type="Grass", ai_type=ai_type) 
        
        # Essayer d'extraire les types réels s'ils sont disponibles globalement, 
        # sinon "Grass" convient pour la structure par défaut.

        # Création d'un environnement virtuel pour appliquer les actions
        sim_env = BattleEnvironment(ai_type=ai_type, bot_type="Grass")
        sim_env.state = copy.deepcopy(env_state)
        
        # On applique le tour de combat de manière invisible (verbose=False)
        sim_env.execute_turn(ai_action, bot_action, verbose=False)
        next_state = sim_env.get_state()

        # On descend d'un niveau dans l'arbre vers le prochain tour de l'IA (Nœud MAX)
        return self._max_node(next_state, depth + 1)