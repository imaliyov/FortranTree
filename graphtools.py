#!/usr/bin/env python3

"""
Tools for graphviz parametrization
"""

import time,sys
import pygraphviz as pgv
from collections import OrderedDict

import yaml

from yaml        import load,dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

tnow = time.perf_counter

def print_meta_graph_dict():
   """
   Dict of properties of the graph that cannot be tuned with standard graphviz tools
   """

   meta_graph_dict = {
      'node_size_depth' : False,
      'size_depth_init' : 20,
      'size_depth_delta': 2,
   }

   return meta_graph_dict

def print_default_graph_param():
   """
   Default graph parameters
   Order of parameters matters
   """
   graph_param_dict = OrderedDict({
      ('graph','outputorder') : 'edgesfirst',
      ('graph','splines') : 'spline', # 'compound', 'line', 'curved', 'polyline', 'none', 'ortho', 'spline'
      ('node','shape')    : 'rectangle',
      ('graph','overlap') : 'false',
      ('graph','rankdir') : 'LR',
      ('graph','layout')  : 'dot', # 'dot', 'fdp', 'neato', 'twopi'
      ('graph','pad')     : 0.1,
      ('node','fontsize') : 14,
      ('node','style') : 'filled',
      ('node','fillcolor') : 'white',
   })

   return graph_param_dict 

def get_node_depth(graph,node,depth=0):
   """
   Get the depth of the node (an integer starting from 0) using the predecessors method.
   """

   predecessors = graph.predecessors(node)

   if len(predecessors) > 0:
      depth = get_node_depth(graph,predecessors[0],depth=depth+1)

   return depth

def get_all_graph_successors(graph,node,glob_list=None):
   """
   Get all the successors of a node recursively.
   """
   if glob_list is None:
      glob_list = []

   successors = graph.successors(node)

   glob_list += successors

   for successor in successors:
      get_all_graph_successors(graph,successor,glob_list=glob_list)

   return glob_list

def create_call_graph(graph_dict,callable_dict,root_node_name,hide_from_files=None,hide_nodes=None,allowed_connections=None,forbidden_connections=None):
   """
   Create a pygraphviz graph based on callable_dict
   """
   t1 = tnow()
   print('\nCreating graph')

   call_graph = pgv.AGraph(graph_dict,strict=False,directed=True)#.reverse()

   root_node = call_graph.get_node(root_node_name)

   #
   # Remove the nodes that are from the files in hide_from_files list
   # or if a node is in hide_nodes list
   #
   if hide_from_files is not None or hide_nodes is not None:

      for node in call_graph.nodes():

         node_in_list = node in hide_nodes

         node_from_hid_file = \
            node in callable_dict.keys() and \
            callable_dict[node].filename in hide_from_files

         if node_in_list or node_from_hid_file:
            call_graph.delete_node(node)

   #
   # Allowed connections for specific nodes
   #
   if allowed_connections is not None:
      modify_node_connections(call_graph,allowed_connections,action='keep')

   if forbidden_connections is not None:
      modify_node_connections(call_graph,forbidden_connections,action='exclude')

   #
   # Remove all the nodes that are not the successors of the root node
   #
   all_successors = get_all_graph_successors(call_graph,root_node)

   for node in call_graph.nodes():
      if node not in all_successors and node != root_node:
         call_graph.delete_node(node)

   print('Done: {:.2f} s'.format(tnow() - t1))

   return call_graph

def modify_node_connections(graph,path_to_dict,action='keep'):
   """
   Remove or to keep only some connections of specific nodes.
   """
   with open(path_to_dict ,'r') as stream:
      action_dict = load(stream,Loader=yaml.FullLoader)

   for node_name, connections in  action_dict.items():
      node = graph.get_node(node_name)

      for successor in graph.itersucc(node):

         if action == 'keep':
            if successor not in connections:
               graph.delete_node(successor)

         elif action == 'exclude':
            if successor in connections:
               graph.delete_node(successor)

         else:
            sys.exit(f'Wrong action: {action}')

