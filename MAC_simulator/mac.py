import matplotlib.pyplot as plt
import logging

from node import State, get_node_by_id
from aloha_node import ALOHANode
from rts_cts_node import RTSCTSNode
from transmission import HighLevelMessage

# from scenarious import data_sink_rts_cts_25_random_max_100 as scen
from scenarious_routing import Routing_1_aloha as scen

"""
for i in range(0, N):
    new_node = n.create_new_node(i, radius, transceive_range, X, Y)
    while (n.can_add_node_without_overlap(new_node, nodes, min_distance) == False):
        new_node = n.create_new_node(i, radius, transceive_range, X, Y)

    #for i in range(0, num_of_transmissions_per_node):
    #    new_node.send_schedule.append(n.Transmission(new_node, 10, 0, n.Message("Hello", 10)))

    nodes.append(new_node)

nodes[0].send_schedule.append(n.Transmission(0, nodes[0], 7, 0, n.Message("HALLO", 7)))
"""

class Visualizer:
    def __init__(self, x: int, y: int):
        self.fig = None
        self.ax = None
        self.x = x
        self.y = y
        self.circle_parameters = {'color': 'red', 'fill': False, 'linestyle': '--'}
        self.set_up_plot()

    def set_up_plot(self):
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlabel("$x_0$")
        self.ax.set_ylabel("$x_1$")
        self.ax.set_title("Template title")
        self.fig.show()

    def draw_function(self, nodes, sim_time):
        x_coords = [node.x_pos for node in nodes]
        y_coords = [node.y_pos for node in nodes]
        node_circle_range = zip(zip(x_coords, y_coords), [node.transceive_range for node in nodes])
        colours = [node.get_color_based_on_state() for node in nodes]

        established_links = [
            (get_node_by_id(nodes, node.protocol.currently_receiving.source).x_pos,
             get_node_by_id(nodes, node.protocol.currently_receiving.source).y_pos,
             node.x_pos - get_node_by_id(nodes, node.protocol.currently_receiving.source).x_pos,
             node.y_pos - get_node_by_id(nodes, node.protocol.currently_receiving.source).y_pos)
            for node in nodes if node.state == State.Receiving]

        self.ax.clear()
        self.ax.scatter(x_coords, y_coords, clip_on=False, color=colours)

        for link in established_links:
            self.ax.arrow(*link)

        for config in node_circle_range:
            self.ax.add_patch(plt.Circle(*config, **self.circle_parameters))

        self.ax.set_xlim((0, self.x))
        self.ax.set_ylim((0, self.y))
        self.ax.set_aspect('equal')  # Ensure the circles are not distorted

        self.ax.set_title(f'Current network state {sim_time}')
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

        #plt.pause(0.1)
        #input()


def main():
    N = 2  # Number of nodes
    X = 20  # Window size
    Y = 20  # Window size

    logging.basicConfig(format='%(message)s', level=logging.INFO)

    simulation_time = 0
    active_transmissions = []

    scen.setup()

    vis = Visualizer(X, Y)

    while True:
        logging.debug("simulation_time: {}".format(simulation_time))

        scen.run(simulation_time, active_transmissions)

        vis.draw_function(scen.nodes, simulation_time)
        simulation_time += 1

if __name__ == '__main__':
    main()
