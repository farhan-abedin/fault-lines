import matplotlib.pyplot as plt
import networkx as nx
import math

rows, cols = 6, 6
G = nx.grid_2d_graph(rows, cols)

pos = {(i, j): (j, -i) for i, j in G.nodes()}

plt.figure(figsize=(8, 8))
G.clear_edges()
numberToNode = {}
for node in range(rows * cols):
  numberToNode[node] = (node // rows, node % rows)
nTN = numberToNode
G.add_edges_from([(nTN[0], nTN[6])])
#G.add_edges_from([(nTN[1], nTN[2])])
#G.add_edges_from([(nTN[3], nTN[4])])
#G.add_edges_from([(nTN[5], nTN[11])])
#G.add_edges_from([(nTN[7], nTN[13]), (nTN[8], nTN[14]), (nTN[9], nTN[10])])
pairs = [[7,8], [9,10], [13,14], [12,18], [19,20], [21,22], [15,16], [17,23], [24,25], [26,27], [30,31], [32,33], [28,34], [29,35]]
for pair in pairs:
  #G.add_edge(nTN[pair[0]], nTN[pair[1]])
  continue


nx.draw_networkx_nodes(G, pos, node_color='black', node_size=100)
nx.draw_networkx_edges(G, pos)