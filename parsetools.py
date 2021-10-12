#!/usr/bin/env python3

"""
Tools for the FORTRAN source code parsing
"""

import os, sys, time, warnings

from fparser.common.readfortran import FortranFileReader
from fparser.two.utils import walk

from fparser.two.parser import ParserFactory
from fparser.two import Fortran2003

tnow = time.time

def print_object_attributes(obj,show_hidden = False):
   print('\n'*2)
   for key,value in obj.__dict__.items():
      if (not key.startswith('_')) or show_hidden:
         print('='*30)
         print('attribute: ',key)
         print('value: ')
         print(value)
         print('\n'*2)

   return

def get_parse_tree_dict(path,source_file_list,print_progress=True):
   """
   Parse all the files of the source code (from source_file_list) using fparser into parse_tree_dict
   Since it is the longest procedure, it is better to do that once and that
   """
   t1 = tnow()
   print_len = 0
   print('Parsing the source code directory: {:}'.format(path))
   parse_tree_dict = {}
   for i,filename in enumerate(source_file_list):

      filepath = os.path.join(path,filename)

      reader = FortranFileReader(filepath,ignore_comments=False)
      f2008_parser = ParserFactory().create(std="f2008")
      parse_tree = f2008_parser(reader)

      parse_tree_dict[filename] = parse_tree
      
      
      if print_progress:
         status_message = '  {:2.1%}  {:}'.format((i+1)/(len(source_file_list)), filename)
         
         print(' '*print_len, end='\r')
         print(status_message, end='\r', flush=True)

         print_len = len(status_message)+1

   if print_progress:
      print(' '*print_len, end='\r')

   print('\nDone: {:.2f} s'.format(tnow() - t1))
   return parse_tree_dict
 

def get_global_node_dict(parse_tree_dict,fparser_types,debug=False):
   """
   Get the dictionary of all the nodes in the source code directory (global_node_dict)
   """
   global_node_dict = {}
   for filename,parse_tree in parse_tree_dict.items():

      node_list = walk(parse_tree, fparser_types, debug=False)

      local_node_dict = {}
      for node in node_list:
         mynode = MyClassFactory(node,filename)
         local_node_dict[mynode.name] = mynode

         if debug:
            print(mynode.name)

      keys_intersection = local_node_dict.keys() & global_node_dict.keys()

      if len(keys_intersection) > 0:
         warn_message = 'Non-zero intersection between local_node_dict and global_node_dict: {:}'.format(keys_intersection)
         warnings.warn(warn_message)

      global_node_dict = global_node_dict | local_node_dict

   return global_node_dict
   

def MyClassFactory(node, filename):
   """
   Return a subclass of MyNode or MyNode depending on the fparser type
   """

   for subclass in MyNode.get_all_subclasses():
      if hasattr(subclass,'supported_fparser_types'):
         if type(node) in subclass.supported_fparser_types():
            return subclass(node,filename)

   warnings.warn('Type {:} is not supported by MyNode subclasses, assigning the MyNode class (base)'.format(type(node)))
   return MyNode(node,filename)


