#!/usr/bin/python3

import requests # For API Calls 
import math
import sys
import os
from itertools import islice
from openai import OpenAI
os.environ['OPENAI_API_KEY'] = "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"

# ask_chatgpt is a function to encapsulate the API call logic
def ask_chatgpt(prompt):
    client = OpenAI(
    # This is the default and can be omitted
    api_key="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",
    )

    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="gpt-3.5-turbo",
    )
    return response.choices[0].message.content


# Card represents a single card
# Attributes: suit (e.g., "H" for hearts), value (e.g., "T" for ten), and points determined by the card's value.
class Card:
    def __init__(self, name) -> None:
        self.suit = name[0]
        self.value = name[1]
        match self.value:
            case "5":
                self.points = 5
            case "T" | "A":
                self.points = 10
            case _:
                self.points = 0

    # Returns a string representation of the card (e.g., "HT").
    def stringify(self):
        return f"{self.suit}{self.value}"
    
    # Checks if another card's string representation matches this card's.
    def equals(self, card):
        return card == self.stringify()
    
    # Compares the rank of this card against another, based on a predefined order.
    def compare(self, card):
        order = "56789TJQKA"
        self_rank = order.index(self.value)
        card_rank = order.index(card.value)
        # print(f"self {self.value} {self_rank} card {card.value} {card_rank}", file=sys.stderr)
        return self_rank > card_rank
    
    # Returns the strength (rank) of the card.
    def strength(self):
        order = "56789TJQKA"
        return order.index(self.value) + 1

# Hand represents a player's hand of cards.
# Attributes: cards (list of Card objects).
class Hand:
    def __init__(self, cards) -> None:
        self.cards = cards

    # Returns a string representation of all cards in the hand.
    def stringify(self):
        string = ""
        for card in self.cards:
            string += f"{card.stringify()} "
        return string

    # Removes a card from the hand.
    def remove(self, played):
        for card in self.cards:
            if card.equals(played):
                self.cards.remove(card)
                return
            
    # Determines which cards can be legally played based on the game rules.
    def playable(self, trump, trick):
        playable = []
        for card in self.cards:
            if card.suit == trick.required:
                playable.append(card)
        if not playable:
            playable = [card for card in self.cards]
        return playable
    
    #Estimated score for bidding
    #nb de cartes atout
    #force de l'atout
    #couleurs vides
    #points espérés
    #contrôle des points
    #cap de points
    #miser partie si 10 atouts
    def score(self):
        suits = {"C":[0,0,0], "D":[0,0,0], "H":[0,0,0], "S":[0,0,0]}
        for card in self.cards:
            suits.update({card.suit:[suits[card.suit][0]+1, suits[card.suit][1] + card.strength(), suits[card.suit][2] + card.points]})

        high_suit = "C"
        hight_count = suits["C"][0]
        high_strength = suits["C"][1]
        high_score = suits["C"][2]
        empty = []
        bid = 0

        for suit, count in islice(suits.items(), 1, None):
            replace = False

            #If more cards in suit
            if (count[0] > hight_count):
                replace = True

            #If equal cards in suit
            elif (count[0] == hight_count):

                #If higher strength
                if (count[1] > high_strength):
                    replace = True

                #If equal strength and higher score
                elif (count[1] == high_strength) and (count[2] > high_score):
                    replace = True
            
            if replace:
                high_suit = suit
                hight_count = count[0]
                high_strength = count[1]
                high_score = count[2]

            #If empty suit
            if count[0] == 0:
                empty.append(suit)

        #Find value to bid up to:
        if hight_count > 3:
            bid = ((high_strength / 55) * 50 + 7.5 * hight_count) // 5 * 5

            if empty:
                bid += 5 * len(empty)

        return bid, suits, high_suit, hight_count, high_strength, high_score, empty

# Trick represents a single round of play in the game where players each play a card.
# Attributes: played, a dictionary of cards played by player ID, and required, the suit that must be followed if possible.    
class Trick:
    def __init__(self) -> None:
        self.played = {}
        self.required = None

    def stringify(self):
        string = ""
        for player in self.played:
            string += f"{self.played[player].stringify()} "
        return string
    
    def getCards(self):
        return [self.played[player] for player in self.played]
    
    def getPlayed(self):
        return self.played

    def add(self, player, card):
        if not self.played:
            self.required = card.suit
        self.played[player] = card

    def empty(self):
        self.played.clear()
        self.required = None
               
    def score(self):
        sum = 0
        for player in self.played:
            sum += self.played[player].points
        return sum

    # Determines the winner of the trick.
    def winner(self, trump):
        players = list(self.played)
        # print(trump, file=sys.stderr)
        # print(self.played, file=sys.stderr)
        # print(players, file=sys.stderr)
        id = players[0]
        top = self.played[id]
        for player in players[1:]:
            card = self.played[player]
            if card.suit == trump:
                if top.suit == trump:
                    if not top.compare(card):
                        top = card
                        id = player
                else:
                    top = card
                    id = player
            elif card.suit == self.required:
                if not top.compare(card):
                    top = card
                    id = player
        return id

hand = None
turn = 0
player = ""
teammate = 0
team = 0
trick = Trick()
rounds = []
played = {}
bids = [0, 0, 0, 0]
bidWinner = 0
bid_limit = 0
trump = None
new_game = False
game_points = [0, 0]
points = [0, 0]

