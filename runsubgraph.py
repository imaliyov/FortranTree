#!/usr/bin/env python3

"""
Tools for graphviz parametrization
"""

import time,sys,os
import pygraphviz as pgv
from collections import OrderedDict

import graphtools, runparse

import yaml

from yaml        import load,dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

tnow = time.perf_counter

def main():

   subgraph_dict = {
      #'calc_band_structure' : None,
      #'calc_phonon_spectra' : None,
      #'calc_ephmat' : None,
      'electron_imsigma' : None,
      'calc_electron_mfp' : None,
      'transport' : None,
      'carrier_dynamics_run' : None,
   }

   #
   # 1. Build the first-neighbor graph
   #
   root_node = 'perturbo'
   root_graph = pgv.AGraph(f'{root_node}.dot')

   graph = pgv.AGraph(directed=True)

   for successor in subgraph_dict:
      graph.add_edge(root_node,successor)

   #
   # 2. Add clusters
   #

   color_list = ['red','green','blue','brown','orange','pink','violet']

   for i,subroot in enumerate(subgraph_dict):
      #break
      tmpgraph = pgv.AGraph(f'{subroot}.dot')
      subedges = tmpgraph.edges()
      subnodes = tmpgraph.nodes()
      color = color_list[i]
      subgraph = graph.add_subgraph(subnodes,name=f'cluster_{subroot}',style='setlinewidth(0)')#,color=color)
      #subgraph = graph.add_subgraph(subnodes,name=f'{subroot}',color=color)
      subgraph.add_edges_from(subedges)
   
      depth_list = [graphtools.get_node_depth(subgraph,x) for x in subnodes]

      for node_name, depth in zip(subnodes,depth_list):

         if depth > 2:
            graph.delete_node(node_name)

   #forbidden_connections = True
   forbidden_connections = False
   if forbidden_connections:
      graphtools.modify_node_connections(graph,'forbidden_connections.yml',action='exclude')

   #print(graph.string())

   #graph.layout(prog='neato')
   graphtools.set_graph_param(graph, root_node, manual_param_path = 'graph_param.yml')


   t1 = tnow()
   print('\nDrawing graph')
   graph.write('subgraphs.dot'.format(root_node))
   graph.draw('subgraphs.png')
   graph.draw('subgraphs.svg')
   print(f'Done: {tnow() - t1:.2f} s')

if __name__ == '__main__':
   main()

