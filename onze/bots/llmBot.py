#!/usr/bin/python3

import requests # For API Calls 
import math
import sys
from itertools import islice

# ask_chatgpt is a function to encapsulate the API call logic
def ask_chatgpt(prompt, api_key):
    url = "https://api.openai.com/v1/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "text-davinci-003",  # Adjust based on current models and  access
        "prompt": prompt,
        "max_tokens": 150,  # Adjust based on  needs
        "temperature": 0.7,  # Adjust for creativity
    }
    response = requests.post(url, json=payload, headers=headers)
    response_json = response.json()
    return response_json["choices"][0]["text"].strip()

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
                prompt = f"Your current hand is {hand.stringify()}. What do you want to bid?"
                bid_response = ask_chatgpt(prompt, OUR_API_KEY) # Replace with actual API key

                # Process bid_response to extract the bid value
                print(bid_response)  # Need to parse this response depending on the output
                
            else:
                bid = int(line[2])
                bids[int(line[1])] = bid
                if bid:
                    bidWinner = int(line[1])

        case "card":
            if line[1] == "?":
                # prompt for playing a card
                prompt = f"Your current hand is {hand.stringify()}, and the current trick is {trick.stringify()}. What card do you want to play?"
                card_response = ask_chatgpt(prompt, OUR_API_KEY) # Replace with actual API key

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
    