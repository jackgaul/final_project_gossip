from flask import Flask, request, jsonify
import random
import uuid
import argparse
import json
import requests

app = Flask(__name__)

games = {}

# server_list=["http://localhost:5001","http://localhost:5002","http://localhost:5003"]
server_list = ["http://server1:5000", "http://server2:5000", "http://server3:5000"]


def share_games():
    global games
    for i in server_list:
        if i.split(":")[-1] != args.port:
            response = requests.post(i + "/share_games", json=games)


def share_deleted_game(game_id):
    global games
    for i in server_list:
        if i.split(":")[-1] != args.port:
            response = requests.post(
                i + "/share_deleted_game", json={"game_id": game_id}
            )


# add missing games to server's list to maintain consistency
@app.route("/share_games", methods=["POST"])
def share_games_route():
    global games
    data = request.get_json()
    for key in data.keys():
        # lead_val = games.get(key, None)
        if games.get(key, None):
            games[key] = data[key]
        else:
            games[key] = data[key]

    return "Updated games list"


# delete a game that exists in all servers
@app.route("/share_deleted_game", methods=["POST"])
def share_deleted_game_route():
    global games
    data = request.get_json()
    game_id_key = data["game_id"]
    print(f"printing game id key: {game_id_key}")
    if game_id_key in games:
        del games[game_id_key]
        return "Shared game deleted"
    return "Game not found"


@app.route("/create_game", methods=["POST", "GET"])
def create_game_route():
    """Create a new game and return the game ID."""
    global games
    user_ip = request.remote_addr
    real_user_ip = request.headers.get("X-Real-IP")
    game_id = str(uuid.uuid4())
    games[game_id] = real_user_ip
    share_games()
    print(
        f"Created game w/ id {game_id} and leader IP {real_user_ip}"
    )  # debug statement
    result = {
        "leader": True,
        "game_data": {"game_id": game_id, "leader_ip": real_user_ip},
    }
    return jsonify(result)


@app.route("/join_random_game", methods=["GET"])
def join_random_game_route():
    """Join a random game and return the game ID and leader's IP."""
    global games
    if not games:
        return jsonify({"error": "No games available"}), 404

    game_id = random.choice(list(games.keys()))

    leader_ip = games[game_id]
    result = {
        "leader": False,
        "game_data": {"game_id": game_id, "leader_ip": leader_ip},
    }
    return jsonify(result)


@app.route("/join_game/<game_id>", methods=["GET"])
def join_game_route(game_id):
    """Join a specific game and return the game ID and leader's IP."""
    global games
    if not games:
        return jsonify({"error": "Game does not exist"}), 404

    leader_ip = games[game_id]
    result = {
        "leader": False,
        "game_data": {"game_id": game_id, "leader_ip": leader_ip},
    }
    return jsonify(result)


@app.route("/delete_game/<game_id>", methods=["DELETE", "GET"])
def delete_game_route(game_id):
    """Delete a game by its ID."""
    global games
    if game_id in games:
        del games[game_id]
        print(f"deleted gameid {game_id}")
        share_deleted_game(game_id)
        return jsonify({"status": "success", "message": f"Game {game_id} deleted"}), 200
    else:
        return jsonify({"status": "error", "message": "Game ID not found"}), 404


@app.route("/update_state", methods=["POST"])
def update_state_route():
    global games
    data = request.get_json()
    games[data["game_id"]] = data["leader_ip"]
    print(games)
    share_games()
    return "Updated state"


# for testing purposes
@app.route("/get_games", methods=["GET"])
def get_games():
    return jsonify(games)


@app.route("/")
def hello_world():
    return "Home Screen"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple HTTP Server")
    parser.add_argument(
        "--port", "-p", type=int, default=5000, help="Port number to run the server on"
    )
    args = parser.parse_args()
    app.run(host="0.0.0.0", port=args.port, debug=True)
