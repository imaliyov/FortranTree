#!/usr/bin/env python3

"""
Tools for the html file writing based on the call graph
"""

import re, re, os, sys, time
import numpy as np

def get_node_coord(svg_path, node_list):
   """
   Get coordinates of each node by parsing the svg graph file
   """

   polygone_dict = {}

   with open(svg_path,'r') as f:
      lines = f.readlines()

      for i,line in enumerate(lines):

         if 'viewBox' in line:
            image_width, image_height = list(map(float,line.split('viewBox=')[1].replace('"','').split()[2:4]))

         if 'translate' in line:
            x_offset, y_offset = list(map(float,re.sub(r'[()">]','',line.split('translate')[1]).split() ))
            y_offset = image_height - y_offset

         # line example: <!-- init_boltz_grid -->
         if '<!--' in line and line.split()[1] in node_list:
            node = line.split()[1]
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

def print_map(html, image_width, image_height, corner_dict):
   """
   Print the map for the nodes of the callgraph
   """

   html.write('<map name="callgraph">\n')

   for node,corner in corner_dict.items():

      html.write('  <area class="calc_mode_block" id={0:<15} shape="rect" coords={1:<30} alt={0:<15} href="">\n'.format('"'+node+'"','"'+corner_dict[node]+'"'))

   html.write('</map>\n\n')


def print_css_style(html):
   
   info_block_width = 350 # in px

   html.write('\n')
   html.write('<style>\n\n')

   #
   # Wrapper
   #
   html.write('.img_info_wrapper{\n')
   html.write('   width: 100%;\n')
   html.write('}\n\n')

   #
   # Graph image
   #
   html.write('.img_block{\n')
   html.write('   display: inline-block;\n')
   html.write('   float: left;\n')
   html.write('}\n\n')

   #
   # Info sub-block
   #
   html.write('.info_block{\n')
   html.write('   display: inline-block;\n')
   html.write('   float: left;\n')
   html.write('   width: {:}px;\n'.format(info_block_width))
   html.write('}\n\n')

   #
   # Info sub-block
   #
   html.write('.info_sub_block{\n')
   html.write('   width: 100%;\n')
   html.write('   border-radius: 5px;\n')
   html.write('   border: 1px solid #000000;\n')
   html.write('   padding: 10px;\n')
   html.write('   /*padding-bottom: 5px;*/\n')
   html.write('   display: inline-block;\n') # side by side
   html.write('   background: #F5F3DE;\n')
   html.write('   line-height: 80%;\n')
   html.write('   font-size: initial;\n')
   html.write('   \n')
   html.write('   /* IE 7 hack */\n')
   html.write('   *zoom:1;\n')
   html.write('   *display: inline;\n')
   html.write('   vertical-align: middle;\n')
   html.write('   }\n\n')

   html.write('</style>\n\n')

def print_maphilight(html):
   
   html.write('<!-- Load jquery -->\n')
   html.write('<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>\n\n')

   html.write('<!-- Add maphilight plugin -->\n')
   html.write('<script type="text/javascript" src="js/jquery.maphilight.min.js"></script>\n\n')

   html.write('<!-- Activate maphilight plugin -->\n')
   html.write('<script type="text/javascript">$(function() {\n')
   html.write('        $(\'.map\').maphilight();\n')
   html.write('    });\n')
   html.write('</script>\n\n')

   html.write('<!-- Script to trigger show/hide blocks when a calculation mode is selected -->\n')
   html.write('<script>\n')
   html.write('$(document).ready(function(){\n')
   html.write('$(".node_block").on("click", function(e){\n')
   html.write('   e.preventDefault();\n')
   html.write('\n')
   html.write('   /* get the id of the clicked block */\n')
   html.write('   elem_id = this.id\n')
   html.write('\n')
   html.write('   ShowCallGraphBlock(elem_id)\n')
   html.write('\n')
   html.write('   });\n')
   html.write('});\n')
   html.write('</script>\n\n')

def print_node_info(html, callable_dict, node_list):

   html.write('<!-- Nodes description -->\n\n')

   html.write('<!-- info block div-->\n')
   html.write('<div class="info_block">\n')

   for node in node_list:

      #html.write('<div id="hide_node_{0}" style="display:none;">\n'.format(node))
      html.write('<div id="hide_node_{0}" class="info_sub_block" >\n'.format(node))

      if node in callable_dict.keys():
         html.write('<p><i>{:}</i>: {:}</p>\n'.format(callable_dict[node].type,callable_dict[node].name))
         html.write('<p><i>File</i>: {:}</p>\n'.format(callable_dict[node].filename))
         html.write('<p><i>Line</i>: {:}</p>\n'.format(callable_dict[node].nfirst_line))
         html.write('<p><i>Num. of lines</i>: {:}</p>\n'.format(callable_dict[node].nlines))

      else:
         html.write('<p><i>External node</i>: {:}</p>\n'.format(node))
         html.write('<p>This node is implemented outside the source directory.</p>\n')
      
      html.write('</div>\n\n')

   html.write('<!-- info block div-->\n')
   html.write('</div>\n\n')

def create_html(callable_dict, svg_path, node_list, path, root_node):

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

   print_maphilight(html)

   print_css_style(html)

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
   html.write('<p style="font-size:120%; text-align: center;">Click on a node to get its description.</p>\n\n')
   html.write('<br>\n'*2)
   html.write('\n'*2)

   #
   # Node coordinates from svg
   #
   image_width, image_height, corner_dict = get_node_coord(svg_path, node_list)

   print_map(html, image_width, image_height, corner_dict)

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
   print_node_info(html, callable_dict, node_list)

   html.write('<!-- wrapper div -->\n')
   html.write('</div>\n\n')

   html.write('</body>\n\n')

   html.write('</html>\n')

   html.close()

if __name__ == '__main__':
   sys.exit('This file is not inteded to be run as __main__')
