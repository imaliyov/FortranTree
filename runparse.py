#!/usr/bin/env python3

"""
Run the code parsing and create the subroutine/module interactive graphs
"""

import os, sys, shutil
import pygraphviz as pgv
import textwrap
import argparse

import htmltools, graphtools

from parsetools import  get_parse_tree_dict, \
                        get_global_node_dict, \
                        print_object_attributes, \
                        MySubrOrFunc, MyInterface

from fparser.two.utils import walk

from fparser.two.parser import ParserFactory
from fparser.two import Fortran2003
from datetime import datetime
import time

import pickle

from yaml import load, dump
try:
   from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
   from yaml import Loader, Dumper

#tnow = datetime.now
#tnow = time.time
tnow = time.perf_counter
start_time = tnow()

def str_examples():
   return """
Usage examples:
   
   runparse.py -p ../../pert-src        Parse the perturbo.x source code and build the subroutine tree
   runparse.py -p ../../qe2pert-src     Parse the qe2pert.x source code and build the subroutine tree
   
   runparse.py -p ../../pert-src -m     Parse the perturbo.x source code and build the subroutine and module trees
   """

def create_callable_dict(path,source_file_list):
   """
   Create a dictionary of the calls (functions, subroutines, and interfaces) 
   from all the files from source_file_list
   """
   #
   # fparser provides a parse tree per file.
   # So here, we run over all the files of the source directory and create a dictionary of parse trees
   #
   parse_tree_dict = get_parse_tree_dict(path,source_file_list)

   #
   # Get the dictionary of MyNode instances 
   # for Fortran "callables": subroutines, functions, and interfaces
   #
   types_tuple = (Fortran2003.Subroutine_Stmt,Fortran2003.Function_Stmt,Fortran2003.Interface_Stmt, Fortran2003.Program_Stmt)
   callable_dict = get_global_node_dict(parse_tree_dict,types_tuple,debug=False)

   function_list = [ x.name for x in callable_dict.values() if x.fparser_type == Fortran2003.Function_Stmt]

   #
   # Once the function list is known, add the function calls to the .calls attribute
   # It was not possible to do before the function list is known since the Fortran syntax 
   # for a function and an array is the same
   #

   for obj in callable_dict.values():
      if isinstance(obj,MySubrOrFunc):
         # append the function calls of obj
         obj.append_func_calls(function_list)

   #
   # Once the callable_dict is filled entirely for functions and subroutines, we can update
   # the interfaces attributes to encorporate all the calls, etc. of the module procedures 
   # that they contain
   #
   for obj in callable_dict.values():
      if isinstance(obj,MyInterface):
         obj.update_interface_attrs(callable_dict)

   return callable_dict

def create_callable_graph_dict(callable_dict):
   """
   Using the callable_dict, create a dict that can be processed by pygraphviz
   """
   t1 = tnow()
   print('\nCreating graph dictionary')

   graph_dict = {}

   for name, obj in callable_dict.items():

      tmp_call_dict = {}
      for call in obj.calls: 
         tmp_call_dict[call] = None

      graph_dict[name] = tmp_call_dict

   print('Done: {:.2f} s'.format(tnow() - t1))

   return graph_dict

def get_sorted_node_list(graph):
   """
   Sort the graph nodes according to their depth in the graph and then alphabetic oreder
   """

   node_list = graph.nodes()

   node_list = sorted(node_list, key = lambda x: (graphtools.get_node_depth(graph,x), x ))

   return node_list

def get_node_type_dict(callable_dict, node_list):
   
   node_type_dict = {}

   for node in node_list:
      if node in callable_dict.keys():
         ntype = callable_dict[node].type
         node_type_dict[node] = ntype
      else:
         node_type_dict[node] = 'External'

   return node_type_dict

def get_prefix_node_list(callable_dict, node_list):
   
   prefix_node_list = []

   for node in node_list:
      if node in callable_dict.keys():
         ntype = callable_dict[node].type
         prefix_node_list.append(ntype+'-'+node)
      else:
         prefix_node_list.append('External'+'-'+node)

   return prefix_node_list

def create_graph_for_node(root_node,graph_dict,callable_dict,args,hide_nodes,img_dir,svg_path):
   """
   Callable graph creation (including HTML) for a given root node
   """

   call_graph = graphtools.create_call_graph(graph_dict,callable_dict,root_node,hide_from_files=args.hide_from_files,hide_nodes=hide_nodes,allowed_connections=args.allowed_connections, forbidden_connections = args.forbidden_connections )

   graphtools.set_graph_param(call_graph, root_node, manual_param_path = args.param_dict)

   t1 = tnow()
   print('\nDrawing graph')
   call_graph.write('{:}.dot'.format(root_node))
   call_graph.draw(svg_path)
   call_graph.draw('{:}.png'.format(root_node))
   print(f'Done: {tnow() - t1:.2f} s')

   sorted_node_list = get_sorted_node_list(call_graph)
   prefix_node_list = get_prefix_node_list(callable_dict,sorted_node_list)
   node_type_dict = get_node_type_dict(callable_dict,sorted_node_list)

   #
   # Dump HTML
   #
   t1 = tnow()
   print('\nCreating HTML file')

   htmltools.create_html(callable_dict, svg_path, prefix_node_list, node_type_dict, args.path, root_node)

   print('Done: {:.2f} s'.format(tnow() - t1))

