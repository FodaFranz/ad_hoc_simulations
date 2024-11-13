import logging
import csv
import random
from node import Node, get_node_by_id
from dataclasses import dataclass
import numpy as np

from protocols import DSDVRoutingProtocol
from transmission import HighLevelMessage, Message, MessageType
from rts_cts_node import RTSCTSNode
from aloha_node import ALOHANode

np.random.seed(42)


@dataclass
class PlannedTransmission:
    transmit_time: int
    message: HighLevelMessage
    source_node_id: int


@dataclass
class Scenario:
    name: str
    radius: float
    transceive_range: float
    nodes: list[Node]
    send_schedule: list[PlannedTransmission]
    movement: bool

    def get_collision_count(self):
        cnt = 0
        #for node in self.nodes:
        cnt += self.nodes[0].collision_counter

        return cnt


    def return_result(self):
        return (self.established_time, self.resulting_time, self.hops, self.name)

    def report(self):
        with open(f"./routing.csv", mode='a+', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(self.return_result())


    def setup(self):
        self.hops = 0
        self.established_time = -1
        self.resulting_time = -1
        for node in self.nodes:
            node.routing_protocol = DSDVRoutingProtocol(node.id)
            node.add_neighbors(self.nodes)

    def get_node_by_id(self, id: int) -> Node | None:
        for node in self.nodes:
            if node.id == id:
                return node

        return None


    def send_messages(self, simulation_time: int):
        for transmission in self.send_schedule:
            if simulation_time == transmission.transmit_time:
                self.get_node_by_id(transmission.source_node_id).routing_protocol.send(transmission.message)


    def run(self, simulation_time: int, active_transmissions: list[Message]):
        self.send_messages(simulation_time)

        if simulation_time >= 10_000:
            self.report()
            return self.return_result()

        source_node = self.nodes[-2]
        target_node = self.nodes[-1]

        if target_node.id in source_node.routing_protocol.table and self.established_time == -1:
            self.established_time = simulation_time

        if self.movement:
            for node in self.nodes:
                node.move()
                node.add_neighbors(self.nodes)

        for node in self.nodes:
            node.execute_state_machine(simulation_time, active_transmissions)

        for node in self.nodes:
            msg = node.receive()
            if msg:
                # if msg.get_type() == MessageType.Data:
                if 'Hello' in msg.content:
                    self.hops += 1
                    if msg.route_target == msg.target:
                        self.resulting_time = simulation_time
                        self.report()
                        return self.return_result()

                if 'cts' in msg.content:
                    logging.info("Node {} received: {}".format(node.id, msg))
                reply = node.routing_protocol.reply(msg, node.get_packet_travel_time(get_node_by_id(self.nodes, msg.source)))
            else:
                reply = node.routing_protocol.tick()
            if reply:
                logging.debug("Node {} wants to send: {}".format(node.id, reply))
                node.send(reply)


def create_scenario(node_class, n: int, movement: bool = False, transmit_range=3, name=None):
    scenario = Scenario(
        f"Routing_{name}",
        0.25,
        3,
        [node_class(i, 0.25, transmit_range, np.random.uniform(0, 10), np.random.uniform(0, 10)) for i in range(1, n)] +
        [node_class(0, 0.25, transmit_range, 0, 0),  # source
         node_class(100, 0.25, transmit_range, 10, 10)],  # sink

        [
            PlannedTransmission(2, HighLevelMessage(100, "Hello message", 5), 0)
        ],
        movement
    )

    return scenario



