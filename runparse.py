#!/usr/bin/env python3

"""
Run the code parsing and create the subroutine/module interactive graphs
"""

import os, sys
import textwrap
import argparse

from parsetools import  get_parse_tree_dict, \
                        get_global_node_dict, \
                        print_object_attributes, \
                        MySubrOrFunc, MyInterface

from fparser.two.utils import walk

from fparser.two.parser import ParserFactory
from fparser.two import Fortran2003
from datetime import datetime
import time

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

#
# Parse command line arguments
#
help_description = textwrap.dedent(str_examples())

cmd_parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,description=help_description)

cmd_parser.add_argument('-p','--path',help='Path to the source code',required = True)
cmd_parser.add_argument('--exclude',help='List of file to exclude from parsing',nargs='*',required = False,default=[])
cmd_parser.add_argument('-m','--module_tree',action='store_true',help='Build the module tree',default=False)

args = cmd_parser.parse_args()


#
# Create the source code tree fparser
#
source_folder = os.path.abspath(args.path)

source_file_list = []
for filename in os.listdir(args.path):
   if filename.upper().endswith('.F90') and filename not in args.exclude:
      source_file_list.append(filename)

source_file_list = sorted(source_file_list)

#
# fparser provides a parse tree per file.
# So here, we run over all the files of the source directory and create a dictionary of parse trees
#
parse_tree_dict = get_parse_tree_dict(args.path,source_file_list)

#
# Get the dictionary of MyNode instances 
# for Fortran "callables": subroutines, functions, and interfaces
#
types_tuple = (Fortran2003.Subroutine_Stmt,Fortran2003.Function_Stmt,Fortran2003.Interface_Stmt)
callable_dict = get_global_node_dict(parse_tree_dict,types_tuple,debug=False)

function_list = [ x.name for x in callable_dict.values() if x.fparser_type == Fortran2003.Function_Stmt]

#
# Once the function list is known, add the function calls to the .calls attribute
# It was not possible to do before the function list is known since the Fortran syntax 
# for a function and an array is the same
#

for obj in callable_dict.values():
   if isinstance(obj,MySubrOrFunc):
      obj.append_func_calls(function_list)

#
# Once the callable_dict is filled entirely for functions and subroutines, we can update
# the interfaces attributes to encorporate all the calls, etc. of the module procedures 
# that they contain
#
for obj in callable_dict.values():
   if isinstance(obj,MyInterface):
      obj.update_interface_attrs(callable_dict)

#obj = callable_dict['init_boltz_grid']
#obj = callable_dict['transport']
#obj = callable_dict['hdf_read_attr_integer_1']
print_object_attributes(obj)

# maybe, the built in comparison works...
#print(callable_dict['transport']==callable_dict['transport'])

# tostr() takes into account the comments that are before!
#print(obj._node.parent.tostr())
#s1.strip().lower() == s3.strip().lower()
