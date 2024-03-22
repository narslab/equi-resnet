# -*- coding: utf-8 -*-
"""
Created on Tue Apr 18 09:53:34 2023

@author: Mahsa
"""
import cenpy
import osmnx as ox
import networkx as nx
import pandas as pd
from sklearn.neighbors import BallTree
import numpy as np

# Step 1: Generate pv graph
pioneer_valley = ['Hampshire County, Massachusetts, USA', 'Hampden County, Massachusetts, USA', 'Franklin County, Massachusetts, USA']
graph = ox.graph_from_place(pioneer_valley, network_type='drive', simplify=False)

# Step 2: Get demographic data
acs = cenpy.products.ACS(2017)

variables = ['B01001_001E', 'B19025A_001E', 'B01002_001E']
variables_info = acs.variables.loc[variables]

spfld_msa_demog = cenpy.products.ACS(2017).from_msa('Springfield, MA', variables=variables)

# Step 3: Normalize the demographic data
spfld_msa_demog['population_density_norm'] = spfld_msa_demog['B01001_001E'] / spfld_msa_demog['B01001_001E'].max()
spfld_msa_demog['inverse_income_norm'] = 1 / (spfld_msa_demog['B19025A_001E'] / spfld_msa_demog['B19025A_001E'].max())

# Step 4: Create a BallTree for nearest-neighbor search
spfld_msa_demog['centroid'] = spfld_msa_demog['geometry'].centroid
spfld_msa_demog['latitude'] = spfld_msa_demog['centroid'].apply(lambda x: x.y)
spfld_msa_demog['longitude'] = spfld_msa_demog['centroid'].apply(lambda x: x.x)
tree = BallTree(np.radians(spfld_msa_demog[['latitude', 'longitude']]), metric='haversine')


pv_nodes, pv_streets = ox.graph_to_gdfs(graph)
pv_nodes["latitude"] = np.radians(pv_nodes["y"])
pv_nodes["longitude"] = np.radians(pv_nodes["x"])

# Step 5: Find the closest demographic data for each node
indices = tree.query(pv_nodes[['latitude', 'longitude']], return_distance=False)
closest_demog_data = spfld_msa_demog.iloc[indices.flatten()]

# Step 6: Calculate the weighted eccentricity
connected_components = nx.connected_components(graph.to_undirected())
weighted_eccentricity = {}

for component in connected_components:
    subgraph = graph.subgraph(component)
    eccentricity = nx.eccentricity(subgraph.to_undirected())

    for node, value in eccentricity.items():
        node_data = closest_demog_data.loc[node]
        weight_pop_density = node_data['population_density_norm']
        weight_inverse_income = node_data['inverse_income_norm']

        weighted_eccentricity[node] = {
            'weighted_eccentricity_pop_density': value * weight_pop_density,
            'weighted_eccentricity_inverse_income': value * weight_inverse_income,
            'weighted_eccentricity_combined': value * (weight_pop_density + weight_inverse_income),
        }

weighted_eccentricity_df = pd.DataFrame.from_dict(weighted_eccentricity, orient='index')
weighted_eccentricity_df.index.name = 'osmid'

pv_nodes.reset_index(inplace=True)
merged_pv_nodes = pd.merge(pv_nodes, weighted_eccentricity_df, on='osmid', how='left')

# Save the merged DataFrame to a CSV file
merged_pv_nodes.to_csv('eccentricity.csv')
