# Distributed Systems Project: Multiplayer Game Infrastructure

## Project Overview
This project focuses on creating the underlying infrastructure required to build a distributed multiplayer game. The system incorporates key distributed systems concepts such as leader election, redundancy, load balancing, gossip protocol, and state dissemination.

## System Architecture
The architecture consists of the following components:

1. **Web Server (Load Balancer):** An NGINX server that balances the load and directs new player requests to one of the three game brokers.
2. **Game Brokers:** Three game brokers maintain a list of ongoing games, mapping game IDs to the leader's IP address.
3. **Players:** Players connect to the game through the leader, with the game orchestrated in a ring fashion.

## Key Components and Protocols

### Game Brokers
- **Role:** Manage game lists with game IDs and leader IP addresses.
- **Update:** Keep the game brokers updated with the new leader information upon leader election.

### Heartbeat Protocol
- **Function:** Detects node failures.
- **Process:** Nodes inform the leader about any failed nodes and detect if the leader has failed.
- **Leader Election:** Triggered if the leader fails, choosing the new leader based on the lowest IP address.

### Leader Election
- **Trigger:** Initiated upon detection of leader failure.
- **Criteria:** New leader is chosen based on the lowest IP address.
- **Update:** Game brokers are updated with the new leader information.

### Gossip Protocol
- **Purpose:** Share the state of the game world (e.g., XY coordinates) among nodes.
- **Mechanism:** Nodes randomly select peers to share their state, ensuring consistent state dissemination.

## Conclusion
This project successfully implements the necessary infrastructure to support any distributed multiplayer game. By utilizing distributed systems concepts like heartbeat protocols, leader election, and gossip protocols, the system ensures robust and efficient management of game state and player interactions.

## Setup and Installation
1. **Clone the Repository:**
    ```bash
    git clone https://github.com/jackgaul/final_project_gossip.git
    cd final_project_gossip/all_together
    ```

2. **Run the Load Balancer:**
    ```bash
    cd gamebroker
    docker-compose up -d --build
    ```

4. **Run the Game Brokers:**
    ```bash
    cd leader_docker
    docker-compose up -d --build
    ```



## Usage
- New players reach out to the load balancer to join a game.
- Game brokers handle the assignment of players to game leaders.
- The system ensures continuous monitoring and updating of game states through the implemented protocols.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements
Special thanks to Professor Moazzeni for the knowledge and resources provided throughout the project.

## Division of Work
- Jack Gaul: Gossip Protocol Implementation
- Patrick Lee: Replication and Concurrency Control Implementation
- Hardik Vora: Leader-Election Implementation

## To run
1. run: cd all_together/gamebroker
2. run: docker-compose up -d --build
