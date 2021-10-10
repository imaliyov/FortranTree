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

   print(polygone_dict)
   corner_dict = {}

def print_css_style(html):
   html.write('<style>\n\n')
   html.write('</style>\n\n')

def print_maphilight(html):
   html.write('<!-- Add maphilight plugin -->\n')
   html.write('<script type="text/javascript" src="js/jquery.maphilight.min.js"></script>\n')
   html.write('\n')
   html.write('<!-- Activate maphilight plugin -->\n')
   html.write('<script type="text/javascript">$(function() {\n')
   html.write('        $(\'.map\').maphilight();\n')
   html.write('    });\n')
   html.write('</script>\n\n')

def create_html(svg_path, html_filename, node_list):

   get_node_coord(svg_path, node_list)

   html = open(html_filename,'w')

   html.write('<html>\n')
   html.write('<head>\n\n')

   print_maphilight(html)

   print_css_style(html)

   html.write('</head>\n\n')

   html.write('</html>\n')

   html.close()

if __name__ == '__main__':
   sys.exit('This file is not inteded to be run as __main__')