def apply_node_size_depth(graph,size_init,size_delta,root_node):
   """
   Make the size of the node change as a function of depth.
   """
   
   node_list = graph.nodes()

   depth_list = [get_node_depth(graph,x) for x in node_list]

   for node_name, depth in zip(node_list,depth_list):

      fontsize = size_init - size_delta * depth

      node = graph.get_node(node_name)
      node.attr['fontsize'] = fontsize
      node.attr['width'] = 0.1
      node.attr['height'] = 0.1

def get_meta_graph_dict(graph,param_dict,root_node):
   """
   Read the entire meta dict first, then apply together with other parameters.
   This is done to provide flexibility in the order.
   """
   # Dictionary of graph properties
   meta_graph_dict = print_meta_graph_dict()
   manual_meta_graph_dict = {}

   for key,value in param_dict.items():
      # Meta parameters
      if key[0] == 'meta':

         param = key[1]
         manual_meta_graph_dict[param] = value

   meta_graph_dict = print_meta_graph_dict()

   meta_graph_dict = meta_graph_dict | manual_meta_graph_dict 

   return meta_graph_dict

def apply_meta_properties(graph,meta_graph_dict,root_node):
   """
   Properties of the graph that cannot be tuned with standard graphviz tools.
   """
   
   if meta_graph_dict['node_size_depth']:
      apply_node_size_depth(graph,meta_graph_dict['size_depth_init'],meta_graph_dict['size_depth_delta'],root_node)

def apply_graph_param(graph,param_dict,root_node):
   """
   Apply graph parameters to graph.
   Order in which parameters apply is important.
   """

   # Dictionary of graph properties
   meta_graph_dict = get_meta_graph_dict(graph,param_dict,root_node)

   for key,value in param_dict.items():
      # General graph parameters
      if key[0] == 'graph':
         param = key[1]
         if param == 'layout':
            graph.layout(prog=value)
         else:
            graph.graph_attr[param]=value

      # Node parameters
      elif key[0] == 'node':
         # General node parameters
         if len(key) == 2:
            param = key[1]
            graph.node_attr[param]=value

         # Parameters for a specific node
         elif len(key) == 3:
            node_name  = key[1]
            param = key[2]

            node = graph.get_node(node_name)
            node.attr[param] = value

         else:
            sys.exit('Error in reading graph parameters.')

      # Edge parameters
      elif key[0] == 'edge':
         # General node parameters
         if len(key) == 2:
            param = key[1]
            graph.edge_attr[param]=value

         else:
            sys.exit('Error in reading graph parameters.')

      # Meta parameters
      elif key[0] == 'meta':

         param = key[1]
         if param == 'node_size_depth':
            if meta_graph_dict['node_size_depth']:
               size_init = meta_graph_dict['size_depth_init']
               size_delta = meta_graph_dict['size_depth_delta']
               apply_node_size_depth(graph,size_init,size_delta,root_node)

      else:
         print(type(key))
         sys.exit('Error in reading graph parameters.')

def load_manual_param_dict(manual_param_path):
   """
   Load the dict of parameters from YAML for graph and nodes
   In this dict, keys are tuples, but YAML does not natively load tuples,
   they will be read as string, therefore, a conversion needed.
   """

   with open(manual_param_path ,'r') as stream:
      key_string_dict = load(stream,Loader=yaml.FullLoader)

   key_tuple_dict = OrderedDict()

   # Convert string key to tuple key
   for key_str, value in key_string_dict.items():
      key_list = key_str.replace('(','').replace(')','').replace("'","").split(',')
      key_tuple = tuple(key_list)

      key_tuple_dict[key_tuple] = value

   return key_tuple_dict

def set_graph_param(graph, root_node, manual_param_path = None):
   """
   Wrapper to apply different sets of parameters to a graph
   """

   # First, read the default parameters
   graph_param_dict = print_default_graph_param()

   # Second, read the custom graph parameters if specified
   if manual_param_path is not None:

      manual_graph_param_dict = load_manual_param_dict(manual_param_path)

      graph_param_dict = graph_param_dict | manual_graph_param_dict

   apply_graph_param(graph,graph_param_dict,root_node)

