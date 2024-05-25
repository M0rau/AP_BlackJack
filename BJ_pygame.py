import pygame
import os
import sys
from abc import ABC, abstractmethod
import random
import matplotlib.pyplot as plt

# Initialize Pygame
pygame.init()
font = pygame.font.Font(None, 36)
screen_width = 1024  # Adjust width as needed
screen_height = 768  # Adjust height as needed
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Blackjack Game")

# Load card images and return a dictionary with card images

def load_card_images(cards_folder):
    card_images = {} 
    suits = ['clubs', 'diamonds', 'hearts', 'spades']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'jack', 'queen', 'king', 'ace']
    
    cards_folder = 'cards'
    cardback_image_path = os.path.join(cards_folder, "cardback1.png")
    if os.path.exists(cardback_image_path):
        cardback_image = pygame.image.load(cardback_image_path).convert_alpha()
        card_images['cardback1'] = ('cardback1', cardback_image)
    else:
        print("Error: cardback1 image not found.")

    for suit in suits:
        for rank in ranks:
            filename = f"{rank}_of_{suit}.png".lower()
            file_path = os.path.join(cards_folder, filename)
            if os.path.exists(file_path):
                image = pygame.image.load(file_path).convert_alpha()
                card_images[(rank, suit)] = (rank, image)
            else:
                print(f"Error loading {filename}: File not found.")

    return card_images

# Load Button Images
def load_button_images(buttons_folder):
    buttons = {
        'hit': ('hit_button_blue.png', 'hit_button_blue_fade.png'),
        'stand': ('stand_button_blue.png', 'stand_button_blue_fade.png'),
        'double_down': ('doubledown_button_blue.png', 'doubledown_button_blue_fade.png'),
        'play': ('play_button_blue.png', 'play_button_blue_fade.png'),
        'split': ('split_button_blue.png', 'split_button_blue_fade.png'),
        'undo_bet': ('undobet_button_blue.png', 'undobet_button_blue_fade.png'),
        'stop': ('stop_button_blue.png', 'stop_button_blue_fade.png')
    }
    button_images = {}
    buttons_folder = 'buttons'

    for key, (active, inactive) in buttons.items():
        try:
            button_images[f'{key}_active'] = pygame.image.load(os.path.join(buttons_folder, active)).convert_alpha()
            button_images[f'{key}_inactive'] = pygame.image.load(os.path.join(buttons_folder, inactive)).convert_alpha()
        except pygame.error as e:
            print(f"Error loading button image: {e}")
    
    return button_images

class CardCountingStrategy(ABC):
    def __init__(self):
        self.running_count = 0

    @abstractmethod
    def update_count(self, card):
        pass

    @abstractmethod
    def calculate_bet(self, base_bet, nb_deck, cards_dealt):
        pass

class HiLowStrategy(CardCountingStrategy):
    def update_count(self, hand):
       for rank in hand:  # Unpack the tuple to get the rank
            if rank in ['2', '3', '4', '5', '6']:
                self.running_count += 1
            elif rank in ['10', 'jack', 'queen', 'king', 'ace']:
                self.running_count -= 1

    def calculate_bet(self, base_bet, nb_deck, cards_dealt):
        decks_remaining = ((nb_deck * 52) - cards_dealt) / 52
        true_count = self.running_count / decks_remaining
        if true_count <= 1:
            return int(base_bet)
        elif true_count < 3:
            return int(base_bet * 2)
        else:
            return int(base_bet * 4)

class KOStrategy(CardCountingStrategy):
    def update_count(self, hand):
        for rank in hand:  # Unpack the tuple to get the rank
            if rank in ['2', '3', '4', '5', '6', '7']:
                self.running_count += 1
            elif rank in ['10', 'jack', 'queen', 'king', 'ace']:
                self.running_count -= 1

    def calculate_bet(self, base_bet, nb_deck, cards_dealt):
        # KO strategy does not convert to true count
        if self.running_count <= 1:
            return int(base_bet)
        elif self.running_count < 4:
            return int(base_bet * 2)
        else:
            return int(base_bet * 4)

class FiveCountStrategy(CardCountingStrategy):
    def __init__(self, nb_deck):
        super().__init__()
        self.total_fives = nb_deck * 4  # Total number of fives in the deck(s)
        self.seen_fives = 0             # Track number of fives seen
        self.total_cards = nb_deck * 52 # Total number of cards in the deck(s)

    def update_count(self, hand):
        for rank in hand:  # Unpack the tuple to get the rank
            if rank == '5':
                self.seen_fives += 1
            self.total_cards -= 1

    def calculate_bet(self, base_bet, nb_deck, cards_dealt):
        unseen_fives = self.total_fives - self.seen_fives
        unseen_cards = self.total_cards - cards_dealt

        if unseen_cards > 0:
            count_ratio = unseen_cards / unseen_fives
        else:
            count_ratio = float('inf')  # Avoid division by zero

        if count_ratio > 14:
            return int(base_bet * 4)  # Bet more if ratio is higher
        elif count_ratio < 12:
            return int(base_bet * 0.5)  # Bet less if ratio is lower
        else:
            return int(base_bet)

