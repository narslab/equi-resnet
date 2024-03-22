# -*- coding: utf-8 -*-
"""
Created on Tue Apr 18 20:08:54 2023

@author: Mahsa
"""


import osmnx as ox
import networkx as nx
import pandas as pd
from concurrent.futures import ProcessPoolExecutor

def compute_bc(G, weight):
    return nx.approximate_current_flow_betweenness_centrality(G, weight=weight)

# osmnx
pioneer_valley = ['Hampshire County, Massachusetts, USA', 'Hampden County, Massachusetts, USA', 'Franklin County, Massachusetts, USA']
graph = ox.graph_from_place(pioneer_valley, network_type='drive', simplify=False)

# Convert directed graph to undirected graph
graph = graph.to_undirected()
area = ox.geocode_to_gdf(pioneer_valley)

# Compute betweenness centrality using networkx in parallel
with ProcessPoolExecutor() as executor:
    future = executor.submit(compute_bc, graph, 'length')
    bc = future.result()

nodes_betweenness_centrality = pd.DataFrame.from_dict(bc, orient='index', columns=['betweenness_centrality'])
nodes_betweenness_centrality.index.name = 'osmid'

pv_nodes, pv_streets  = ox.graph_to_gdfs(graph)
pv_nodes.reset_index(inplace=True)
merged_pv_nodes = pd.merge(pv_nodes, nodes_betweenness_centrality, on='osmid')

merged_pv_nodes.to_csv('betweenness-centrality-approximated.csv')