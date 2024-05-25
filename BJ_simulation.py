import random
from abc import ABC, abstractmethod
import pandas as pd
import matplotlib.pyplot as plt

class CardCountingStrategy(ABC):
    def __init__(self):
        self.running_count = 0

    @abstractmethod
    def update_count(self, hand):
        pass

    @abstractmethod
    def calculate_bet(self, base_bet, nb_deck, cards_dealt):
        pass

class HiLowStrategy(CardCountingStrategy):
    def update_count(self, hand):
        for rank in hand:
            if rank in ['2', '3', '4', '5', '6']:
                self.running_count += 1
            elif rank in ['10', 'jack', 'queen', 'king', 'ace']:
                self.running_count -= 1

    def calculate_bet(self, base_bet, nb_deck, cards_dealt):
        decks_remaining = max(((nb_deck * 52) - cards_dealt) / 52, 1e-6)
        true_count = self.running_count / decks_remaining
        if true_count <= 1:
            return int(base_bet)
        elif true_count < 3:
            return int(base_bet * 2)
        else:
            return int(base_bet * 4)

class KOStrategy(CardCountingStrategy):
    def update_count(self, hand):
        for rank in hand:
            if rank in ['2', '3', '4', '5', '6', '7']:
                self.running_count += 1
            elif rank in ['10', 'jack', 'queen', 'king', 'ace']:
                self.running_count -= 1

    def calculate_bet(self, base_bet, nb_deck, cards_dealt):
        if self.running_count <= 1:
            return int(base_bet)
        elif self.running_count < 3:
            return int(base_bet * 2)
        else:
            return int(base_bet * 4)

class FiveCountStrategy(CardCountingStrategy):
    def __init__(self, nb_deck):
        super().__init__()
        self.total_fives = nb_deck * 4
        self.seen_fives = 0
        self.total_cards = nb_deck * 52
        self.cards_dealt = 0

    def update_count(self, hand):
        for rank in hand:
            if rank == '5':
                self.seen_fives += 1
            self.cards_dealt += 1

    def calculate_bet(self, base_bet, nb_deck, cards_dealt):
        unseen_fives = self.total_fives - self.seen_fives
        unseen_cards = self.total_cards - self.cards_dealt

        if unseen_fives == 0:
            return int(base_bet)

        count_ratio = unseen_cards / unseen_fives

        if count_ratio > 14:
            return int(base_bet * 4)
        elif count_ratio < 12:
            return int(base_bet * 0.5)
        else:
            return int(base_bet)

    def reset(self):
        self.seen_fives = 0
        self.cards_dealt = 0

