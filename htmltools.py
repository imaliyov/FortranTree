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
   html.write('<style>\n\n')
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
   html.write('   ShowBlockInteractive(elem_id)\n')
   html.write('\n')
   html.write('   });\n')
   html.write('});\n')
   html.write('</script>\n\n')


def create_html(svg_path, html_filename, node_list, path, root_node):

   image_width, image_height, corner_dict = get_node_coord(svg_path, node_list)

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

   #
   # Image
   #
   html.write('<img src="{:}" class="map" style="width:{:}px;height:{:}px" alt="Callgraph" usemap="#callgraph">\n\n'.format(svg_path,image_width,image_height))

   print_map(html, image_width, image_height, corner_dict)

   html.write('</body>\n\n')

   html.write('</html>\n')

   html.close()

if __name__ == '__main__':
   sys.exit('This file is not inteded to be run as __main__')