# Main game loop
while (line := input().split())[0] != "end":
    print(line, file=sys.stderr)

    match line[0]:
        case "player":
            player = line[1]
            teammate = int(player) + 2 % 4
            # print(f"player number {player}, teammate {teammate}\n", file=sys.stderr)

        case "hand":
            new_game = True
            rounds = []
            played = {}
            hand = Hand([Card(card) for card in line[1:]])
            estimate = hand.score()
            bid_limit = estimate[0]
            print(f"initial hand: {hand.stringify()}\n", file=sys.stderr)
            print(f"Estimated score: {estimate}", file=sys.stderr)

        case "bid":
            if line[1] == "?":
                # Construct a prompt for bidding
                # prompt = f"Your current hand is {hand.stringify()}. What do you want to bid?"
                # bid_response = ask_chatgpt(prompt) 
                print("0")
                # Process bid_response to extract the bid value
                #print(bid_response)  # Need to parse this response depending on the output
                
            else:
                bid = int(line[2])
                bids[int(line[1])] = bid
                if bid:
                    bidWinner = int(line[1])

        case "card":
            if line[1] == "?":
                # prompt for playing a card
                rules_prompt = """
                You are a player of "10". The game of "10" is played by two teams of two players each. You use a standard deck of cards, but remove all 2s, 3s, 4s, and jokers, leaving 40 cards in the deck. The cards rank from lowest to highest as follows: 5, 6, 7, 8, 9, 10, Jack (J), Queen (Q), King (K), and Ace (A).
                The goal is to score more points than your team's bid after 10 rounds. Points are earned from cards in won rounds: 10s and Aces are worth 10 points, 5s are worth 5 points, and other cards score nothing.
                At the start, players sit opposite their partner, and cards are shuffled and dealt, giving each player 10 cards. The player to the left of the dealer bids first, and the highest bidder decides the trump suit and starts the game.
                Bidding involves predicting the number of points your team will score. Bids must be in multiples of 5, starting at 50 points. The highest bid wins, and that team must meet or exceed their bid to win the round. The maximum bid is 100 points, but a team can bid "the game," meaning they commit to scoring 100 points. If successful, they earn 500 points; if not, they lose 500 points.
                Scoring is optional. If time allows, keep track of scores on paper, noting which player dealt the cards. Teams can choose names, traditionally "us" and "you," with "us" being the scorekeeper's team. The game ends when a team reaches 500 points. The bidding team scores their collected points if they meet their bid and loses their bid amount if they don't. The defending team scores their collected points under certain conditions. A team can bid "the game" if they have a non-negative score, committing to win all points to win the game. If they fail and lose by at least 5 points, the other team wins.
                You interact with the game by reading from and writing to the standard input and output streams. The judge will send commands to your bot, and you should respond with commands as described below.
                The judge will send the following commands to your bot:
                - "player <id>": The judge is informing you of your player ID, which is an integer from 0 to 3. Your teammate's ID is (id + 2) % 4. You shouldn't respond.
                - "hand <card1> <card2> ... <card10>": The judge is informing you of your hand, which consists of 10 cards. Each card is a string of two characters, where the first character is the rank (5, 6, 7, 8, 9, T, J, Q, K, A) and the second character is the suit (C, D, H, S). You shouldn't respond.
                - "bid ?": The judge is asking you to make a bid. You should respond with a single line containing your bid, which must be an integer from 50 to 105 and a multiple of 5.
                - "card ?": The judge is asking you to play a card. You should respond with a single line containing the card you want to play, which must be one of the cards in your hand.
                Cards are represented by two characters (e.g. HJ for the Jack of Hearts)
                    - Suit: C (Clubs), D (Diamonds), H (Hearts), S (Spades)
                    - Rank: 5, 6, 7, 8, 9, T (10), J (Jack), Q (Queen), K (King), A (Ace)
                Example:
                player 3:
                hand CK CA D8 DK DA H8 HJ HQ ST SQ:
                bid ?:50
                card ?:DK
                card ?:CA
                card ?:D8
                card ?:CK
                card ?:DA
                """
                prompt = f"Your current hand is {hand.stringify()}, and the current trick is {trick.stringify()}. What card do you want to play? Provide the two characters corresponding to the card."
                prompt = rules_prompt + prompt
                card_response = ask_chatgpt(prompt)
                # Process card_response to determine which card to play
                print(card_response)  # Need to parse and format this response

            else:
                turn = (turn + 1) % 4
                card = line[2]
                trick.add(int(line[1]), Card(card))
                # print(f"trick: {trick.stringify()} winner: {trick.winner(trump)}\n", file=sys.stderr)
                if new_game:
                    trump = line[2][0]
                    new_game = False
                if not turn: #turn == 0
                    game_points[trick.winner(trump)%2] += trick.score()
                    # print(f"Trick score: {trick.score()} Trick winner: {trick.winner(trump)} Winning team: {trick.winner(trump)%2} Game score: {game_points}", file=sys.stderr)
                    # played.update(trick.getCards())
                    rounds.append(trick)
                    trick.empty()
                if line[1] == player:
                    hand.remove(card)
                    # print(f"hand: {hand.stringify()}\n", file=sys.stderr)
    