#!/usr/bin/env python3

"""
Tools for the html file writing based on the call graph
"""

import re, re, os, sys, time
import numpy as np
import print_style
import print_script

def get_node_coord(svg_path, node_list, node_type_dict):
   """
   Get coordinates of each node by parsing the svg graph file
   """

   polygone_dict = {}

   with open(svg_path,'r') as f:
      lines = f.readlines()

      # insted of "Subroutine-boltz_setup", "boltz_setup", to match with svg file node names
      node_list_wo_prefix = [l.split('-')[1] for l in node_list]

      for i,line in enumerate(lines):

         if 'viewBox' in line:
            image_width, image_height = list(map(float,line.split('viewBox=')[1].replace('"','').split()[2:4]))

         if 'translate' in line:
            x_offset, y_offset = list(map(float,re.sub(r'[()">]','',line.split('translate')[1]).split() ))
            y_offset = image_height - y_offset

         # line example: <!-- init_boltz_grid -->
         if '<!--' in line and line.split()[1] in node_list_wo_prefix:
            node = line.split()[1]
            node = node_type_dict[node] + '-' + node

            # line example: <polygon fill="none" stroke="black" points="378.99,-36 286.99,-36 286.99,0 378.99,0 378.99,-36"/>
            poly_line = lines[i+3]
            pairs = poly_line.split('points=')[1].strip('"/>').split()[:-1]
            pairs_list = [tuple(map(float,p.split(','))) for p in pairs]
            polygone_dict[node] = pairs_list

      #ymin = -left_bottom[1] + y_offset
      #ymax = -right_top[1]   + y_offset

   corner_dict = {}

   for node,p in polygone_dict.items():

      left_bottom = p[1]
      right_top   = p[3]

      xmin = left_bottom[0] + x_offset
      xmax = right_top[0]   + x_offset

      ymin = left_bottom[1] - y_offset + image_height
      ymax = right_top[1]   - y_offset + image_height

      corner_dict[node] = '{},{},{},{}'.format(xmin,ymin,xmax,ymax)

   return image_width, image_height, corner_dict

def print_image_map(html, image_width, image_height, corner_dict):
   """
   Print the map for the nodes of the callgraph
   """

   html.write('<map name="callgraph">\n')

   for node,corner in corner_dict.items():

      html.write('  <area class="graph_node_block" id={0:<15} shape="rect" coords={1:<30} alt={0:<15} href="">\n'.format('"'+node+'"','"'+corner_dict[node]+'"'))

   html.write('</map>\n\n')


def get_nodes_with_prefix(node_list,prefix):

   node_list_with_prefix = []
   for node in node_list:
      if node.startswith(prefix):
         node_list_with_prefix.append(node)

   return node_list_with_prefix

def print_module_use(html,node_obj):

   if len(node_obj.uses) == 0:
      return

   html.write('<button type="button" class="collapsible">'+'&#9660;'+'&nbsp;'*10+'Uses modules'+'&nbsp;'*10+'&#9660;'*1+'</button>')
   html.write('<div class="collapsibleContent">\n')
   html.write('<nobr>\n')

   for usename in node_obj.uses:
      html.write(f'<code> {usename} </code>\n')

   html.write('\n<!--collapsibleContent -->\n')
   html.write('</div>\n')
   html.write('<br>\n'*2)

def print_node_info(html, callable_dict, node_list, action_dict):

   html.write('<!-- Nodes description -->\n\n')

   html.write('<!-- info block wrapper-->\n')
   html.write('<div class="info_block_wrapper">\n\n')

   html.write('<!-- info block div-->\n')
   html.write('<div class="info_block">\n\n')

   for node in node_list:

      node_name = node.split('-')[1]
      node_type = node.split('-')[0]

      html.write('<div id="node_{:}" class="info_sub_block_container" >\n'.format(node))

      html.write('<div id="box_node_{:}" class="info_sub_block {:}">\n'.format(node,node_type))

      # Close "button"
      html.write('<div onclick="CloseDivById(\'{:}\')" class="closeDiv">&#215;</div>\n\n'.format(node))

      if node_name in callable_dict.keys():
         node_obj = callable_dict[node_name]

         html.write('<p style="font-size:1.2em;"><i>{:}</i>:&nbsp; <b>{:}</b></p>\n'.format(node_obj.type,node_obj.name))
         html.write('<p><i>File</i>: {:}</p>\n'.format(node_obj.filename))
         html.write('<p><i>Line</i>: {:} &ensp;<i>Num. of lines</i>: {:}</p>\n\n'.format(node_obj.nfirst_line,node_obj.nlines))

         print_module_use(html,node_obj)

      else:
         html.write('<p style="font-size:1.2em;"><i>External node</i>:&nbsp; <b>{:}</b></p>\n'.format(node_name))
         html.write('<p>This node is implemented outside the source directory.</p>\n')
      
      html.write('<!-- sub block div -->\n')
      html.write('</div>\n\n')

      html.write('<!-- Container div -->\n')
      html.write('</div>\n\n')

   html.write('<!-- info block div-->\n')
   html.write('</div>\n\n')

   html.write('<!-- info block wrapper-->\n')
   html.write('</div>\n\n')