class BlackjackSimulator:
    def __init__(self, nb_decks=1, base_bet=8, initial_balance=1000, num_players=1, tracked_player_position=0, seed=None):
        self.nb_decks = nb_decks
        self.base_bet = base_bet
        self.initial_balance = initial_balance
        self.num_players = num_players
        self.tracked_player_position = tracked_player_position
        self.seed = seed
        if seed is not None:
            random.seed(seed)
        self.deck = self.create_deck()
        self.strategy = None
        self.hands = []
        self.cards_dealt = 0
        self.reshuffle_threshold = random.randint(int(0.6 * len(self.deck)), int(0.9 * len(self.deck)))

    def create_deck(self):
        deck = []
        for _ in range(self.nb_decks):
            for suit in ['clubs', 'diamonds', 'hearts', 'spades']:
                for rank in ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'jack', 'queen', 'king', 'ace']:
                    deck.append(rank)
        random.shuffle(deck)
        return deck

    def reshuffle_cards(self):
        self.deck = self.create_deck()
        self.cards_dealt = 0
        if self.strategy:
            if isinstance(self.strategy, FiveCountStrategy):
                self.strategy.reset()
            else:
                self.strategy.running_count = 0

    def deal_card(self):
        if len(self.deck) == 0 or self.cards_dealt >= self.reshuffle_threshold:
            self.reshuffle_cards()
        self.cards_dealt += 1
        return self.deck.pop()

    def play_hand(self, strategy, bet, use_basic_strategy=False):
        if self.num_players == 1:
            player_hand = [self.deal_card(), self.deal_card()]
            dealer_hand = [self.deal_card(), self.deal_card()]
            self.hands = [player_hand, dealer_hand]
            double_down = False
            split_hands = []
            split_bets = []

            # Check for blackjack
            if self.calculate_hand_value(player_hand) == 21:
                if self.calculate_hand_value(dealer_hand) == 21:
                    return 0  # Tie
                else:
                    return 1.5 * bet  # Player wins with blackjack

            while True:
                if use_basic_strategy:
                    action = self.basic_strategy(player_hand, dealer_hand)
                else:
                    action = 'hit' if self.calculate_hand_value(player_hand) < 17 else 'stand'

                if action == 'hit':
                    player_hand.append(self.deal_card())
                    if self.calculate_hand_value(player_hand) >= 21:
                        break
                elif action == 'double':
                    double_down = True
                    player_hand.append(self.deal_card())
                    bet *= 2
                    break
                elif action == 'split':
                    split_hands.append([player_hand[0], self.deal_card()])
                    split_hands.append([player_hand[1], self.deal_card()])
                    split_bets.append(bet)
                    split_bets.append(bet)
                    bet *= 2
                    break
                else:
                    break

            while self.calculate_hand_value(dealer_hand) < 17:
                dealer_hand.append(self.deal_card())

            player_total = self.calculate_hand_value(player_hand)
            dealer_total = self.calculate_hand_value(dealer_hand)

            if strategy:
                strategy.update_count(player_hand)
                strategy.update_count(dealer_hand)

            if split_hands:
                results = []
                for i, hand in enumerate(split_hands):
                    hand_total = self.calculate_hand_value(hand)
                    if hand_total > 21:
                        results.append(-split_bets[i])
                    elif dealer_total > 21 or hand_total > dealer_total:
                        results.append(split_bets[i])
                    elif hand_total < dealer_total:
                        results.append(-split_bets[i])
                    else:
                        results.append(0)
                return sum(results)

            if player_total > 21:
                return -bet
            elif dealer_total > 21 or player_total > dealer_total:
                return bet if not double_down else 2 * bet
            elif player_total < dealer_total:
                return -bet if not double_down else -2 * bet
            else:
                return 0
        else:
            players_hands = [[self.deal_card(), self.deal_card()] for _ in range(self.num_players)]
            dealer_hand = [self.deal_card(), self.deal_card()]

            self.hands = players_hands + [dealer_hand]
            double_down = False
            split_hands = []
            split_bets = []

            for i, player_hand in enumerate(players_hands):
                if self.calculate_hand_value(player_hand) == 21:
                    continue
                while True:
                    if use_basic_strategy and i == self.tracked_player_position:
                        action = self.basic_strategy(player_hand, dealer_hand)
                    else:
                        action = 'hit' if self.calculate_hand_value(player_hand) < 17 else 'stand'

                    if action == 'hit':
                        player_hand.append(self.deal_card())
                        if self.calculate_hand_value(player_hand) >= 21:
                            break
                    elif action == 'double' and i == self.tracked_player_position:
                        double_down = True
                        player_hand.append(self.deal_card())
                        bet *= 2
                        break
                    elif action == 'split' and i == self.tracked_player_position:
                        split_hands.append([player_hand[0], self.deal_card()])
                        split_hands.append([player_hand[1], self.deal_card()])
                        split_bets.append(bet)
                        split_bets.append(bet)
                        bet *= 2
                        break
                    else:
                        break

            while self.calculate_hand_value(dealer_hand) < 17:
                dealer_hand.append(self.deal_card())

            tracked_hand = players_hands[self.tracked_player_position]
            player_total = self.calculate_hand_value(tracked_hand)
            dealer_total = self.calculate_hand_value(dealer_hand)

            if strategy:
                strategy.update_count(tracked_hand)
                strategy.update_count(dealer_hand)

            if split_hands:
                results = []
                for i, hand in enumerate(split_hands):
                    hand_total = self.calculate_hand_value(hand)
                    if hand_total > 21:
                        results.append(-split_bets[i])
                    elif dealer_total > 21 or hand_total > dealer_total:
                        results.append(split_bets[i])
                    elif hand_total < dealer_total:
                        results.append(-split_bets[i])
                    else:
                        results.append(0)
                return sum(results)

            if player_total > 21:
                return -bet
            elif dealer_total > 21 or player_total > dealer_total:
                return bet if not double_down else 2 * bet
            elif player_total < dealer_total:
                return -bet if not double_down else -2 * bet
            else:
                return 0

    def calculate_hand_value(self, hand):
        values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
                  'jack': 10, 'queen': 10, 'king': 10, 'ace': 11}
        result = 0
        aces = 0
        for rank in hand:
            if rank == 'ace':
                aces += 1
            result += values[rank]
        while result > 21 and aces:
            result -= 10
            aces -= 1
        return result

    def basic_strategy(self, player_hand, dealer_hand):
        player_total = self.calculate_hand_value(player_hand)
        dealer_card_rank = dealer_hand[0]
        dealer_value = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'jack': 10, 'queen': 10, 'king': 10, 'ace': 11}[dealer_card_rank]

        soft = 'ace' in player_hand and player_total <= 21
        pair = len(player_hand) == 2 and player_hand[0] == player_hand[1]
        can_double = len(player_hand) == 2

        if player_total < 8:
            action = 'hit'
        elif player_total == 8:
            if dealer_value in [2, 3, 4, 7, 8, 9, 10, 11]:
                action = 'hit'
            else:
                action = 'double'
        elif player_total == 9:
            if dealer_value in [7, 8, 9, 10, 11]:
                action = 'hit'
            elif can_double:
                action = 'double'
            else:
                action = 'hit'
        elif player_total == 10:
            if dealer_value in [10, 11] or not can_double:
                action = 'hit'
            else:
                action = 'double'
        elif player_total == 11:
            if can_double:
                action = 'double'
            else:
                action = 'hit'
        elif player_total == 12:
            if dealer_value in [2, 3, 7, 8, 9, 10, 11]:
                action = 'hit'
            else:
                action = 'stand'
        elif player_total in [13, 14, 15, 16]:
            if dealer_value in [2, 3, 4, 5, 6]:
                action = 'stand'
            else:
                action = 'hit'
        elif player_total >= 17:
            action = 'stand'
        elif soft:
            if player_total in [13, 14, 15, 16] and can_double:
                if dealer_value in [4, 5, 6]:
                    action = 'double'
                else:
                    action = 'hit'
            elif player_total == 17:
                if dealer_value in [2, 3, 4, 5, 6] and can_double:
                    action = 'double'
                else:
                    action = 'hit'
            elif player_total == 18:
                if dealer_value in [3, 4, 5, 6] and can_double:
                    action = 'double'
                elif dealer_value in [2, 7, 8, 11]:
                    action = 'stand'
                else:
                    action = 'hit'
            elif player_total == 19:
                if dealer_value == 6 and can_double:
                    action = 'double'
                else:
                    action = 'stand'
            elif player_total == 20:
                action = 'stand'
        elif pair:
            if player_total == 4:
                if dealer_value in [3, 4, 5, 6, 7]:
                    action = 'split'
                else:
                    action = 'hit'
            elif player_total == 6:
                if dealer_value in [4, 5, 6, 7]:
                    action = 'split'
                else:
                    action = 'hit'
            elif player_total == 8:
                if dealer_value in [5, 6]:
                    action = 'double'
                else:
                    action = 'hit'
            elif player_total == 10:
                if dealer_value in [10, 11]:
                    action = 'hit'
                else:
                    action = 'double'
            elif player_total == 12:
                if dealer_value in [2, 3, 4, 5, 6]:
                    action = 'split'
                else:
                    action = 'hit'
            elif player_total == 14:
                if dealer_value in [8, 9, 11]:
                    action = 'hit'
                elif dealer_value == 10:
                    action = 'stand'
                else:
                    action = 'split'
            elif player_total == 18:
                if dealer_value in [7, 10, 11]:
                    action = 'stand'
                else:
                    action = 'split'
            elif player_total == 20:
                action = 'stand'
            elif player_total == 16 or player_hand.count('ace') == 2:
                action = 'split'

        return action

    def run_simulation(self, strategy_class, num_hands=1000, use_basic_strategy=False):
        balance = self.initial_balance
        if strategy_class:
            if strategy_class == FiveCountStrategy:
                self.strategy = FiveCountStrategy(self.nb_decks)
            else:
                self.strategy = strategy_class()
        else:
            self.strategy = None
        self.cards_dealt = 0
        for hand_number in range(num_hands):
            if balance <= 0:
                break
            bet = self.base_bet if not self.strategy else self.strategy.calculate_bet(self.base_bet, self.nb_decks, self.cards_dealt)
            result = self.play_hand(self.strategy, bet, use_basic_strategy)
            balance += result
            if self.cards_dealt >= self.reshuffle_threshold:
                self.reshuffle_cards()

        return balance

    def run_multiple_simulations(self, strategy_class, num_simulations=1000, num_hands=1000, use_basic_strategy=False):
        final_balances = []
        for simulation_number in range(num_simulations):
            final_balance = self.run_simulation(strategy_class, num_hands, use_basic_strategy)
            final_balances.append(max(final_balance, 0))
            if self.strategy:
                self.strategy.running_count = 0
        return sum(final_balances) / len(final_balances)


