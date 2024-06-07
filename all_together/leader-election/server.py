from flask import Flask, request, jsonify
import threading
import time
import requests
import os
import random

app = Flask(__name__)

node_id = os.getenv("NODE_ID", "server1")  # Default to server1 if NODE_ID is not set
port = os.getenv("PORT", "5000")

servers = {
    "server1": "http://server1:5000",
    "server2": "http://server2:5000",
    "server3": "http://server3:5000",
}

games = {}
games_lock = threading.Lock()


class Node:
    def __init__(self, player_id, role="player"):
        self.player_id = player_id
        self.role = role
        self.alive = True

    def to_dict(self):
        return {"player_id": self.player_id, "role": self.role, "alive": self.alive}

    @classmethod
    def from_dict(cls, data):
        node = cls(data["player_id"], data["role"])
        node.alive = data["alive"]
        return node


def generate_game_id():
    return str(random.randint(1000, 9999))


def propagate_state():
    print(f"Propagating state from {node_id}: {games}")
    for server_id, server_url in servers.items():
        if server_id != node_id:  # Avoid propagating to self
            try:
                print(f"Sending state to {server_url}")
                response = requests.post(f"{server_url}/update_state", json=games)  #
                if response.status_code == 204:
                    print(f"State successfully propagated to {server_url}")
                else:
                    print(
                        f"Failed to propagate state to {server_url}: {response.status_code}"
                    )
            except Exception as e:
                print(f"Failed to propagate state to {server_url}: {e}")


def merge_state(new_state):
    """Merge the received game state with the current state."""
    with games_lock:
        for game_id, state in new_state.items():
            if game_id not in games:
                games[game_id] = state
            else:
                for player in state["players"]:
                    existing_player = next(
                        (
                            p
                            for p in games[game_id]["players"]
                            if p["player_id"] == player["player_id"]
                        ),
                        None,
                    )
                    if existing_player:
                        existing_player.update(player)
                    else:
                        games[game_id]["players"].append(player)
                games[game_id]["host"] = state["host"]
                games[game_id]["leader"] = state["leader"]
                games[game_id]["sub_leaders"] = state["sub_leaders"]
    print(f"State after merge at {node_id}: {games}")


def initiate_ring_election(game_id):
    """Initiate the ring election process within a game room."""
    print(f"Initiating ring election for game {game_id}")
    game = games.get(game_id)
    if not game:
        print(f"Game {game_id} not found at {node_id}")
        return
    candidates = [player["player_id"] for player in game["players"] if player["alive"]]
    message = {"game_id": game_id, "candidates": candidates, "current_max": None}
    send_message_to_next_node("/election_message", message, candidates[0])


def send_message_to_next_node(endpoint, message, current_node):
    """Send a message to the next node in the ring."""
    next_node = get_next_node(current_node, message["candidates"])
    if next_node:
        try:
            response = requests.post(servers[next_node] + endpoint, json=message)
            if response.status_code == 200:
                print(f"Message successfully sent to {next_node} from {node_id}")
            else:
                print(
                    f"Failed to send message to {next_node} from {node_id}: {response.status_code}"
                )
        except requests.exceptions.RequestException as e:
            print(f"Failed to send message to {next_node} from {node_id}: {e}")


def get_next_node(current_node, candidates):
    """Determine the next node in the ring."""
    current_index = candidates.index(current_node)
    next_index = (current_index + 1) % len(candidates)
    return candidates[next_index]


def remove_player_from_game(game, player):
    try:
        node_to_remove = next(
            (node for node in game["players"] if node["player_id"] == player), None
        )
        if node_to_remove:
            game["players"].remove(node_to_remove)
            print(f"Player {player} removed from players list")
            return node_to_remove
        else:
            print(f"Player {player} not found in game")
            return None
    except Exception as e:
        print(f"Error in remove_player_from_game: {e}")
        raise e


def update_sub_leaders(game):
    try:
        game["sub_leaders"] = [
            p["player_id"] for p in game["players"] if p["role"] == "sub_leader"
        ]
        while (
            len(game["sub_leaders"]) < 2
            and len(game["players"]) > len(game["sub_leaders"]) + 1
        ):
            potential_sub_leader = next(
                (p for p in game["players"] if p["role"] == "player"), None
            )
            if potential_sub_leader:
                potential_sub_leader["role"] = "sub_leader"
                game["sub_leaders"].append(potential_sub_leader["player_id"])
    except Exception as e:
        print(f"Error in update_sub_leaders: {e}")
        raise e