def set_action_dict():
   """
   Set up a dictionary that contains colors and actions for each node type
   """
   action_dict = {
      'ShowAll': { 
         'backgr' : 'FFFFFF', 
         'font'   : '000000',
         'func' : 'ShowAll',
         'text' : 'Show all nodes',
         },
      'HideAll': { 
         'backgr' : 'E3E3E3', 
         'font'   : '000000',
         'func' : 'HideAll',
         'text': 'Hide all nodes',
         },
      'Subroutine': { 
         #'backgr' : 'F5F3DE',
         'backgr' : 'FFE0AA', 
         'backgr2' : 'fff0d6', 
         'font'   : '654610',
         'func' : 'ShowSubr',
         'text': 'Show subroutines',
         },
      'Function': { 
         'backgr' : 'FFCAAA', 
         'backgr2' : 'ffe0cc', 
         'font'   : '552000',
         'func' : 'ShowFunc',
         'text': 'Show functions',
         },
      'Interface': { 
         'backgr' : 'bdc6d6', 
         'backgr2' : 'd9dfe7', 
         'font'   : '152D54',
         'func' : 'ShowInter',
         'text': 'Show interfaces',
         },
      'External': { 
         'backgr' : 'bfe8de', 
         'backgr2' : 'e9f7f3', 
         'font'   : '003326',
         'func' : 'ShowExt',
         'text': 'Show external nodes',
         },
   }

   return action_dict

def create_html(callable_dict, svg_path, node_list, node_type_dict, path, root_node):

   #
   # Dictionary that contains colors and actions for each node type
   #
   action_dict = set_action_dict()

   #
   # Node coordinates from svg
   #
   image_width, image_height, corner_dict = get_node_coord(svg_path, node_list, node_type_dict)

   #
   # HTML file
   #
   html_filename = 'call_graph_{:}.html'.format(root_node)
   html = open(html_filename,'w')

   #
   # Head
   #
   html.write('<!DOCTYPE html>\n')
   html.write('<html>\n')
   html.write('<head>\n\n')

   html.write('<title>{:} call graph</title>\n\n'.format(root_node))

   print_script.print_maphilight(html, node_list)

   print_script.print_script_show_blocks(html)

   print_script.print_collapsible_func(html)

   print_style.print_css_style(html,action_dict, image_width)

   html.write('</head>\n\n')

   #
   # Body
   #
   html.write('<body>\n\n')

   #
   # Title
   #
   html.write('<!-- Title -->\n')
   html.write('<h1 style="text-align: center;">Call graph from the source folder: <code>{:}</code>. Root node: <code>{:}</code>.</h1>\n'.format(os.path.split(path)[1],root_node)) 
   #html.write('<p style="font-size:120%; text-align: center;">Click on a node to get its description.</p>\n\n')

   html.write('<div class="actionBlocksContainer">\n')

   num_actions = len(list(action_dict.keys()))

   for i,action in enumerate(action_dict.keys()):

      func = action_dict[action]['func']
      text = action_dict[action]['text']

      action = '' if action == 'ShowAll' else action
      num = len( get_nodes_with_prefix(node_list,action) )

      if action == 'HideAll':
         html.write('<div class="actionBlock {0:}" id="action{0:}" onclick="{0:}()">{1:}</div>\n&nbsp;\n'.format(func,text))
      elif num > 0:
         html.write('<div class="actionBlock {0:}" id="action{0:}" onclick="{0:}()">{1:} (<b>{2:}</b>)</div>\n'.format(func,text,num))
         if i < num_actions-1:
            html.write('&nbsp;\n')


   html.write('</div>\n\n')

   html.write('<br>\n'*2)
   html.write('\n'*2)

   print_image_map(html, image_width, image_height, corner_dict)

   #
   # Wrapper
   #
   html.write('<!-- wrapper div -->\n\n')
   html.write('<div class="img_info_wrapper">\n')

   #
   # Image
   #
   html.write('<!-- image div -->\n')
   html.write('<div class="img_block">\n')
   html.write('<img src="{:}" class="map" style="width:{:}px;height:{:}px;" alt="Callgraph" usemap="#callgraph">\n\n'.format(svg_path,image_width,image_height))
   html.write('</div>\n')

   #
   # Nodes description
   #
   print_node_info(html, callable_dict, node_list, action_dict)

   html.write('<!-- wrapper div -->\n')
   html.write('</div>\n\n')

   html.write('</body>\n\n')

   html.write('</html>\n')

   html.close()

if __name__ == '__main__':
   sys.exit('This file is not inteded to be run as __main__')