class IntroScreen:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.num_players = None
        self.player_position = None
        self.num_decks = None
        self.strategy_choice = None
        self.basic_strategy_advice = None
        self.initial_bet = None
        self.active_field = None
        self.fields = {
            'num_players': {'prompt': 'Enter number of players (1-7):', 'input': '', 'position': (50, 100)},
            'player_position': {'prompt': 'Enter your position (1-7):', 'input': '', 'position': (50, 150)},
            'num_decks': {'prompt': 'Enter number of decks (1-8):', 'input': '', 'position': (50, 200)},
            'strategy_choice': {'prompt': 'Choose a card counting strategy (1: None, 2: HiLow, 3: KO, 4: Five Count):', 'input': '', 'position': (50, 250)},  # Update prompt
            'initial_bet': {'prompt': 'Enter your base bet:', 'input': '', 'position': (50, 300)},
            'basic_strategy': {'prompt': 'Do you want basic strategy advice? (Yes/No):', 'input': '', 'position': (50, 350)}
            }

        self.current_field = list(self.fields.keys())[0]
        self.buttons = {} 

    def draw_text(self, text, position, color=(255, 255, 255)):
        text_surface = self.font.render(text, True, color)
        self.screen.blit(text_surface, position)

    def draw_input_fields(self):
        self.screen.fill((0, 128, 0))  # Background color
        for key, field in self.fields.items():
            prompt_text = f"{field['prompt']} {field['input']}"
            color = (255, 255, 0) if key == self.current_field else (255, 255, 255)
            self.draw_text(prompt_text, field['position'], color)
    
    def check_button_clicks(self, position):
        """ Check if a button was clicked and execute its action. """
        if self.buttons:
            for button_key, button in self.buttons.items():
                if button['rect'].collidepoint(position):
                    button['action']()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                # Handle the current input field
                self.process_input_field()
            elif event.key == pygame.K_BACKSPACE:
                # Handle backspace for current field
                if self.current_field:
                    self.fields[self.current_field]['input'] = self.fields[self.current_field]['input'][:-1]
            else:
                # Handle general text input
                if self.current_field:
                    self.fields[self.current_field]['input'] += event.unicode
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Check for button clicks
            self.check_button_clicks(event.pos)
   
    def process_input_field(self):
        try:
            if self.current_field == 'num_players':
                num_players = int(self.fields['num_players']['input'])
                if 1 <= num_players <= 7:
                    self.num_players = num_players
                    self.current_field = 'player_position'
                else:
                    print("Invalid number of players")
            elif self.current_field == 'player_position':
                player_position = int(self.fields['player_position']['input'])
                if 1 <= player_position <= self.num_players:
                    self.player_position = player_position
                    self.current_field = 'num_decks'
                else:
                    print("Invalid player position. Must be within the number of players.")
            elif self.current_field == 'num_decks':
                num_decks = int(self.fields['num_decks']['input'])
                if 1 <= num_decks <= 8:
                    self.num_decks = num_decks
                    self.current_field = 'strategy_choice'
                else:
                    print("Invalid number of decks")
            elif self.current_field == 'strategy_choice':
                strategy_choice = int(self.fields['strategy_choice']['input'])
                if strategy_choice in [1, 2, 3, 4]:
                    self.strategy_choice = strategy_choice
                    if strategy_choice == 1:
                        self.current_field = 'basic_strategy'  # Skip base bet question if no card counting is chosen
                    else:
                        self.current_field = 'initial_bet'  # Ask base bet question for all other strategies
                else:
                    print("Invalid strategy choice")
            elif self.current_field == 'initial_bet':
                initial_bet = int(self.fields['initial_bet']['input'])
                if initial_bet > 0:
                    self.initial_bet = initial_bet
                    self.base_bet = initial_bet  # Set the base_bet here
                    self.current_field = 'basic_strategy'  
                else:
                    print("Invalid bet amount")
            elif self.current_field == 'basic_strategy':
                basic_strategy = self.fields['basic_strategy']['input'].lower()
                if basic_strategy in ['yes', 'no']:
                    self.basic_strategy_advice = basic_strategy == 'yes'
                    self.current_field = None  # All inputs completed
                else:
                    print("Invalid input for basic strategy advice. Enter 'Yes' or 'No'.")
        except ValueError:
            print("Invalid input")

    def run(self):
        """Runs the intro screen until all inputs are collected"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                else:
                    self.handle_event(event)

            self.draw_input_fields()
            pygame.display.flip()

            if not self.current_field:
                running = False

        return (self.num_players, self.player_position, self.num_decks, self.strategy_choice, self.basic_strategy_advice, self.initial_bet)

class Blackjack:
    def __init__(self, screen, font, card_images, button_images, num_players, player_position, num_decks, strategy_choice, basic_strategy_advice, initial_bet):    
        """Initializes the Blackjack game with the given settings"""
        # Game setup
        self.screen = screen
        self.font = font
        self.card_images = card_images
        self.button_images = button_images
        self.setup_buttons()  
        self.count_cards = False
        self.num_players = num_players
        self.nb_deck = num_decks
        self.cards_dealt = 0
        self.hands = [[] for _ in range(num_players + 1)]  # Players + Dealer
        self.dealer_index = num_players  # Dealer is the last in the hands list
        self.player_index = player_position - 1
        self.player_balance = 1000
        self.base_bet = initial_bet  # Ensure base_bet is set from initial_bet
        self.next_bet_input = '' 
        self.splitted = False
        self.current_hand_index = 0
        self.double_down_taken = False 
        self.basic_strategy_advice = basic_strategy_advice

        self.can_double_down = True  # Flag for double down
        self.can_split = True        # Flag for split
        self.double_down_taken = False  # Flag to track if double down was taken
        self.original_bet = initial_bet  # Store the initial bet separately
        self.current_bet = initial_bet    # Set the current bet initially
        
        # Initialize Strategy
        self.strategy = None  
        self.choose_strategy(strategy_choice)

        # Game Variables
        self.wealth = [self.player_balance]
        self.show_basic_strategy = False
        self.reshuffle_cards()

        self.round_in_progress = True

        # Advice and Status
        self.advice = ''
        self.current_action = ''
        self.action_done = False
        self.next_bet_advice = 0
        self.prompt_message = ''

        # Button UI Setup
        self.buttons = {
            'hit': {'image': button_images['hit_active'], 'position': (650, 500)},
            'stand': {'image': button_images['stand_active'], 'position': (650, 450)},
            'double_down': {'image': button_images['double_down_active'], 'position': (650, 400)},
            'split': {'image': button_images['split_active'], 'position': (650, 300)},
            'play': {'image': button_images['play_active'], 'position': (1500, 700)},
            'stop': {'image': button_images['stop_active'], 'position': (1500, 700)}
        }

        # Initialize button rectangles
        for button in self.buttons.values():
            if button is not None:
                button['rect'] = pygame.Rect(button['position'][0], button['position'][1], button['image'].get_width(), button['image'].get_height())

    def choose_strategy(self, choice):
        strategies = {
            1: None,  # No strategy
            2: HiLowStrategy,
            3: KOStrategy,
            4: lambda: FiveCountStrategy(self.nb_deck)  
        }
        strategy_class = strategies.get(choice, None)
        if strategy_class is not None:
            self.strategy = strategy_class()
        else:
            self.strategy = None

    def create_deck(self):
        deck = []
        for _ in range(self.nb_deck):
            for suit in ['clubs', 'diamonds', 'hearts', 'spades']:
                for rank in ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'jack', 'queen', 'king', 'ace']:
                    card = self.card_images.get((rank, suit), None)
                    if card:
                        deck.append(card)  
                    else:
                        print(f"Missing card image for {rank} of {suit}")
        return deck

    def draw_text(self, text, position, color=(255, 255, 255)):
        text_surface = self.font.render(text, True, color)
        self.screen.blit(text_surface, position)

    def reshuffle_cards(self):
        self.deck = self.create_deck()
        random.shuffle(self.deck)
        self.cards_dealt = 0
        self.reshuffle_threshold = random.randint(int(0.6 * len(self.deck)), int(0.9 * len(self.deck)))
        if self.strategy:
            self.strategy.running_count = 0  # Reset the count for the strategy
            self.current_bet = self.strategy.calculate_bet(self.base_bet, self.nb_deck, self.cards_dealt)
        
        # Display reshuffling message on screen
        reshuffle_text = self.font.render("Shuffling Cards...", True, (255, 255, 0))
        reshuffle_rect = reshuffle_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2))
        self.screen.blit(reshuffle_text, reshuffle_rect)
        pygame.display.flip()

        # Wait for a second to simulate the shuffling effect
        pygame.time.wait(1000)
     
    def deal_card(self, hand, x, y):
        
        if self.cards_dealt >= self.reshuffle_threshold:
            self.reshuffle_cards()
        card = self.deck.pop()
        hand.append(card)
        self.cards_dealt += 1  # Increment cards dealt
        card_position_x = x + (len(hand) - 1) * 30  # Offset each card by 30 pixels
        self.screen.blit(card[1], (card_position_x, y))
        pygame.display.flip()
        if self.strategy:
            self.strategy.update_count(card)  # Pass the card to update the count
        pygame.time.wait(500)

        if len(hand) > 2:  # More than two cards means the player has hit
            self.can_double_down = False
            self.can_split = False
        
    def sum_hand(self, hand):
        values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
                'jack': 10, 'queen': 10, 'king': 10, 'ace': 11}
        result = 0
        aces = 0
        for card in hand:
            if card[0] == 'cardback1':
                continue  # Skip this card as its value and rank are unknown
            rank = card[0]
            if rank == 'ace':
                aces += 1
            result += values.get(rank, 0)  # Safely get the value, defaulting to 0 if not found
        while result > 21 and aces:
            result -= 10
            aces -= 1
        return result

    def prepare_new_deal(self):
        """Ensure betting advice and input are shown before dealing a new round."""
        self.clear_board()  # Clear the board before dealing new cards
        self.input_next_bet()  # Make sure to capture the next bet before dealing cards
        # Check if the deck needs reshuffling
        if len(self.deck) < self.reshuffle_threshold:
            self.reshuffle_cards()
        else:
            self.deal_new_round()
    
    def initial_deal(self):
        """Deals the initial two cards to each player and the dealer"""
        # Clear existing hands first
        self.hands = [[] for _ in range(self.num_players + 1)]  # Include dealer's hand at the end

        # Determine positions dynamically 
        for index, hand in enumerate(self.hands):
            x, y = self.calculate_card_position(index)
            self.deal_card(hand, x, y)  # Deal first card openly
            if index == self.dealer_index:  # Special handling for the dealer's second card
                # Store second card but do not show it yet
                self.deal_hidden_card(hand, x, y)
            else:
                self.deal_card(hand, x, y)  # Deal second card openly for players
    
    
    def deal_hidden_card(self, hand, x, y):
        """ Deal a hidden card to the dealer """
        card = self.deck.pop()
        hand.append(('HIDDEN', card[1]))  # Hide the card initially
        self.dealer_hidden_card = card  # Store the actual card to reveal later

    def deal_new_round(self):
        # Prepare the hands without dealing new cards immediately
        self.hands = [[] for _ in range(self.num_players + 1)]  # Reset hands for all players and the dealer
        self.draw_interface()  # Redraw the interface to reflect the clean slate
        pygame.display.flip()

    def calculate_card_position(self, index):
        """Revised to center the dealer consistently at the top and distribute players evenly below."""
        if index == self.dealer_index:  # Dealer's position
            x = self.screen.get_width() // 2 - 45  # Centering for the dealer
            y = 50  # Top of the screen
        elif index == self.player_index + 1 and self.splitted:
            x = 50 + self.player_index * 200
            y = 400  # Position the second split hand below the first one
        else:  # Player positions
            num_players = self.num_players  # Assuming this is set correctly
            spacing = (self.screen.get_width() - 100) / max(num_players, 1)
            x = 50 + index * spacing
            y = 300  # Lower part of the screen
        return x, y

    def draw_hand(self, hand, x, y, label=None):
        """Draws a single hand at the specified position, revealing the dealer's hidden card if present."""
        for i, (rank, image) in enumerate(hand):
            if rank == 'HIDDEN':
                # Show cardback for the hidden card initially
                card_image = self.card_images['cardback1'][1]
            else:
                card_image = image
            card_position_x = x + i * 30  # Offset each card by 30 pixels
            card_position_y = y
            self.screen.blit(card_image, (card_position_x, card_position_y))
        
        if label:
            self.draw_text(label, (x, y - 30), (255, 255, 255))

    def draw_interface(self):
        self.screen.fill((0, 128, 0))  # Green background
        
        # Draw dealer's hand at the top center
        dealer_x = self.screen.get_width() // 2 - 45  
        dealer_y = 50
        self.draw_hand(self.hands[self.dealer_index], dealer_x, dealer_y, "Dealer")
        
        # Determine the horizontal start position for players
        num_players = self.num_players
        spacing = (self.screen.get_width() - 100) / num_players

        # Draw each player's hand
        for index, hand in enumerate(self.hands[:-1]):
            player_x = 50 + index * spacing
            player_y = 300  # Fixed vertical position for all players
            label = f"Player {index + 1}" if index != self.player_index else "Your Hand"
            self.draw_hand(hand, player_x, player_y, label=label)

        if self.basic_strategy_advice and self.hands[self.dealer_index]:
            dealer_hand = self.hands[self.dealer_index]
            advice = self.basic_strategy(self.player_index, dealer_hand)
            self.draw_text(f"Basic strategy advice: {advice}", (50, 700), (255, 255, 0))

    def dealer_turn(self):
        """Plays the dealer's turn and reveals the hidden card."""
        # Reveal second card
        self.hands[0][1] = self.dealer_hidden_card
        self.draw_hand(self.hands[0], self.dealer_x, self.dealer_y, False)  # Redraw dealer's hand with the revealed card
        # Continue with dealer's game logic
        dealer_hand = self.hands[0]
        while self.sum_hand(dealer_hand) < 17:
            self.deal_card(dealer_hand, (160, 100))

    def reveal_dealer_card(self):
        """Reveals the dealer's hidden card at the end of the round"""
        if hasattr(self, 'dealer_hidden_card') and 'HIDDEN' in [rank for rank, _ in self.hands[self.dealer_index]]:
            # Replace the 'HIDDEN' card with the actual card
            hidden_card = self.dealer_hidden_card
            self.hands[self.dealer_index][1] = hidden_card
            x, y = self.calculate_card_position(self.dealer_index)
            self.draw_hand(self.hands[self.dealer_index], x, y, "Dealer")

    def update_buttons(self):
        """Update button visibility and interactivity."""
        for button_key, button in self.buttons.items():
            if button['visible']:
                button['rect'] = pygame.Rect(button['position'][0], button['position'][1], button['image'].get_width(), button['image'].get_height())
            else:
                button['rect'] = None
   
    def draw_buttons(self):
        """Draws action buttons like Split, Double, Hit, Stand, Play, and Stop."""
        button_x = 50  # Starting x position for buttons
        button_y = 500  # Fixed y position for buttons
        button_spacing = 125  # Horizontal space between buttons

        for key in ['split', 'double_down', 'hit', 'stand', 'play', 'stop']:
            button = self.buttons.get(key)
            if button and button['visible']:
                button['position'] = (button_x, button_y)
                self.screen.blit(button['image'], button['position'])
                button['rect'] = pygame.Rect(button_x, button_y, button['image'].get_width(), button['image'].get_height())
                button_x += button_spacing

    def check_button_clicks(self, position):
        """ Check if a button was clicked and execute its action. """
        for button in self.buttons.values():
            if button['rect'] is not None and button['rect'].collidepoint(position):
                button['action']()  # Execute the associated action

    def setup_buttons(self):
        self.buttons = {
            'hit': {'image': self.button_images['hit_active'], 'position': (650, 500), 'action': self.hit_action, 'visible': True},
            'stand': {'image': self.button_images['stand_active'], 'position': (650, 550), 'action': self.stand_action, 'visible': True},
            'double_down': {'image': self.button_images['double_down_active'], 'position': (650, 600), 'action': self.double_down_action, 'visible': True},
            'split': {'image': self.button_images['split_active'], 'position': (650, 650), 'action': self.split_action, 'visible': True},
            'play': {'image': self.button_images['play_active'], 'position': (650, 700), 'action': self.play_action, 'visible': False},
            'stop': {'image': self.button_images['stop_active'], 'position': (750, 700), 'action': self.stop_action, 'visible': False}
        }

        for key, button in self.buttons.items():
            if button['visible']:
                button['rect'] = pygame.Rect(button['position'][0], button['position'][1], button['image'].get_width(), button['image'].get_height())
            else:
                button['rect'] = None

    def handle_player_action_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for key, button in self.buttons.items():
                if button['visible'] and button['rect'].collidepoint(event.pos):
                    button['action']()
                    self.action_done = True
                    return True
        return False

    def hit_action(self):
        player_hand = self.hands[self.player_index]
        x, y = self.calculate_card_position(self.player_index)
        self.deal_card(player_hand, x, y)
        if self.sum_hand(player_hand) >= 21:
            self.action_done = True  # End turn if player hits 21 or busts
        self.update_buttons()  # Update buttons possibly to disable hit and double down if necessary

    def stand_action(self):
        self.action_done = True  
      
    def double_down_action(self):
        if self.can_double_down and self.player_balance >= self.current_bet * 2:
            self.player_balance -= self.current_bet  # Deduct the original bet first
            self.current_bet *= 2  # Double the bet
            self.double_down_taken = True  # Set the double down flag
            self.hit_action()
            self.stand_action()  # Automatically end the turn after doubling down
            self.can_double_down = False  # Prevent further actions after doubling down
        else:
            print("Cannot double down now.")

    def split_action(self):
        player_hand = self.hands[self.player_index]
        if self.can_split and len(player_hand) == 2 and player_hand[0][0] == player_hand[1][0] and self.player_balance >= self.current_bet * 2:
            self.current_bet *= 2
            new_hand1 = [player_hand.pop(0)]
            new_hand2 = [player_hand.pop(0)]
            self.hands.insert(self.player_index + 1, new_hand2)
            self.hands[self.player_index] = new_hand1
            self.splitted = True  # Add a flag to indicate split
            self.current_hand_index = 0  # Start with the first hand
            x1, y1 = self.calculate_card_position(self.player_index)
            x2, y2 = self.calculate_card_position(self.player_index + 1)
            self.deal_card(new_hand1, x1, y1)
            self.deal_card(new_hand2, x2, y2 + 100)  # Offset the second hand below the first hand
            print(f"Player {self.player_index + 1} splits hand.")
            self.can_split = False  # Set this flag to False when player splits
        else:
            print("Cannot split now.") 

    def play_action(self):
        
        # Clear the board for the new round and wait for bet input
        self.clear_board()
        self.draw_interface()
        self.draw_buttons()
        # Hide the play and stop buttons initially
        self.buttons['play']['visible'] = False
        self.buttons['stop']['visible'] = False
        pygame.display.flip()

    def stop_action(self):
        print("Stop button pressed")  
        self.display_game_over()
    
    def prepare_new_deal(self):
        """Clears the board and deals new cards only after a bet has been placed."""
        self.clear_board()  # Clear the board before dealing new cards
        if len(self.deck) < self.reshuffle_threshold:
            self.reshuffle_cards()

        # Deal a new round now that the bet is set
        self.deal_new_round()

        # Redraw the interface
        self.draw_interface()
        pygame.display.flip()

    def display_final_wealth(self):
        """Displays the final wealth screen with an option to start a new game."""
        self.screen.fill((0, 0, 0))  # Black background
        final_wealth_text = self.font.render(f"Final Wealth: ${self.player_balance}", True, (255, 255, 255))
        play_again_text = self.font.render("Press PLAY to start a new game", True, (255, 255, 0))

        self.screen.blit(final_wealth_text, (350, 250))
        self.screen.blit(play_again_text, (350, 300))

        # Make the PLAY button visible
        self.buttons['play']['visible'] = True

        pygame.display.flip()

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.buttons['play']['rect'].collidepoint(event.pos):
                        waiting = False
                        self.play_action()  

    def reset_game(self):
        """Resets the game state for a new game."""
        self.player_balance = 1000  # Reset player balance
        self.wealth = []
        self.current_bet = 0
        self.reshuffle_cards()
        self.buttons['play']['visible'] = False
        self.clear_board()
           
    def handle_bet_input_event(self, event):
        """Handles input events for the bet prompt."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.next_bet_input.isdigit() and int(self.next_bet_input) > 0:
                    bet = int(self.next_bet_input)
                    if bet <= self.player_balance:
                        self.current_bet = bet
                        self.next_bet_input = ''  # Clear input field
                        return True  # Bet successfully set
                    else:
                        print(f"Insufficient balance. Your balance is ${self.player_balance}, but the bet was ${bet}.")
                else:
                    print("Invalid input, please enter a valid positive number.")
                self.next_bet_input = ''  # Clear input field in case of any error
            elif event.key == pygame.K_BACKSPACE:
                self.next_bet_input = self.next_bet_input[:-1]  # Remove last character
            elif event.unicode.isdigit():  # Ensure that only numeric input is allowed
                self.next_bet_input += event.unicode
        return False

    def input_next_bet(self):  
        """Prompts the user for the next bet, ensuring the bet is set before moving on."""
        betting_complete = False  # Properly initializing betting_complete
        self.prompt_message = "Enter your bet:"
        self.clear_board()  # Clear the screen for a fresh bet prompt
        pygame.display.flip()

        while not betting_complete:
            self.clear_board()
            self.draw_bet_prompt()  # Display the initial betting prompt
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if self.handle_bet_input_event(event):
                        betting_complete = True  # End the loop if the bet is successfully set

        # Set the current bet after input is completed
        if self.next_bet_input.isdigit():  
            self.current_bet = self.next_bet_input 

        # Prepare for a new deal now that the bet has been confirmed
        self.prepare_new_deal()

    def draw_bet_prompt(self):
        """Draws the bet prompt and input field."""
        if self.strategy:
            suggested_bet = self.strategy.calculate_bet(self.base_bet, self.nb_deck, self.cards_dealt)
            strategy_message = f"Suggested bet based on strategy: ${suggested_bet}"
        else:
            strategy_message = ""

        bet_prompt_text = self.font.render(self.prompt_message, True, (255, 255, 0))
        bet_input_text = self.font.render(f"{self.next_bet_input}", True, (255, 255, 0))
        strategy_text = self.font.render(strategy_message, True, (255, 255, 0))

        self.screen.blit(bet_prompt_text, (50, 50))
        self.screen.blit(bet_input_text, (50, 100))
        if strategy_message:
            self.screen.blit(strategy_text, (50, 200))

    def handle_bet_input_event(self, event):
        """Processes betting input events and checks for valid bet confirmation."""
        if event.key == pygame.K_RETURN:
            if self.next_bet_input.isdigit() and int(self.next_bet_input) > 0:
                bet = int(self.next_bet_input)
                if bet <= self.player_balance:
                    self.current_bet = bet  # Set the current bet to the entered amount
                    self.next_bet_input = ''  # Clear the input field
                    return True  # Return True to signal a successful bet setup
                else:
                    print(f"Insufficient balance. Your balance is ${self.player_balance}, but the bet was ${bet}.")
            else:
                print("Invalid input. Please enter a positive number.")
            self.next_bet_input = ''  # Reset the input on error
        elif event.key == pygame.K_BACKSPACE:
            self.next_bet_input = self.next_bet_input[:-1]  # Allow backspace functionality
        elif event.unicode.isdigit():
            self.next_bet_input += event.unicode  # Append new digits
        return False  # Continue receiving input if no valid bet is confirmed

    def basic_strategy(self, index, dealer_hand):
        player_hand = self.hands[index]
        player_total = self.sum_hand(player_hand)
        dealer_card_rank = dealer_hand[0][0] 
        dealer_value = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'jack': 10, 'queen': 10, 'king': 10, 'ace': 11}[dealer_card_rank]

        # Check for soft hand (Ace as 11)
        soft = 'ace' in [card[0] for card in player_hand] and player_total <= 21
        
        # Check for pairs (only applicable for the first decision with two cards)
        pair = len(player_hand) == 2 and player_hand[0][0] == player_hand[1][0]

        can_double = len(player_hand) == 2

        if player_total < 8:
            return 'hit'
        
        if player_total == 8:
            if dealer_value in [2, 3, 4, 7, 8, 9, 10, 11]:
                return 'hit'
            else:
                return 'double'
        
        if player_total == 9:
            if dealer_value in [7, 8, 9, 10, 11]:
                return 'hit'
            elif can_double:
                return 'double'
            else:
                return 'hit'
        
        if player_total == 10:
            if dealer_value in [10, 11] or not can_double:
                return 'hit'
            return 'double'
            
        if player_total == 11:
            if can_double:
                return 'double'
            else:
                return 'hit'
        
        if player_total == 12:
            if dealer_value in [2, 3, 7, 8, 9, 10, 11]:
                return 'hit'
            return 'stand'
        
        if player_total in [13, 14, 15, 16]:
            if dealer_value in [2, 3, 4, 5, 6]:
                return 'stand'
            return 'hit'

        if player_total >= 17:
            return 'stand'
        
        if soft:
            
            if player_total in [13, 14, 15, 16] and can_double:
                if dealer_value in [4, 5, 6]:
                    return 'double'
                return 'hit'
                
            if player_total == 17:
                if dealer_value in [2, 3, 4, 5, 6] and can_double:
                    return 'double'
                return 'hit'
            
            if player_total == 18:
                if dealer_value in [3, 4, 5, 6] and can_double:
                    return 'double'
                if dealer_value in [2, 7, 8, 11]:
                    return 'stand'
                return 'hit'
            
            if player_total == 19:
                if dealer_value == 6 and can_double:
                    return 'double'
                return 'stand'
            
            if player_total == 20:
                return 'stand'

        if pair:
            
            if player_total == 4:
                if dealer_value in [3, 4, 5, 6, 7]:
                    return 'split'
                return 'hit'
            
            if player_total == 6:
                if dealer_value in [4, 5, 6, 7]:
                    return 'split'
                return 'hit'
            
            if player_total == 8:
                if dealer_value in [5, 6]:
                    return 'double'
                return 'hit'
            
            if player_total == 10:
                if dealer_value in [10, 11]:
                    return 'hit'
                return 'double'
            
            if player_total ==12:
                if dealer_value in [2, 3, 4, 5, 6]:
                    return 'split'
                return 'hit'

            if player_total == 14:
                if dealer_value in [8, 9, 11]:
                    return 'hit'
                if dealer_value == 10:
                    return 'stand'
                return 'split'

            if player_total == 18:
                if dealer_value in [7, 10, 11]:
                    return 'stand'
                return 'split'
            
            if player_total == 20:
                return 'stand'

            if player_total == 16 or player_hand.count('A') == 2:
                return 'split'
 
    def handle_player_actions(self, player_index):
        """Handles the actions of a single player in the round."""
        if not self.check_blackjack(player_index):
            self.player_turn(player_index)
            
    def draw_basic_strategy_advice(self, advice, x, y):
        """Draws basic strategy advice next to the player's hand value"""
        advice_text = self.font.render(f"Advice: {advice}", True, (255, 255, 0))
        self.screen.blit(advice_text, (x + 120, y - 30))
    
    def handle_player_action_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for key, button in self.buttons.items():
                if button['visible'] and button['rect'].collidepoint(event.pos):
                    print(f"Button {key} clicked")  # Debugging statement
                    button['action']()
                    # Only set action_done for stand and double down actions
                    if key in ['stand', 'double_down', 'stop']:
                        self.action_done = True
                    return True  # Return after any button press to avoid multiple detections
        return False

    def draw_player_buttons(self):
        """Draws action buttons (hit, stand, double down, split) on the screen"""
        for button in self.buttons.values():
            self.screen.blit(button['image'], button['position'])
   
    def determine_next_bet(self):
        """Determines and returns the next bet based on the card counting strategy"""
        if self.strategy:
            self.next_bet_advice = self.strategy.calculate_bet(self.base_bet, self.nb_deck, self.cards_dealt)
        else:
            self.next_bet_advice = self.base_bet
        return self.next_bet_advice

    def draw_next_bet_advice(self):
        """Draws the next bet advice on the screen"""
        advice_text = self.font.render(f"Next Bet: ${self.next_bet_advice}", True, (255, 255, 0))
        self.screen.blit(advice_text, (50, 50))
 
    def initial_deal(self):
        """Deals the initial two cards to each player and the dealer, should be called only once per round."""
        # Clear existing hands first if needed
        if not self.hands:
            self.hands = [[] for _ in range(self.num_players + 1)]  # Include dealer's hand at the end

        # Deal two cards to each player and one to the dealer with one hidden
        for index, hand in enumerate(self.hands):
            x, y = self.calculate_card_position(index)
            self.deal_card(hand, x, y)  # Deal first card openly
            if index == self.dealer_index:
                self.deal_hidden_card(hand, x, y)  # Dealer's second card is hidden
            else:
                self.deal_card(hand, x, y)  # Second card openly for players

    def clear_board(self):
        """Clears the board after each round"""
        self.screen.fill((0, 128, 0))  # Reset the background
        pygame.display.flip()
    
    def display_end_of_round_info(self):
        """Display wealth, next bet advice, and accept next bet input before a new round."""
        self.screen.fill((0, 128, 0))  # Clearing the screen
        wealth_text = f"Ending Wealth: ${self.player_balance}"
        next_bet_advice = f"Next Bet: ${self.determine_next_bet()}"
        self.draw_text(wealth_text, (50, 100), (255, 255, 255))
        self.draw_text(next_bet_advice, (50, 150), (255, 255, 255))
        #self.input_next_bet()  # Function to handle next bet input
 
    def play_game(self):
        self.reshuffle_cards()
        running = True  # Flag to control the game loop

        while running and self.player_balance > 0:
            self.play_round()
            self.display_end_of_round_info()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif self.handle_player_action_event(event):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.buttons['stop']['rect'] and self.buttons['stop']['rect'].collidepoint(event.pos):
                            self.stop_action()
                            running = False
                            break  # Exit the loop

            if self.player_balance <= 0:
                break

            self.clear_board()  # Clear the board for the next round

        print("Game over. Thanks for playing!")
        if running:
            self.display_game_over()

    def play_round(self):
        # Hide the play and stop buttons at the start of the round
          # Reposition the play and stop buttons
        self.buttons['play']['position'] = (1500, 700)  
        self.buttons['stop']['position'] = (1500, 700)   

        self.clear_board()  # Clear the board before starting a new round

        self.determine_next_bet()
        self.input_next_bet()  # Ensure this runs only once per round
        self.initial_deal()

        for player_index in range(self.num_players):
            self.player_turn(player_index)

        self.reveal_dealer_card()
        self.handle_dealer_action()
        self.calculate_round_results()

        # Update the next bet for the following round based on card counting
        if self.count_cards:
            self.current_bet = self.strategy.calculate_bet(self.base_bet, self.nb_deck)

        # Update player wealth tracking and plot changes visually
        self.update_wealth_tracking()
        self.draw_interface()

        # Ensure buttons are displayed correctly
        self.update_buttons()
        self.draw_buttons()

        pygame.time.wait(300)

        # Call display_round_result to show the result screen
        self.display_round_result()

    def check_blackjack(self, hand_index):
        """Check if the specified hand has a blackjack."""
        hand = self.hands[hand_index]
        return len(hand) == 2 and self.sum_hand(hand) == 21
    
    def player_turn(self, index):
        self.can_double_down = True  # Reset this at the start of each turn
        self.can_split = True        # Reset this at the start of each turn
        self.double_down_taken = False  # Reset double down flag

        player_name = "You" if index == self.player_index else f"Player {index + 1}"
        hand = self.hands[index]

        # Clear previous action
        self.current_action = ''
        self.action_done = False

        # Hide play and stop buttons
        self.buttons['play']['visible'] = False
        self.buttons['stop']['visible'] = False

        if index != self.player_index:  # Bot logic for other players
            print(f"{player_name}'s hand: {hand}, Total: {self.sum_hand(hand)}")
            while self.sum_hand(hand) < 17:
                x, y = self.calculate_card_position(index)
                self.deal_card(hand, x, y)
            if self.sum_hand(hand) > 21:
                print(f"{player_name} busts.")
            else:
                print(f"{player_name} stands.")
        else:
            # Check for blackjack
            if self.check_blackjack(index):
                print(f"{player_name} get BLACKJACK!")
                self.draw_text(f"{player_name} get BLACKJACK!", (200, 200), (255, 255, 0))
                pygame.display.flip()
                pygame.time.wait(2000)
                self.action_done = True
                return  # Player turn ends automatically if they get a blackjack

            # Player's turn with graphical UI
            self.draw_interface()
            self.draw_buttons()
            # Hide the play and stop buttons initially
            self.buttons['play']['visible'] = False
            self.buttons['stop']['visible'] = False

            while not self.action_done:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    self.handle_player_action_event(event)

                self.screen.fill((0, 128, 0))  # Green table background
                self.draw_interface()
                self.draw_player_buttons()

                if self.show_basic_strategy:
                    advice = self.basic_strategy(index, self.hands[-1])  # Assuming dealer's hand is the last in the list
                    self.draw_basic_strategy_advice(advice, 100, 350)

                pygame.display.flip()

            if self.splitted and self.current_hand_index == 0:
                self.current_hand_index += 1
                self.action_done = False
                self.player_turn(self.player_index + 1)

        pygame.time.wait(300)

    def handle_dealer_action(self):
        """Handles the actions of the dealer"""
        # Dealer X and Y coordinates need to be defined, assuming some values here
        dealer_x = 100  
        dealer_y = 50   
        dealer_hand = self.hands[self.dealer_index]
        while self.sum_hand(dealer_hand) < 17:
            self.deal_card(dealer_hand, dealer_x, dealer_y)
        
        pygame.time.wait(1000)
       
    def calculate_round_results(self):
        """Calculates and prints the results of the round for the real player"""
        self.round_result = ""  # Initialize the round result
        dealer_total = self.sum_hand(self.hands[self.dealer_index])
        player_total = self.sum_hand(self.hands[self.player_index])

        # Determine result for the player
        if player_total > 21:
            result_text = "You bust."
            self.player_balance -= self.current_bet  # Deduct the current bet if the player busts
        elif player_total == 21 and len(self.hands[self.player_index]) == 2:
            result_text = "You get BLACKJACK!"
            blackjack_payout = 1.5 * self.current_bet
            self.player_balance += blackjack_payout
            result_text += f" You win {blackjack_payout}!"
        elif dealer_total > 21 or player_total > dealer_total:
            result_text = "You win."
            self.player_balance += self.current_bet  # Add the current bet if the player wins
            self.round_result = "You win!"
        elif player_total < dealer_total:
            result_text = "You lose."
            self.player_balance -= self.current_bet  # Deduct the current bet if the player loses
            self.round_result = "You lose!"
        else:
            result_text = "You tie with the dealer."
            self.round_result = "Tie with the dealer."

        print(result_text)
        print(f"Ending Wealth: ${self.player_balance}")

        # If player busted or got blackjack, set round result accordingly
        if player_total > 21:
            self.round_result = "You bust!"
        elif player_total == 21 and len(self.hands[self.player_index]) == 2:
            self.round_result = "You get BLACKJACK!"

        # Reset double down flag for the next round
        self.double_down_taken = False

    def display_round_result(self):
        """Displays the result of the round and shows the wealth graph"""
        self.screen.fill((0, 128, 0))  # Green background

        result_text = self.round_result
        current_wealth_text = f"Current Wealth: ${self.player_balance}"

        self.draw_text(result_text, (100, 100), (255, 255, 0))
        self.draw_text(current_wealth_text, (100, 150), (255, 255, 255))
        self.draw_text("Press PLAY to continue to play", (100, 200), (255, 255, 255))
        self.draw_text("Press STOP to exit", (100, 250), (255, 255, 255))

        # Reposition the play and stop buttons
        self.buttons['play']['position'] = (650, 700)  
        self.buttons['stop']['position'] = (750, 700)  

        # Show play and stop buttons
        self.buttons['play']['visible'] = True
        self.buttons['stop']['visible'] = True

        # Ensure button rects are updated
        self.update_buttons()
        self.draw_buttons()

        # Plot the wealth graph
        self.plot_wealth_graph()

        pygame.display.flip()

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.buttons['play']['rect'] and self.buttons['play']['rect'].collidepoint(event.pos):
                        waiting = False
                        self.play_action()  # Start a new game
                    elif self.buttons['stop']['rect'] and self.buttons['stop']['rect'].collidepoint(event.pos):
                        pygame.quit()
                        sys.exit()

    def plot_wealth_graph(self):
        fig, ax = plt.subplots(figsize=(5.1, 4.1), facecolor=(0, 128/255, 0))  # Set green background for the figure

        # Plotting the wealth data
        ax.plot(self.wealth, color='red')

        # Setting the title and labels with gold color and bold text
        ax.set_title('Player Wealth Over Time', fontsize=14, fontweight='bold', color='gold')
        ax.set_xlabel('Rounds', fontsize=12, fontweight='bold', color='gold')
        ax.set_ylabel('Wealth', fontsize=12, fontweight='bold', color='gold')

        # Setting the axes to gold
        ax.spines['top'].set_color('none')  # Hide the top spine
        ax.spines['right'].set_color('none')  # Hide the right spine
        ax.spines['bottom'].set_color('gold')
        ax.spines['left'].set_color('gold')

        ax.xaxis.label.set_color('gold')
        ax.yaxis.label.set_color('gold')
        ax.tick_params(axis='x', colors='gold')
        ax.tick_params(axis='y', colors='gold')

        # Set background color for the plot area
        ax.set_facecolor((0, 128/255, 0))

        # Save the plot to a temporary file with a green facecolor
        plot_filename = 'wealth_plot.png'
        fig.savefig(plot_filename, bbox_inches='tight', facecolor=(0, 128/255, 0))  
        plt.close(fig)

        # Load the plot image
        plot_img = pygame.image.load(plot_filename)
        self.screen.blit(plot_img, (50, 300))  

    def update_wealth_tracking(self):
        """Tracks and visually displays changes in player wealth"""
        self.wealth.append(self.player_balance)

        if self.player_balance <= 0:
            print("You've spent all your money.")
            self.display_game_over()
  
    def display_game_over(self):
        print("Displaying game over screen")  
        """Displays the end of game screen with final wealth and the wealth graph."""
        self.screen.fill((0, 128, 0))  

        # Display final wealth
        final_wealth_text = self.font.render(f"End of Game - Final Wealth: ${self.player_balance}", True, (255, 255, 255))
        self.screen.blit(final_wealth_text, (100, 50))

        # Plot wealth graph and save it to a file
        plot_img = pygame.image.load('wealth_plot.png')

        # Get the dimensions of the plot image
        plot_rect = plot_img.get_rect()

        # Position the plot in the center of the screen
        plot_rect.topleft = (100, 150)

        # Draw the plot image on the screen
        self.screen.blit(plot_img, plot_rect)

        # Display restart prompt
        prompt_text = self.font.render("Start a new game (Yes/No): ", True, (255, 255, 0))  # Yellow text
        self.screen.blit(prompt_text, (100, 700))

        pygame.display.flip()

        input_text = ''
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if input_text.lower() == 'yes':
                            self.restart_game()
                            waiting = False
                        elif input_text.lower() == 'no':
                            pygame.quit()
                            sys.exit()
                        else:
                            input_text = ''
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        input_text += event.unicode

                    # Refresh the screen to show the current input
                    self.screen.fill((0, 128, 0))  
                    self.screen.blit(final_wealth_text, (100, 50))
                    self.screen.blit(plot_img, plot_rect)
                    self.screen.blit(prompt_text, (100, 700))
                    input_display = self.font.render(input_text, True, (255, 255, 255))
                    self.screen.blit(input_display, (450, 700))
                    pygame.display.flip()
  
    def restart_game(self):
        # Re-run the intro screen to collect game settings
        intro_screen = IntroScreen(self.screen, self.font)
        try:
            num_players, player_position, num_decks, strategy_choice, basic_strategy_advice, initial_bet = intro_screen.run()
        except ValueError as e:
            print("Error in input handling:", e)
            pygame.quit()
            sys.exit()

        # Load resources (if not already loaded or if they need to be refreshed)
        card_images = load_card_images('cards')
        button_images = load_button_images('buttons')

        # Reinitialize the game with new settings
        self.__init__(self.screen, self.font, card_images, button_images, num_players, player_position, num_decks, strategy_choice, basic_strategy_advice, initial_bet)
        
        # Setup buttons after reinitialization
        self.setup_buttons()

        # Start the game loop again
        self.play_game()

def main():
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))
    font = pygame.font.Font(None, 36)
    
    # Run the intro screen to collect game settings
    intro_screen = IntroScreen(screen, font)
    try:
        num_players, player_position, num_decks, strategy_choice, basic_strategy_advice, initial_bet = intro_screen.run()
    except ValueError as e:
        print("Error in input handling:", e)
        pygame.quit()
        sys.exit()

    # Load resources
    card_images = load_card_images('cards')
    button_images = load_button_images('buttons')
    
    # Initialize the Blackjack game
    game = Blackjack(screen, font, card_images, button_images, num_players, player_position, num_decks, strategy_choice, basic_strategy_advice, initial_bet)
    
    # Setup buttons after all resources are loaded but before the game loop
    game.setup_buttons()
    
    # Start the game loop
    game.play_game()

if __name__ == "__main__":
    main()
