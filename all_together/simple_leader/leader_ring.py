from flask import Flask, request, jsonify
import threading
import time
import requests
import os
import random

app = Flask(__name__)

nodes_lock = threading.Lock()
game_id = 1
nodes = []


@app.route("/leader/join_game", methods=["POST"])
def join_game():
    data = request.get_json()
    if data["game_id"] != game_id:
        return jsonify({"error": "Game not found"}), 404

    with nodes_lock:
        nodes.append(data)
    return jsonify({"game_id": game_id, "nodes": nodes}), 200


@app.route("/leader/remove_player", methods=["POST"])
def remove_player():
    data = request.get_json()
    with nodes_lock:
        nodes.remove(data)
    return jsonify({"game_id": game_id, "nodes": nodes}), 200


@app.route("/player/heartbeat", methods=["POST"])
def heartbeat():
    return jsonify({"status": "OK"})


@app.route("/player/add_node", methods=["POST"])
def add_node():
    data = request.get_json()
    with nodes_lock:

        nodes.append(data)
    return jsonify({"game_id": game_id, "nodes": nodes}), 200




def heartbeat():
    global nodes
    while True:
        time.sleep(5)
        with nodes_lock:
            myindex = nodes.index(myself)
            nodeA = nodes[myindex+1%len(nodes)]
            nodeB = nodes[myindex-1%len(nodes)]
            try:
                result = requests.post(f"http://{nodeA['ip']}:{nodeA['port']}/player/heartbeat")
                if result.status_code != 200:
                    # send requst to remove node
                    result = requests.post(f"{}/leader/remove_player", json=nodeA)
                    nodes.remove(nodeA)
            except:
                nodes.remove(nodeA)

            
            try:
                result = requests.post(f"http://{nodeB['ip']}:{nodeB['port']}/player/heartbeat")
                if result.status_code != 200:
                    # send requst to remove node
                    nodes.remove(nodeB)
            except:
                nodes.remove(nodeB)

if __name__ == "__main__":

    if iamleader == True:
        nodes.append(myself)
    else:
        result = requests.post(f"{}/leader/join_game", json=myself)
        if result.status_code != 200:
            print("Failed to join game")
            exit()
        nodes = result.json()["nodes"]
    threading.Thread(target=heartbeat).start()


    app.run(host="0.0.0.0", port=port)