class MyNode:
   """
   fparser Fortran node class 
   calls are any objects belonging to Fortran2003.Call_Stmt (Subroutine,Interface)
   functions can be added to the self.calls attribute, once the all function names are known
   """
   def __init__(self,node,filename):
      self._node    = node
      self.fparser_type = type(node)
      self.type = self.interprete_fparser_type(self.fparser_type)
      self.filename = filename
      self.name     = self.get_node_name(node)
      self.parent_types  = self.get_parents(node)
      self.uses     = None
      self.calls    = None
      self.arrays_or_funcs  = None
      
      # Implemented subroutine abd functions inside the node
      self.subroutines   = self.get_type_list( (Fortran2003.Subroutine_Stmt) )
      self.functions     = self.get_type_list( (Fortran2003.Function_Stmt) )
      
      # Line statistics
      self.nfirst_line, self.nlines = self.get_line_numbers()

   def get_line_numbers(self):
      
      if self._node.parent.content[0] is not None:
         start = self._node.parent.content[0]
      else:
         start = self._node.parent.content[1]
      
      nfirst_line = start.item.span[0]
      nlines      = self._node.parent.tostr().count('\n')
      
      return nfirst_line, nlines

   def get_uses(self,include_from_module=True):
      """
      Get the list of modules used by a node
      By default, if a node is inside a module, the modules used by this one are accounted
      """
      root = None
      if include_from_module and Fortran2003.Module in self.parent_types:
         root = [ parent for parent in self.get_parents(self._node,obj=True) if type(parent) == Fortran2003.Module ][0]
      
      return self.get_type_list( (Fortran2003.Use_Stmt), root = root)

   def get_type_list(self, types, root = None):
      """
      Returns a list of all the childs if the type of child matches the types from input
      """
      if root is None:
         root = self._node.parent

      type_list = walk(root, types=types, debug=False)
      if self._node in type_list:
         type_list.remove(self._node)

      type_name_list = [self.get_node_name(x) for x in type_list]

      return sorted(list(set(type_name_list)))
   
   def get_non_internal_type_list(self, types, obj=False):
      """
      Returns a list of the childs if the type of child matches the types from input
      Children inside the 'contains' block of a subroutine (Internal_Subprogram_Part) will be excluded 
      If the node itself is a part of contains block of a subroutine, then return all the calls
      If obj is True, return a list of objects
      """
      type_list = walk(self._node.parent, types=types, debug=False)
      if self in type_list:
         type_list.remove(self)

      # Check if the node itself is a part of the contains block
      if Fortran2003.Internal_Subprogram_Part not in self.get_parents(self._node):
         non_internal_type_list = \
            [x for x in type_list if Fortran2003.Internal_Subprogram_Part not in self.get_parents(x)]

      else:
         non_internal_type_list = type_list

      if not obj:
         non_internal_type_name_list = [self.get_node_name(x) for x in non_internal_type_list]
         return sorted(list(set(non_internal_type_name_list)))
      else:
         return non_internal_type_list

   def interprete_fparser_type(self, fparser_type):
      """
      Return a human readable type of a callable based on the fparser typee
      """
      if fparser_type == Fortran2003.Subroutine_Stmt:
         return 'Subroutine'
      elif fparser_type == Fortran2003.Function_Stmt:
         return 'Function'
      elif fparser_type == Fortran2003.Interface_Stmt:
         return 'Interface'
      else:
         raise ValueError('interprete_fparser_type: fparser_type {:} is unknown'.format(fparser_type)+fparser_type)

   @classmethod
   def get_all_subclasses(self):
      for subclass in self.__subclasses__():
         yield from subclass.get_all_subclasses()
         yield subclass
   
   @staticmethod
   def get_node_name(node):
      """
      Get the name of a fparser Fortran node from Fortran2003.Name object
      """
      for child in node.children:
         if type(child) in [Fortran2003.Name,Fortran2003.Procedure_Designator]:
            return child.string

      raise ValueError('No attribute of the Fortran2003.Name type in {:}'.format(node))

   @staticmethod
   def get_parents_generator(node):
      if hasattr(node,'parent'):
         yield type(node.parent)
         yield from MyNode.get_parents_generator(node.parent)
   
   @staticmethod
   def get_parents_obj_generator(node):
      if hasattr(node,'parent'):
         yield node.parent
         yield from MyNode.get_parents_obj_generator(node.parent)

   @staticmethod
   def get_parents(node,obj=False):
      """
      Return a list of parent types (if obj == False) or
      Return a list of parent objects (if obj == True)
      """
      if obj:
         return list(MyNode.get_parents_obj_generator(node))
      else:
         return list(MyNode.get_parents_generator(node))


def check_fparser_type(fparser_object,fparser_types):
   """
   Chekck if the type of the fparser object is one of the expected fparser types
   Otherwise, raise an Error
   """
   if type(fparser_object) not in fparser_types:
      raise TypeError('fparser type of {:} is {:} which is not expected. Expected fparser types are: {:}'.format(fparser_object,type(fparser_object),' '.join(map(str,fparser_types))))


