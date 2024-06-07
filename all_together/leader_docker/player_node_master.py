import threading
import socket
import time
import argparse
import json
import random
import requests


# nodes = {}
nodes_lock = threading.Lock()


### Player Functions


def join_game_server(
    gossip_port, game_id, leader_address="localhost", leader_port=12345
):
    global x_pos, y_pos, myself, nodes
    # Create a UDP socket
    leader_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Server address and port
    leader_address = (leader_address, leader_port)
    print(f"attepting to join leader{leader_address}")
    # Join Game
    x = {
        "type": "join",
        "game_id": game_id,
        "gossip_port": gossip_port,
        "x_pos": x_pos,
        "y_pos": y_pos,
    }
    new_x = {
        "type": "join",
        "game_id": game_id,
        "new_node": myself,
    }
    message = json.dumps(new_x)
    # message = "This is the message. It will be sent to the server."
    try:
        leader_socket.sendto(message.encode(), leader_address)
        print("Player -> Leader: JOIN - ", message)
    except Exception as e:
        print(e)
    leader_socket.close()


def get_nodes_from_leader_once(leader_address="localhost", leader_port=12345):
    global nodes
    # Create a UDP socket
    leader_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Server address and port
    leader_address = (leader_address, leader_port)

    try:

        get_nodes = {"type": "get_nodes", "game_id": "1"}
        message = json.dumps(get_nodes)
        leader_socket.sendto(message.encode(), leader_address)
        print("Player -> Leader: GET ", message)
        # Receive response
        data, server = leader_socket.recvfrom(1024)
        with nodes_lock:
            nodes = json.loads(data.decode())

            print("Player <- Leader: ", nodes)

    except Exception as e:
        print(e)

    leader_socket.close()


def leader_election(new_leader_ip, election_dict):
    global nodes, leader_ip, started_election, election_round, game_dict
    next_node_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    old_leader_ip = election_dict["old_leader_ip"]
    leader_ip = new_leader_ip
    if election_round < 2 and election_dict["election_starter"] == myself["ip"]:
        election_round += 1
        for node in nodes["nodes"]:
            if node["ip"] != old_leader_ip and node["ip"] < new_leader_ip:
                new_leader_ip = node["ip"]
        myindex = nodes["nodes"].index(myself)
        next_node = nodes["nodes"][(myindex + 1) % len(nodes["nodes"])]
        next_node_address = (next_node["ip"], next_node["general_port"])
        if next_node["ip"] == myself["ip"]:
            print("im the only one left and am the leader...wait till someone joins")
            return
        leader_ip = new_leader_ip
        message = {
            "type": "leader_election",
            "election_starter": election_dict["election_starter"],
            "new_leader_ip": new_leader_ip,
            "old_leader_ip": election_dict["old_leader_ip"],
        }
        next_node_socket.sendto(json.dumps(message).encode(), next_node_address)
        print(f"New Leader is {new_leader_ip}")
    elif election_dict["election_starter"] != myself["ip"]:
        # started_election = True
        for node in nodes["nodes"]:
            if node["ip"] != old_leader_ip and node["ip"] < new_leader_ip:
                new_leader_ip = node["ip"]
        myindex = nodes["nodes"].index(myself)
        next_node = nodes["nodes"][(myindex + 1) % len(nodes["nodes"])]
        next_node_address = (next_node["ip"], next_node["general_port"])
        if next_node["ip"] == myself["ip"]:
            print("im the only one left and am the leader...wait till someone joins")
            return
        leader_ip = new_leader_ip
        message = {
            "type": "leader_election",
            "election_starter": election_dict["election_starter"],
            "new_leader_ip": new_leader_ip,
            "old_leader_ip": election_dict["old_leader_ip"],
        }
        next_node_socket.sendto(json.dumps(message).encode(), next_node_address)
        print(f"New Leader is {new_leader_ip}")
    else:
        print(f"Leader {leader_ip} has been elected")
        url = f"http://{load_ip}:80/update_state"
        data = {
            "game_id": game_dict["game_id"],
            "leader_ip": leader_ip,
        }
        response = requests.post(url=url, json=data)
        started_election = False
        election_round = 0

    next_node_socket.close()


