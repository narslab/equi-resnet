# -*- coding: utf-8 -*-
"""
Created on Tue Apr 18 09:32:35 2023

@author: Mahsa
"""

import cenpy
import osmnx as ox
import networkx as nx
import pandas as pd

# Step 1: Calculate the closeness centrality of the nodes
pioneer_valley = ['Hampshire County, Massachusetts, USA', 'Hampden County, Massachusetts, USA', 'Franklin County, Massachusetts, USA']
graph = ox.graph_from_place(pioneer_valley, network_type='drive', simplify=False)
centrality = nx.closeness_centrality(graph)

# Step 2: Retrieve the population density, median income, and building density information
acs = cenpy.products.ACS(2017)
variables = ['B01001_001E', 'B19025A_001E', 'B01002_001E']
variables_info = acs.variables.loc[variables]

spfld_msa_demog = acs.from_msa('Springfield, MA', variables=variables)

# Step 3: Normalize the variables
spfld_msa_demog['population_density'] = spfld_msa_demog['B01001_001E'] / spfld_msa_demog.area
spfld_msa_demog['inverse_income'] = 1 / spfld_msa_demog['B19025A_001E']
spfld_msa_demog['building_density'] = spfld_msa_demog['B01002_001E'] / spfld_msa_demog['ALAND']  # assuming building density is represented by B01002_001E

# Normalize the variables
spfld_msa_demog['population_density_norm'] = spfld_msa_demog['population_density'] / spfld_msa_demog['population_density'].max()
spfld_msa_demog['inverse_income_norm'] = spfld_msa_demog['inverse_income'] / spfld_msa_demog['inverse_income'].max()
spfld_msa_demog['building_density_norm'] = spfld_msa_demog['building_density'] / spfld_msa_demog['building_density'].max()

# Step 4: Calculate the weighted closeness centrality
weighted_centrality = {}
for node, value in centrality.items():
    node_data = spfld_msa_demog.loc[spfld_msa_demog['GEOID'] == node]
    if not node_data.empty:
        weight_pop_density = node_data['population_density_norm'].values[0]
        weight_inverse_income = node_data['inverse_income_norm'].values[0]
        weight_building_density = node_data['building_density_norm'].values[0]
        
        weighted_centrality[node] = {
            'weighted_centrality_pop_density': value * weight_pop_density,
            'weighted_centrality_inverse_income': value * weight_inverse_income,
            'weighted_centrality_combined': value * (weight_pop_density + weight_inverse_income),
            'weighted_centrality_all': value * (weight_pop_density + weight_inverse_income + weight_building_density),
        }

# Convert the weighted_centrality dictionary to a DataFrame
weighted_centrality_df = pd.DataFrame.from_dict(weighted_centrality, orient='index')
weighted_centrality_df.index.name = 'osmid'

# Merge the pv_nodes DataFrame with the weighted_centrality_df DataFrame
pv_nodes, pv_streets = ox.graph_to_gdfs(graph)
pv_nodes.reset_index(inplace=True)
merged_pv_nodes = pd.merge(pv_nodes, weighted_centrality_df, on='osmid')

# Save the merged DataFrame to a CSV file
merged_pv_nodes.to_csv('closeness-centrality.csv')