class MyFortranVariable():
   """
   Fortran variable (any type, any shape), taken from the declaration statement
   """
   def __init__(self,name=None,ftype=None):
      self.name = name
      self.ftype = ftype
      self.shape_list = None

   def __repr__(self):
      if self.shape_list is None:
         return "({:}, {:})".format(str(self.name),str(self.ftype))
      else:
         return "({:}, {:}, ({:}) )".format(str(self.name),str(self.ftype),','.join(self.shape_list))


class MyFortranArray():
   """
   Fortran array
   """
   def __init__(self):
      self.name  = None
      self.shape_list = None
      
      # Type of the array (complex, real, etc.)
      self.ftype = None

   def __str__(self):
      return str(self.name)
   
   def __repr__(self):
      if self.shape_list is None:
         return "({:}, {:})".format(str(self.name),str(self.ftype))
      else:
         return "({:}, {:}, ({:}) )".format(str(self.name),str(self.ftype),','.join(self.shape_list))
      

class MySubrOrFunc(MyNode):
   """
   Subroutine or Function
   """
   def __init__(self,node,filename):
      super().__init__(node,filename)
      self.uses   = self.get_uses()
      self.calls  = self.get_non_internal_type_list( (Fortran2003.Call_Stmt) )

      self.arrays = None
      self.arrays_or_funcs  = self.get_non_internal_type_list( (Fortran2003.Part_Ref) )
      
      self.var_dict = self.get_var_dict()

      self.alloc  = self.get_alloc()
      self.dealloc = self.get_dealloc()
      
      self.alloc_wo_dealloc = self.get_alloc_wo_dealloc()
      self.dealloc_wo_alloc = self.get_dealloc_wo_alloc()
      

   @staticmethod
   def supported_fparser_types():
      return [ Fortran2003.Subroutine_Stmt, Fortran2003.Function_Stmt ]

   def get_alloc_wo_dealloc(self):
      """
      Return a list of allocated arrays, which are not deallocated in this node. 
      The arrays will be taken from the self.alloc list
      """
      alloc_wo_dealloc_list = []
      dealloc_name_list = [x.name for x in self.dealloc]
      
      for myarray in self.alloc:
         if myarray.name not in dealloc_name_list:
            alloc_wo_dealloc_list.append(myarray)

      return alloc_wo_dealloc_list
   
   def get_dealloc_wo_alloc(self):
      """
      Return a list of deallocated arrays, which are not allocated in this node. 
      The arrays will be taken from the self.dealloc list
      """
      dealloc_wo_alloc_list = []
      alloc_name_list = [x.name for x in self.alloc]
      
      for myarray in self.dealloc:
         if myarray.name not in alloc_name_list:
            dealloc_wo_alloc_list.append(myarray)

      return dealloc_wo_alloc_list

   def get_var_dict(self):
      """
      Get a dict of MyFortranVariable() objects, that correspond to the declared variables 
      in the subroutine or function
      """
      
      var_dict = {}

      decl_stmt_list = self.get_non_internal_type_list( (Fortran2003.Type_Declaration_Stmt),obj=True )
      #decl_stmt_list = walk(self._node.parent, Fortran2003.Type_Declaration_Stmt, debug=False)

      for decl_stmt in decl_stmt_list:

         # Type
         check_fparser_type(decl_stmt.children[0],
                        [Fortran2003.Declaration_Type_Spec,Fortran2003.Intrinsic_Type_Spec])
         ftype = decl_stmt.children[0].string

         # Name and shape (if exists)
         entity_decl_list = walk(decl_stmt,(Fortran2003.Entity_Decl),debug=False)
         
         for entity_decl in entity_decl_list:
            
            check_fparser_type(entity_decl.children[0], [Fortran2003.Name])
            name = entity_decl.children[0].string

            myvar = MyFortranVariable(name=name,ftype=ftype)

            if type(entity_decl.children[1]) in \
               [Fortran2003.Assumed_Shape_Spec_List,Fortran2003.Explicit_Shape_Spec_List]:
               myvar.shape_list = [x.string for x in entity_decl.children[1].children]
            var_dict[myvar.name] = myvar

      return var_dict

   def get_alloc(self):
      """
      Get the allocated arrays in the subroutine (excluding a possible contains block), from the
      Allocate fparser type
      """
      my_alloc_list = []

      alloc_obj_list = self.get_non_internal_type_list( (Fortran2003.Allocation),obj=True )
      
      for alloc in alloc_obj_list:
         myarray = MyFortranArray()
         
         check_fparser_type(alloc.children[0], [Fortran2003.Name,Fortran2003.Data_Ref])
         name = alloc.children[0].string
         shape_list = [x.string for x in alloc.children[1].children]

         myarray.name = name
         myarray.shape_list = shape_list

         if name in self.var_dict.keys():
            myarray.ftype = self.var_dict[name].ftype

         my_alloc_list.append(myarray)

      return sorted(my_alloc_list, key=lambda x: x.name)

   def get_dealloc(self):
      """
      Get the deallocated arrays in the subroutine (excluding a possible contains block), from the
      Deallocate_Stmt fparser type
      deallocated arrays are not linked to the allocated ones at this point
      """
      my_dealloc_list = []

      dealloc_obj_list = self.get_non_internal_type_list( (Fortran2003.Deallocate_Stmt), obj=True )
      
      for dealloc in dealloc_obj_list:
         
         check_fparser_type(dealloc.children[0], [Fortran2003.Allocate_Object_List])
         
         for alloc_obj in dealloc.children[0].children:
            myarray = MyFortranArray()
            
            check_fparser_type(alloc_obj, [Fortran2003.Name,Fortran2003.Data_Ref])
            myarray.name = alloc_obj.string

            my_dealloc_list.append(myarray)

      return sorted(my_dealloc_list, key=lambda x: x.name)

   def append_func_calls(self,function_list):
      """
      Once the function list is known, append the function calls from self.arrays_or_functions to
      self.calls
      """
      loc_func_list = list( set(self.arrays_or_funcs) & set(function_list))

      self.calls += loc_func_list
      
      self.calls = sorted(self.calls)

      self.arrays = list(set(self.arrays_or_funcs) - set(loc_func_list))

      return

   def print_html(self):
      pass