def get_nodes_from_leader(leader_address="localhost", leader_port=12345):
    global nodes, leader_ip, game_dict, nodes_pos
    # Create a UDP socket
    leader_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    leader_socket.settimeout(2)

    # Server address and port
    leader_address = (leader_address, leader_port)

    while True:
        leader_address = (leader_ip, leader_port)
        if leader_ip == myself["ip"]:
            continue
        else:

            try:

                get_nodes = {
                    "type": "get_nodes",
                    "game_id": game_dict["game_id"],
                    "leader_ip": leader_ip,
                }
                message = json.dumps(get_nodes)
                leader_socket.sendto(message.encode(), leader_address)
                print("Player -> Leader: GET ", message)
                # Receive response
                data, server = leader_socket.recvfrom(1024)
                with nodes_lock:
                    nodes = json.loads(data.decode())

                    print("Player <- Leader: ", nodes)

            except socket.timeout as e:

                # leader_election(new_leader_ip=myself["ip"])
                # print(e.errno)
                print(e)
        node_ips = nodes_pos.keys()
        for node in nodes["nodes"]:
            if node["ip"] not in node_ips:
                nodes_pos[node["ip"]] = [0, 0]

        time.sleep(5)


def gossip_recieve_state_info():
    global nodes_pos
    neighbors = {}
    gossip_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    gossip_address = ("0.0.0.0", myself["gossip_port"])
    gossip_socket.bind(gossip_address)
    while True:
        data, address = gossip_socket.recvfrom(1024)
        data = json.loads(data.decode())
        # neighbors[address] = data
        with nodes_lock:
            for key in data.keys():
                if key != myself["ip"]:
                    nodes_pos[key] = data[key]
            # nodes = data
        print(f"Gossip - Received:  {data}")
        # print(nodes)


def gossip_share_state_info():
    # Send out information to a random neighbor
    global nodes, nodes_pos
    gossip_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    time.sleep(4)
    # randomly choose a value from dictionary nodes

    while True:
        with nodes_lock:
            node = random.choice(nodes["nodes"])
            if node["ip"] == myself["ip"]:
                pass
            # while node["ip"] == myself["ip"]:
            #    node = random.choice(nodes["nodes"])
            else:
                gossip_address = (node["ip"], node["gossip_port"])
                print(f"Gossip destinatiin: {gossip_address}")

                # gossip_socket.sendto(json.dumps(message).encode(), gossip_address)
                gossip_socket.sendto(json.dumps(nodes_pos).encode(), gossip_address)

                print(f"Gossip - Sent:  from {myself['ip']} to {node['ip']}")
        time.sleep(1)


def join_game(load_url):
    # server_url = random.choice(self.server_urls)
    server_url = load_url
    url = f"http://{server_url}:80/join_random_game"
    print(f"joining game at {server_url}")

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        game_id = data["game_data"]["game_id"]
        leader_ip = data["game_data"]["leader_ip"]
        is_leader = False

        print(
            f"Joined {'random' if game_id is None else ''} game with ID: {game_id}. Leader IP: {leader_ip}."
        )
        return {"game_id": game_id, "leader_ip": leader_ip}
    else:
        action = "any game" if game_id is None else f"game {game_id}"
        print(f"Failed to join {action}.")
        return False


### LEader Functions


def node_initiate(data, node_address, game_info):
    # node_socket.settimeout(2)
    global nodes

    if data["game_id"] == game_info["game_id"]:
        # node_dict = {"address": node_address, "gossip_port": data["gossip_port"]}
        node_dict = data["new_node"]

        with nodes_lock:
            nodes["nodes"].append(node_dict)
        print(f"Node {node_address} joined the game")
    else:
        print(f"Node {node_address} tried to join the wrong game")


def get_nodes(data, node_address, leader_socket):
    global nodes
    # node_dict = {"type": "nodes", "nodes": nodes}

    json_data = json.dumps(nodes)
    # print(json_data)
    # print(node_dict)

    print(f"Sending nodes to {node_address}")
    leader_socket.sendto(json_data.encode("utf-8"), node_address)
    return nodes


def remove_node(data_dict, node_address):
    global nodes

    dead_node = data_dict["node"]
    dead_node_message = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    with nodes_lock:
        for node in nodes["nodes"]:
            if node["address"] == dead_node["address"]:
                nodes["nodes"].remove(node)
                print(f"Node {dead_node['ip']} removed")

                break
    dead_node_message.close()