if __name__ == "__main__":
    deck_counts = [1, 3, 5, 8]
    player_positions = [0, 2, 4, 6]  # 1st, 3rd, 7th player
    num_simulations = 1000
    num_hands = 1000
    seed = 42

    strategies = [
        (None, "Play like dealer, same bet"),
        (None, "Basic Strategy, same bet"),
        (HiLowStrategy, "HiLow + Basic Strategy"),
        (KOStrategy, "KO + Basic Strategy"),
        (FiveCountStrategy, "Five Count + Basic Strategy")
    ]

    results = []

    # Single player against dealer
    for nb_decks in deck_counts:
        print(f"Results for {nb_decks} deck(s) of cards, single player against dealer:")
        simulator = BlackjackSimulator(nb_decks=nb_decks, base_bet=8, initial_balance=1000, num_players=1, tracked_player_position=0, seed = seed)

        for strategy, name in strategies:
            use_basic_strategy = "Basic Strategy" in name
            avg_final_balance = simulator.run_multiple_simulations(strategy, num_simulations=num_simulations, num_hands=num_hands, use_basic_strategy=use_basic_strategy)
            results.append([nb_decks, 'Single Player', name, avg_final_balance])
            print(f"Average final balance for {name}: ${avg_final_balance:.2f}")


    # Multiple players at the table
    for nb_decks in deck_counts:
        for position in player_positions:
            print(f"Results for {nb_decks} deck(s) of cards, player at position {position + 1}:")
            simulator = BlackjackSimulator(nb_decks=nb_decks, base_bet=8, initial_balance=1000, num_players=7, tracked_player_position=position, seed = seed)

            for strategy, name in strategies:
                use_basic_strategy = "Basic Strategy" in name
                avg_final_balance = simulator.run_multiple_simulations(strategy, num_simulations=num_simulations, num_hands=num_hands, use_basic_strategy=use_basic_strategy)
                results.append([nb_decks, f'Position {position + 1}', name, avg_final_balance])
                print(f"Average final balance for {name}: ${avg_final_balance:.2f}")

    results_df = pd.DataFrame(results, columns=['Decks', 'Player Position', 'Strategy', 'Average Final Balance'])
    print(results_df)

    # Save the results table to a CSV file
    results_df.to_csv('results_table.csv', index=False)

    # Graph for single player against dealer
    plt.figure(figsize=(14, 7))
    for strategy, name in strategies:
        subset = results_df[(results_df['Strategy'] == name) & (results_df['Player Position'] == 'Single Player')]
        plt.plot(subset['Decks'], subset['Average Final Balance'], marker='o', label=name)
    plt.title('Average Final Balance for Single Player vs Dealer')
    plt.xlabel('Number of Decks')
    plt.ylabel('Average Final Balance')
    plt.legend()
    plt.grid(True)
    # Save the figure
    plt.savefig('single_player_vs_dealer.png')
    plt.show()

    # Graph for multiple players at the table
    for position in player_positions:
        plt.figure(figsize=(14, 7))
        for strategy, name in strategies:
            subset = results_df[(results_df['Strategy'] == name) & (results_df['Player Position'] == f'Position {position + 1}')]
            plt.plot(subset['Decks'], subset['Average Final Balance'], marker='o', label=name)
        plt.title(f'Average Final Balance for Player at Position {position + 1}')
        plt.xlabel('Number of Decks')
        plt.ylabel('Average Final Balance')
        plt.legend()
        plt.grid(True)
        # Save the figure with position number in the filename
        plt.savefig(f'player_position_{position + 1}.png')
        plt.show()