class MyInterface(MyNode):
   def __init__(self,node,filename):
      super().__init__(node,filename)
      self.procedures = self.get_procedure_name_list()
   
   def update_interface_attrs(self,callable_dict):
      attrname_list = ['calls','uses','subroutines','functions']
      
      for attrname in attrname_list:
         setattr(self,attrname,[])

      self.merge_attrs(callable_dict,attrname_list)

   def get_procedure_name_list(self):
      procedure_name_list = walk(self._node.parent,Fortran2003.Procedure_Name_List,debug=False)
      procedure_name_str_list = [self.get_node_name(x) for x in procedure_name_list]

      return sorted(procedure_name_str_list)

   def merge_attrs(self,callable_dict,attrname_list):
      
      for proc in self.procedures:
         if proc not in callable_dict.keys():
            raise ValueError('{:} not found in the callable dictionary.')

         obj = callable_dict[proc]
          
         for attrname in attrname_list:
            loc_attrs = getattr(obj,attrname)
            setattr(self,attrname, getattr(self,attrname) + loc_attrs )

      for attrname in attrname_list:
         value = sorted(list(set( getattr(self,attrname) )))
         setattr(self,attrname, value)

      return

   @staticmethod
   def supported_fparser_types():
      return [ Fortran2003.Interface_Stmt ]
   

class MyModule(MyNode):
   """
   Module only
   """
   def __init__(self,node,filename):
      super().__init__(node,filename)
      self.uses   = self.get_type_list( (Fortran2003.Use_Stmt) )

   @staticmethod
   def supported_fparser_types():
      return [ Fortran2003.Module_Stmt ]