def heartbeat_inbound(inbound_hb_port):

    inbound_hb = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    inbound_hb.bind(("0.0.0.0", inbound_hb_port))
    while True:
        data, address = inbound_hb.recvfrom(1024)
        data_dict = json.loads(data.decode("utf-8"))
        if data_dict["type"] == "heartbeat":
            print(f"HeartBeat -- Node {address} sent me heartbeat")
            response = {
                "type": "heartbeat",
                "message": "OK",
            }
            inbound_hb.sendto(json.dumps(response).encode("utf-8"), address)
        else:
            print(f"Unknown message from {address}")


def udp_message_handle(data, node_address, general_socket, game_info):
    global nodes
    data_dict = json.loads(data.decode("utf-8"))
    # print(data_dict)
    # print(f"Connection from {node_address}")
    if data_dict["type"] == "join":
        node_initiate(data_dict, node_address, game_info)
    elif data_dict["type"] == "state":
        print(f"Node {node_address} sent state {data_dict}")
    elif data_dict["type"] == "get_nodes":
        get_nodes(data_dict, node_address, general_socket)
        print(f"Node {node_address} requested nodes")
    elif data_dict["type"] == "remove_node":
        remove_node(data_dict, node_address)
        # print(f"Node {node_address} removed")
    elif data_dict["type"] == "leader_election":
        print(f"Leader Election -- New Leader is {data_dict['new_leader_ip']}")
        leader_election(data_dict["new_leader_ip"], data_dict)
    # elif data_dict["type"] == "heartbeat":
    #    heartbeat_response(data_dict, node_address)

    else:
        print(f"Unknown message from {node_address}")


def periodic_heartbeat_player_propagate():
    global nodes, started_election, leader_ip
    outbound_hb_port = 22277
    next_node_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    next_node_socket.bind(("0.0.0.0", outbound_hb_port))
    next_node_socket.settimeout(1)

    while True:
        time.sleep(5)
        with nodes_lock:

            if myself in nodes["nodes"]:

                myindex = nodes["nodes"].index(myself)
                next_node = nodes["nodes"][(myindex + 1) % len(nodes["nodes"])]
                try:
                    message = {
                        "type": "heartbeat",
                        "message": f'Heartbeat from {myself["address"]}',
                    }
                    print(
                        f'HeartBeat -- Sending heartbeat to {next_node["ip"]}:{next_node["inbound_hb"]}'
                    )

                    next_node_socket.sendto(
                        json.dumps(message).encode(),
                        (next_node["ip"], next_node["inbound_hb"]),
                    )

                    try:
                        response, address = next_node_socket.recvfrom(1024)
                        response_dict = json.loads(response.decode())
                        print(
                            f'HeartBeat -- Received heartbeat from {address} with message: {response_dict["message"]}'
                        )

                    except:
                        if next_node["ip"] == leader_ip:
                            print(
                                f"Leader did not respond... initiating leader election"
                            )
                            # started_election = True
                            nodes["nodes"].remove(next_node)
                            message = {
                                "type": "leader_election",
                                "election_starter": myself["ip"],
                                "new_leader_ip": myself["ip"],
                                "old_leader_ip": leader_ip,
                            }
                            leader_election(
                                new_leader_ip=myself["ip"], election_dict=message
                            )
                        else:
                            print(
                                f"Node{next_node['address']} did not respond... deleting"
                            )
                            nodes["nodes"].remove(next_node)
                            message = {
                                "type": "remove_node",
                                "node": next_node,
                            }
                            next_node_socket.sendto(
                                json.dumps(message).encode(),
                                (leader_ip, 12345),
                            )

                            continue
                except Exception as e:
                    print("error sending heartbeat")
                    print(e)


def node_accept(general_socket, game_info, gossip_port):
    global nodes
    node_threads = []

    print("Waiting for nodes to join")

    while True:
        data, node_address = general_socket.recvfrom(1024)
        # print(f"Connection from {node_address}")
        node_threads.append(
            threading.Thread(
                target=udp_message_handle,
                args=(
                    data,
                    node_address,
                    general_socket,
                    game_info,
                ),
            )
        )
        node_threads[-1].start()