def handle_leader_removal(game, player):
    try:
        if player == game["leader"]:
            print(f"Leader {player} removed from game")
            if game["sub_leaders"]:
                new_leader = game["sub_leaders"].pop(
                    0
                )  # Promote the first sub-leader to leader
                game["host"] = game["leader"] = new_leader
                for p in game["players"]:
                    if p["player_id"] == new_leader:
                        p["role"] = "leader"
                        break
            elif game["players"]:
                new_leader = game["players"][0]["player_id"]
                game["host"] = game["leader"] = new_leader
                game["players"][0]["role"] = "leader"
            else:
                game["host"] = game["leader"] = None
    except Exception as e:
        print(f"Error in handle_leader_removal: {e}")
        raise e


@app.route("/remove_player", methods=["POST"])
def remove_player():
    """Remove a player from the game, handle leader and sub-leader reassignments."""
    print(f"{node_id} received request to remove player")
    data = request.json
    game_id = data["game_id"]
    player = data["player"]
    with games_lock:
        if game_id in games:
            game = games[game_id]
            print(f"Current game state before removing player: {game}")
            node_to_remove = remove_player_from_game(game, player)
            if node_to_remove:
                handle_leader_removal(game, player)
                update_sub_leaders(game)
                propagate_state()
                print(f"Updated game state after removal: {game}")
                return (
                    jsonify(
                        {
                            "status": "player removed",
                            "new_host": game["host"],
                            "new_leader": game["leader"],
                        }
                    ),
                    200,
                )
            else:
                return jsonify({"error": "Player not found"}), 404
        else:
            print(f"Game ID {game_id} not found at {node_id}")
            return jsonify({"error": "Game not found"}), 404


@app.route("/update_state", methods=["POST"])  # Real endpoint
def update_state():
    """Update the game state based on the received data."""
    new_state = request.json
    print(f"{node_id} received state update: {new_state}")
    merge_state(new_state)
    return "", 204


@app.route("/election_message", methods=["POST"])
def election_message():
    message = request.json
    game_id = message["game_id"]
    candidates = message["candidates"]
    current_max = message["current_max"]
    print(f"{node_id} received election message: {message}")
    with games_lock:
        game = games.get(game_id)
        if not game:
            return jsonify({"status": "game not found"}), 404
        if current_max is None or candidates[0] > current_max:
            message["current_max"] = candidates[0]
        next_node = get_next_node(node_id, candidates)
        if next_node == node_id:  # Election completed
            new_leader = message["current_max"]
            leader_node = next(
                (node for node in game["players"] if node["player_id"] == new_leader),
                None,
            )
            if leader_node:
                leader_node["role"] = "leader"
                game["leader"] = new_leader
                propagate_state()
            return jsonify({"status": "leader elected", "leader": new_leader})
        else:
            send_message_to_next_node("/election_message", message, next_node)
    return jsonify({"status": "message received"})


@app.route("/heartbeat", methods=["GET"])
def heartbeat_response():
    return jsonify({"status": "alive"})


def sync_state():
    while True:
        time.sleep(5)  # Sync every 5 seconds
        for server_id, server_url in servers.items():
            if server_id != node_id:  # Avoid syncing with self
                try:
                    print(f"Syncing state from {server_url}")
                    response = requests.get(f"{server_url}/get_games")
                    if response.status_code == 200:
                        other_state = response.json()
                        print(
                            f"{node_id} received state from {server_url}: {other_state}"
                        )
                        merge_state(other_state)
                    else:
                        print(
                            f"Failed to get state from {server_url}: {response.status_code}"
                        )
                except Exception as e:
                    print(f"Failed to sync with {server_url} at {node_id}: {e}")


def heartbeat_check():
    while True:
        time.sleep(5)  # Check every 5 seconds
        for game_id, game in list(games.items()):
            for player_node in game["players"]:
                if player_node["role"] in ["leader", "sub_leader"]:
                    # Simulate heartbeat check
                    try:
                        response = requests.get(
                            f'http://{player_node["player_id"]}/heartbeat'
                        )
                        if response.status_code != 200:
                            raise Exception("Node not responding")
                    except Exception as e:
                        print(f"Heartbeat failed for {player_node['player_id']}: {e}")
                        player_node["alive"] = False
                        if player_node["role"] == "leader":
                            initiate_ring_election(game_id)


if __name__ == "__main__":
    threading.Thread(target=sync_state, daemon=True).start()
    threading.Thread(target=heartbeat_check, daemon=True).start()
    app.run(host="0.0.0.0", port=port)
