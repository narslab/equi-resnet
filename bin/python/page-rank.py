# -*- coding: utf-8 -*-
"""
Created on Tue Apr 18 20:19:26 2023

@author: Mahsa
"""

import osmnx as ox
import networkx as nx
import pandas as pd
import cenpy

# Built PV graph
pioneer_valley = ['Hampshire County, Massachusetts, USA', 'Hampden County, Massachusetts, USA', 'Franklin County, Massachusetts, USA']
graph = ox.graph_from_place(pioneer_valley, network_type='drive')
area = ox.geocode_to_gdf(pioneer_valley)

# Retrieve the population density, and median income information
acs = cenpy.products.ACS(2017)
variable = ['B01003_001E', 'B19025A_001E']
variables_info = acs.variables.loc[variable]
#spfld_msa_demog = acs.from_msa('Springfield, MA', variables=variables)
hampshire_demog = acs.from_county(county='Hampshire, MA', variables=variable)
hampden_demog = acs.from_county(county='Hampden, MA', variables=variable)
franklin_demog = acs.from_county(county='Franklin, MA', variables=variable)

# Built demographic variables variables
hampshire_demog['popden'] = 1000000*hampshire_demog['B01003_001E']/hampshire_demog.area
hampden_demog['popden'] = 1000000*hampden_demog['B01003_001E']/hampden_demog.area
franklin_demog['popden'] = 1000000*franklin_demog['B01003_001E']/franklin_demog.area
pv_demog = pd.concat([hampshire_demog, hampden_demog, franklin_demog])



pv_demog['invincome'] = 1 / pv_demog['B19025A_001E']

# Normalize the variables
pv_demog['popden_norm'] = (pv_demog['popden']-pv_demog['popden'].min()) / (pv_demog['popden'].max()-pv_demog['popden'].min())
pv_demog['invinc_norm'] = (pv_demog['invincome']-pv_demog['invincome'].min()) / (pv_demog['invincome'].max()-pv_demog['invincome'].min())

pv_nodes, pv_streets  = ox.graph_to_gdfs(graph)
digraph = nx.DiGraph(graph)
centrality = nx.pagerank(digraph)
nodes_centrality = pd.DataFrame.from_dict(centrality.items())
nodes_centrality=nodes_centrality.rename(columns={0: "osmid", 1: "rank"})
merged_pv_nodes_centrality = pd.merge(pv_nodes, nodes_centrality, on ='osmid')
merged_pv_nodes_centrality = merged_pv_nodes_centrality.to_crs(pv_demog.crs)
pv_nodes_centrality_demog_joint = merged_pv_nodes_centrality.sjoin(pv_demog)
pv_nodes_centrality_demog_joint['w_rank_pden']=pv_nodes_centrality_demog_joint['rank']*pv_nodes_centrality_demog_joint['popden_norm']
pv_nodes_centrality_demog_joint['w_rank_invinc']=pv_nodes_centrality_demog_joint['rank']*pv_nodes_centrality_demog_joint['invinc_norm']
pv_nodes_centrality_demog_joint['w_rank_both']=pv_nodes_centrality_demog_joint['rank']*(0.5*pv_nodes_centrality_demog_joint['invinc_norm']+0.5*pv_nodes_centrality_demog_joint['popden_norm'])

# Save the merged DataFrame to a CSV file
pv_nodes_centrality_demog_joint.to_file('page-rank.shp', driver='ESRI Shapefile')