def create_game(load_url):
    # global game_id
    # server_url = random.choice(self.server_urls)
    global nodes

    server_url = f"http://{load_url}:80/create_game"

    response = requests.post(server_url)
    if response.status_code == 200:
        data = response.json()
        game_id = data["game_data"]["game_id"]
        leader_ip = data["game_data"]["leader_ip"]
        is_leader = True

        # leader function

        print(f"Game created with ID: {game_id}. I am the leader with IP: {leader_ip}.")
        return {"game_id": game_id, "leader_ip": leader_ip}
    else:
        print("Failed to create game")
        return False


def change_position():
    global nodes_pos, myself
    while True:

        nodes_pos[myself["ip"]][0] = nodes_pos[myself["ip"]][0] + random.randint(-5, 5)
        nodes_pos[myself["ip"]][1] = nodes_pos[myself["ip"]][1] + random.randint(-5, 5)
        print(f"New Position: {nodes_pos[myself['ip']]}")
        time.sleep(5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple HTTP Server")
    parser.add_argument(
        "--port", "-p", type=int, default=6001, help="Port number to run the server on"
    )
    parser.add_argument(
        "--general_port", "-g", type=int, default=12345, help="General Port number"
    )

    parser.add_argument(
        "--inbound_hb", "-hb", type=int, default=12346, help="Inbound HB Port number"
    )

    parser.add_argument(
        "--load_address",
        "-l",
        type=str,
        default="localhost",
        help="Load Balancer Address",
    )
    parser.add_argument(
        "--is_leader", "-i", type=bool, default=False, help="Is this node the leader?"
    )
    parser.add_argument(
        "--sleep_time", "-s", type=int, default=5, help="Time to sleep before joining"
    )
    parser.add_argument(
        "--my_ip", "-m", type=str, default="localhost", help="My IP Address"
    )

    args = parser.parse_args()

    nodes = {"type": "nodes", "nodes": []}
    # {"type": "nodes",
    #   "nodes": [{"address": node_address, "gossip_port": args.port, "general_port": args.general_port "x_pos": 0,"y_pos": 0,}]}
    x_pos = 0
    y_pos = 0
    node_address = [args.my_ip, args.general_port]
    myself = {
        "address": node_address,
        "ip": args.my_ip,
        "gossip_port": args.port,
        "general_port": args.general_port,
        "inbound_hb": args.inbound_hb,
    }
    nodes_pos = {}
    has_voted_leader = False
    started_election = False
    vote_id = 0
    election_round = 0
    load_ip = args.load_address

    threading.Thread(target=heartbeat_inbound, args=(args.inbound_hb,)).start()

    if not args.is_leader:
        time.sleep(args.sleep_time)
        print(f"Running Player Node...")

        game_dict = join_game(args.load_address)

        leader_address = game_dict["leader_ip"]
        leader_port = args.general_port
        leader_ip = game_dict["leader_ip"]

        join_game_server(args.port, game_dict["game_id"], leader_address, leader_port)
        get_nodes_from_leader_once(leader_address, leader_port)
        nodes_from_leader_thread = threading.Thread(
            target=get_nodes_from_leader, args=(leader_address, leader_port)
        ).start()

        threading.Thread(target=periodic_heartbeat_player_propagate).start()
        threading.Thread(target=gossip_recieve_state_info).start()
        threading.Thread(target=gossip_share_state_info).start()
        threading.Thread(target=change_position).start()
        general_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        general_socket.bind(("0.0.0.0", args.general_port))
        node_accept(
            general_socket=general_socket, game_info=game_dict, gossip_port=args.port
        )

    else:
        # load_url = f"http://{args.load_address}:80"
        print(f"Running Leader Node...")

        result = create_game(args.load_address)
        if not result:
            print("Failed to create game")
            exit()

        nodes["nodes"].append(myself)
        leader_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        leader_socket.bind(("0.0.0.0", args.general_port))

        threading.Thread(target=periodic_heartbeat_player_propagate).start()
        # threading.Thread(target=gossip_recieve_state_info, args=(args.port,)).start()
        # threading.Thread(target=gossip_share_state_info, args=(args.port,)).start()

        node_accept(
            general_socket=leader_socket, game_info=result, gossip_port=args.port
        )

    # nodes_from_leader_thread.join()
