from http import server
import requests
import random
import time
import threading
import sys
from flask import Flask, request, jsonify

class GameNode:
    def __init__(self, port):
        self.server_urls = ["http://localhost:5001", "http://localhost:5002", "http://localhost:5003"]
        self.load_url = "http://localhost:80"
        self.port = port
        self.game_id = None
        self.player_id = random.randint(100, 999)
        self.is_leader = False
        self.leader_ip = None
        self.sub_leaders = []
        self.players = []
        self.app = Flask(__name__)
        self.setup_routes()

    def setup_routes(self):
        @self.app.route('/heartbeat', methods=['GET'])
        def heartbeat():
            return jsonify({"status": "alive"}), 200

        @self.app.route('/update_state', methods=['POST'])
        def update_state():
            data = request.json
            self.leader_ip = data['leader_ip']
            self.players = data['players']
            self.sub_leaders = data['sub_leaders']
            self.print_game_state()
            return "State updated", 200

    def run(self):
        threading.Thread(target=self.app.run, kwargs={"host": "0.0.0.0", "port": self.port}, daemon=True).start()

    def create_game(self):
        # server_url = random.choice(self.server_urls)
        server_url = self.load_url
        response = requests.post(f'{server_url}/create_game')
        if response.status_code == 200:
            data = response.json()
            self.game_id = data['game_data']['game_id']
            self.leader_ip = data['game_data']['leader_ip']
            self.is_leader = True
            self.players.append({"player_id": self.player_id, "ip": f'localhost:{self.port}'})
            # leader function
            self.propagate_state()
            print(f"Game created with ID: {self.game_id}. I am the leader with IP: {self.leader_ip}.")
            self.start_heartbeat()
        else:
            print("Failed to create game")

    def join_game(self, game_id=None):
        # server_url = random.choice(self.server_urls)
        server_url = self.load_url
        url = f'{server_url}/join_random_game' if game_id is None else f'{server_url}/join_game/{game_id}'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            self.game_id = data['game_data']['game_id']
            self.leader_ip = data['game_data']['leader_ip']
            self.is_leader = False
            self.players.append({"player_id": self.player_id, "ip": f'localhost:{self.port}'})
            self.propagate_state()
            print(f"Joined {'random' if game_id is None else ''} game with ID: {self.game_id}. Leader IP: {self.leader_ip}.")
            self.start_heartbeat()
        else:
            action = "any game" if game_id is None else f"game {game_id}"
            print(f"Failed to join {action}.")

    def propagate_state(self):
        state = {
            "leader_ip": self.leader_ip,
            "players": self.players,
            "sub_leaders": self.sub_leaders
        }
        for player in self.players:
            if player["ip"] != f'localhost:{self.port}':
                try:
                    requests.post(f'http://{player["ip"]}/update_state', json=state)
                except requests.exceptions.RequestException as e:
                    print(f"Failed to update state on {player['ip']}: {e}")
        self.print_game_state()

    def print_game_state(self):
        print("Current game state:")
        print(f"  Leader: {self.leader_ip}")
        print(f"  Sub-leaders: {self.sub_leaders}")
        print(f"  Players: {self.players}")

    def start_heartbeat(self):
        threading.Thread(target=self.send_heartbeat, daemon=True).start()

    def send_heartbeat(self):
        while True:
            print(f"Heartbeat sent from {self.player_id}")
            for player in self.players:
                if player["ip"] != f'localhost:{self.port}':
                    try:
                        response = requests.get(f'http://{player["ip"]}/heartbeat')
                        if response.status_code != 200:
                            print(f"Node {player['player_id']} is down")
                            self.players = [p for p in self.players if p["player_id"] != player["player_id"]]
                            self.propagate_state()
                    except requests.exceptions.RequestException:
                        print(f"Node {player['player_id']} is down")
                        self.players = [p for p in self.players if p["player_id"] != player["player_id"]]
                        self.propagate_state()
            time.sleep(5)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python game_node.py create|join_random|join <game_id (optional)>")
        sys.exit()

    action = sys.argv[1]
    node = GameNode(port=random.randint(10000, 11000))  # Random port between 10000 and 11000
    node.run()

    if action == 'create':
        node.create_game()
    elif action == 'join_random':
        node.join_game()
    elif action == 'join' and len(sys.argv) == 3:
        game_id = sys.argv[2]
        node.join_game(game_id)
    else:
        print("Invalid command or game ID not provided for 'join'.")
        print("Usage: python game_node.py create|join_random|join <game_id (optional)>")
