import requests
import random
import time

# Configuration
SERVERS = ['http://localhost:5001', 'http://localhost:5002', 'http://localhost:5003']
NUM_PLAYERS = 7
DROP_INTERVAL = 5 # seconds

game_id = None
players = []
leader = None
sub_leaders = []

def create_game():
    global game_id, leader
    host = 'host1'
    server = random.choice(SERVERS)
    response = requests.post(f'{server}/create_game', json={'host': host})
    if response.status_code == 201:
        game_id = response.json()['game_id']
        leader = host
        print(f'Game created with ID: {game_id} on {server} and host: {host}')
        players.append(host)  # Include host as a player
    else:
        print('Failed to create game')

def join_game(player_id):
    global sub_leaders
    server = random.choice(SERVERS)
    response = requests.post(f'{server}/join_game', json={'game_id': game_id, 'player': player_id})
    if response.status_code == 200:
        players.append(player_id)
        print(f'Player {player_id} joined game {game_id} on {server}')
    else:
        print(f'Failed to join game for player {player_id} on {server}')

def drop_random_player():
    global players, leader, sub_leaders
    while len(players) > 1:
        print('players', players)
        time.sleep(DROP_INTERVAL)
        player_to_remove = random.choice(players)
        server = random.choice(SERVERS)
        response = requests.post(f'{server}/remove_player', json={'game_id': game_id, 'player': player_to_remove})
        if response.status_code == 200:
            players.remove(player_to_remove)
            print(f'Player {player_to_remove} removed from game {game_id} on {server}')
            game_state = requests.get(f'{server}/get_games').json()
            print_game_state(game_state)
        else:
            print(f'Failed to remove player {player_to_remove} on {server}')

def print_game_state(game_state):
    game = game_state.get(game_id)
    if game:
        print(f"Game State for {game_id}:")
        print(f"  Host: {game['host']}")
        print(f"  Leader: {game['leader']}")
        print(f"  Sub-Leaders: {game['sub_leaders']}")
        print(f"  Players: {[player['player_id'] for player in game['players']]}")
    else:
        print(f"No game found with ID: {game_id}")

def main():
    create_game()
    for i in range(1, NUM_PLAYERS + 1):
        join_game(f'player{i}')
    time.sleep(2)  # Wait a bit before starting to drop players
    server = random.choice(SERVERS) # initial state
    game_state = requests.get(f'{server}/get_games').json()
    print_game_state(game_state)
    drop_random_player()

if __name__ == '__main__':
    main()
