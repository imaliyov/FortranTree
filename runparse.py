#!/usr/bin/env python3

"""
Run the code parsing and create the subroutine/module interactive graphs
"""

import os, sys, shutil
import pygraphviz as pgv
import textwrap
import argparse

import htmltools

from parsetools import  get_parse_tree_dict, \
                        get_global_node_dict, \
                        print_object_attributes, \
                        MySubrOrFunc, MyInterface

from fparser.two.utils import walk

from fparser.two.parser import ParserFactory
from fparser.two import Fortran2003
from datetime import datetime
import time

from yaml import load, dump
try:
   from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
   from yaml import Loader, Dumper

#tnow = datetime.now
tnow = time.time
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

def get_all_graph_successors(graph,node,glob_list=None):

   if glob_list is None:
      glob_list = []

   successors = graph.successors(node)

   glob_list += successors

   for successor in successors:
      get_all_graph_successors(graph,successor,glob_list=glob_list) 

   return glob_list
      
def create_callable_graph_dict(callable_dict):
   """
   Using the callable_dict, create a dict that can be processed by pygraphviz
   """
   t1 = tnow()
   print('\nCreating a graph dictionary')

   graph_dict = {}

   for name, obj in callable_dict.items():

      tmp_call_dict = {}
      for call in obj.calls: 
         tmp_call_dict[call] = None

      graph_dict[name] = tmp_call_dict

   print('Done: {:.2f} s'.format(tnow() - t1))

   return graph_dict

def create_call_graph(graph_dict,callable_dict,root_node_name,hide_from_files=[],hide_nodes=[]):
   """
   Create a pygraphviz graph based on callable_dict
   """
   t1 = tnow()
   print('\nCreating a graph')

   call_graph = pgv.AGraph(graph_dict,strict=False,directed=True)#.reverse()

   root_node = call_graph.get_node(root_node_name)

   #
   # Remove the nodes that are from the files in hide_from_files list
   # or if a node is in hide_nodes list
   #
   if len(hide_from_files) > 0 or len(hide_nodes) > 0:

      for node in call_graph.nodes():

         node_in_list = node in hide_nodes

         node_from_hid_file = \
            node in callable_dict.keys() and \
            callable_dict[node].filename in hide_from_files 

         if node_in_list or node_from_hid_file:
            call_graph.delete_node(node)
   
   #
   # Remove all the nodes that are not the successors of the root node
   #
   all_successors = get_all_graph_successors(call_graph,root_node)

   for node in call_graph.nodes():
      if node not in all_successors and node != root_node:
         call_graph.delete_node(node)

   print('Done: {:.2f} s'.format(tnow() - t1))

   return call_graph

def get_node_depth(graph,node,depth=0):
   """
   Get the depth of the node (an integer) using the predecessors method.
   """

   predecessors = graph.predecessors(node)
   
   if len(predecessors) > 0:
      depth = get_node_depth(graph,predecessors[0],depth=depth+1)

   return depth

def get_sorted_node_list(graph):
   """
   Sort the graph nodes according to their depth in the graph and then alphabetic oreder
   """

   node_list = graph.nodes()

   node_list = sorted(node_list, key = lambda x: (get_node_depth(graph,x), x ))

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

def main():

   #
   # Parse command line arguments
   #
   help_description = textwrap.dedent(str_examples())

   cmd_parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,description=help_description)

   cmd_parser.add_argument('-p','--path',help='Path to the source code',required = True)
   cmd_parser.add_argument('-r','--root-node',help='Name of the root node. The call tree will be ploted from the root node.', type=str, required=True)
   cmd_parser.add_argument('-y','--hide-from-yaml',help='Hide the callables that are in specific files or select them by name, contained in the yaml file. The file must have the dictionary structure with the following keys: files: [List of files] and/or nodes: [List of nodes].',type=str,required = False,default=None)
   cmd_parser.add_argument('--exclude-files',help='List of file to exclude from parsing',nargs='*',required = False,default=[])
   cmd_parser.add_argument('--hide-from-files',help='List of files. If a suboutine/function is implemented in one of these files, it will be hidden in the graph.',nargs='*',required = False,default=[])
   cmd_parser.add_argument('--hide-nodes',help='List of nodes to hide in the graph',nargs='*',required = False,default=[])
   cmd_parser.add_argument('-m','--module_tree',action='store_true',help='Build the module tree',default=False)

   args = cmd_parser.parse_args()


   #
   # Create the source code tree fparser
   #
   source_folder = os.path.abspath(args.path)

   source_file_list = []
   for filename in os.listdir(args.path):
      if filename.upper().endswith('.F90') and filename not in args.exclude_files:
         source_file_list.append(filename)

   source_file_list = sorted(source_file_list)

   callable_dict = create_callable_dict(args.path,source_file_list)

   #
   # Test
   #
   #obj = callable_dict['init_boltz_grid']
   obj = callable_dict['transport']
   #obj = callable_dict['hdf_write_dataset']
   #obj = callable_dict['hdf_read_attr_integer_1']
   print_object_attributes(obj)

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

   call_graph = create_call_graph(graph_dict,callable_dict,args.root_node,hide_from_files=args.hide_from_files,hide_nodes=args.hide_nodes )

   call_graph.node_attr['shape']='rectangle'
   call_graph.graph_attr['rankdir']='LR'
   call_graph.layout(prog='dot')

   #
   # Create the directory for images and save the svg file
   #
   img_dir = 'images/callgraph'
   os.makedirs(img_dir, exist_ok=True)
   svg_path = os.path.join(img_dir,'{:}.svg'.format(args.root_node))

   call_graph.draw(svg_path)
   call_graph.draw('{:}.png'.format(args.root_node))

   sorted_node_list = get_sorted_node_list(call_graph)
   prefix_node_list = get_prefix_node_list(callable_dict,sorted_node_list)
   node_type_dict = get_node_type_dict(callable_dict,sorted_node_list)

   #
   # Dump HTML
   #
   t1 = tnow()
   print('\nCreating HTML file')

   htmltools.create_html(callable_dict, svg_path, prefix_node_list, node_type_dict, args.path, args.root_node)

   print('Done: {:.2f} s'.format(tnow() - t1))

   #
   # Copy the js scipt for the node highlights
   #
   js_source_path = os.path.join(os.path.dirname(__file__),'js','jquery.maphilight.min.js')
   js_dir = 'js'
   os.makedirs(js_dir, exist_ok=True)
   shutil.copy(js_source_path,js_dir)



if __name__ == '__main__':
   main()