def parse_arguments():
   """
   Parse command line arguments
   """ 

   help_description = textwrap.dedent(str_examples())

   cmd_parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,description=help_description)

   cmd_parser.add_argument('-p','--path',help='Path to the source code',default=None)
   cmd_parser.add_argument('-r','--root-node-list',help='List of root node names. The call tree will be ploted from the root nodes of the list.', nargs='*', type=str, required=True)
   cmd_parser.add_argument('-y','--hide-from-yaml',help='Hide the callables that are in specific files or select them by name, contained in the yaml file. The file must have the dictionary structure with the following keys: files: [List of files] and/or nodes: [List of nodes].',type=str,required = False,default=None)
   
   cmd_parser.add_argument('--exclude-files',help='List of file to exclude from parsing',nargs='*',required = False,default=[])
   cmd_parser.add_argument('--hide-from-files',help='List of files. If a suboutine/function is implemented in one of these files, it will be hidden in the graph.',nargs='*',required = False,default=[])
   cmd_parser.add_argument('--hide-nodes',help='List of nodes to hide in the graph',nargs='*',required = False,default=[])

   cmd_parser.add_argument('--param-dict',help='YAML file contatining the graph and node parameters that will overwrite the default ones. ',type=str,required = False,default=None)
   cmd_parser.add_argument('--allowed-connections',help='YAML file contatining the list of allowed graph connections for specific nodes.',type=str,required = False,default=None)
   cmd_parser.add_argument('--forbidden-connections',help='YAML file contatining the list of forbidden graph connections for specific nodes.',type=str,required = False,default=None)
   
   cmd_parser.add_argument('-m','--module-tree',action='store_true',help='Build the module tree',default=False)

   cmd_parser.add_argument('-s','--save',action='store_true',help='Save the parse tree in a file to save time for following runs.',default=False)
   cmd_parser.add_argument('--load',action='store_true',help='Save the parse tree in a file to save time for following runs.',default=False)

   args = cmd_parser.parse_args()

   # Checks
   if args.path is None and not args.load:
      sys.exit('One of the options must be specified: \n Path (-p) or Load (--load).')

   return args

def call_dict_from_path(path,exclude_files=[]):
   """
   Parse the source folder and return the dictionary of callables
   """
   source_folder = os.path.abspath(path)

   source_file_list = []
   for filename in os.listdir(path):
      if filename.upper().endswith('.F90') and filename not in exclude_files:
         source_file_list.append(filename)

   source_file_list = sorted(source_file_list)

   callable_dict = create_callable_dict(path,source_file_list)

   return callable_dict

def save_call_dict(callable_dict,filename='restart_call_dict'):

   sys.exit('RESTART IS NOT IMPLEMENTED')

   with open(filename,'wb') as f:
      for k,v in callable_dict.items():
         print(k,v)
         pickle.dump(callable_dict,f,protocol=pickle.HIGHEST_PROTOCOL) 
         #json.dump(callable_dict,f) 

def load_call_dict(filename='restart_call_dict'):
   sys.exit('RESTART IS NOT IMPLEMENTED')

def main():

   args = parse_arguments()

   #
   # Create the source code tree fparser
   #
   if args.path is not None:
      callable_dict = call_dict_from_path(args.path, exclude_files = args.exclude_files)

      if args.save:
         save_call_dict(callable_dict,filename='restart_call_dict')

   elif args.load:
      callable_dict = load_call_dict(filename='restart_call_dict')
   else:
      sys.exit('One of the options must be specified: \n Path (-p) or Load (--load).')

   #
   # Test
   #
   #obj = callable_dict['transport']
   #print_object_attributes(obj)

   # maybe, the built in comparison works...
   #print(callable_dict['transport']==callable_dict['transport'])

   # tostr() takes into account the comments that are before!
   #print(obj._node.parent.tostr())

   graph_dict = create_callable_graph_dict(callable_dict)

   #
   # Nodes to hide
   #

   hide_from_files = args.hide_from_files
   hide_nodes      = args.hide_nodes
   
   if args.hide_from_yaml is not None:

      with open(args.hide_from_yaml ,'r') as stream:
         hide_dict = load(stream,Loader=Loader)

      if 'files' in hide_dict.keys():
         hide_from_files += hide_dict['files']

      if 'nodes' in hide_dict.keys():
         hide_nodes += hide_dict['nodes']

   #
   # Callable graph creation (including HTML) for a given root node
   #
   for root_node in args.root_node_list:

      print(f'\n=== ROOT NODE: {root_node} ===\n')

      img_dir = 'images/callgraph'
      os.makedirs(img_dir, exist_ok=True)
      svg_path = os.path.join(img_dir,'{:}.svg'.format(root_node))

      create_graph_for_node(root_node,graph_dict,callable_dict,args,hide_nodes,img_dir,svg_path)

   #
   # Copy the js scipt for the node highlights
   #
   js_source_path = os.path.join(os.path.dirname(__file__),'js','jquery.maphilight.min.js')
   js_dir = 'js'
   os.makedirs(js_dir, exist_ok=True)
   shutil.copy(js_source_path,js_dir)



if __name__ == '__main__':
   main()
