#!/usr/bin/env python3

"""
Print javascript and jQuery functions for Fortran Tree.
To minimize the number of output files, we print styles and scripts directly to the HTML file.
"""

import re, re, os, sys, time
import numpy as np
import htmltools

def print_jquery_highlight_action(html,action_id,node_list,prefix):
   """
   Print jQuery functions to highlight nodes when action buttons are hovered
   """

   node_list_with_prefix = htmltools.get_nodes_with_prefix(node_list,prefix)

   if len(node_list_with_prefix) > 0:
      html.write('   $("#{:}").mouseover(function(e) {{\n'.format(action_id))

      for node in htmltools.get_nodes_with_prefix(node_list,prefix):
         html.write('      $("#{:}").mouseover();\n'.format(node))
      html.write('   }).mouseout(function(e) {\n')

      for node in htmltools.get_nodes_with_prefix(node_list,prefix):
         html.write('      $("#{:}").mouseout();\n'.format(node))
      html.write('   }).click(function(e) { e.preventDefault(); });\n\n')

def print_maphilight(html, node_list):
   """
   Print jQuery functions for maphilight
   """

   html.write('<!-- Load jquery -->\n')
   html.write('<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>\n\n')

   html.write('<!-- Add maphilight plugin -->\n')
   html.write('<script type="text/javascript" src="js/jquery.maphilight.min.js"></script>\n\n')

   html.write('<!-- Activate maphilight plugin -->\n')
   html.write('<script type="text/javascript">$(function() {\n')
   html.write('   $(\'.map\').maphilight();\n\n')

   html.write('   /* Highlight a node on graph if the info block is hovered */\n')
   html.write('   $(".info_sub_block_container").mouseover(function(e) {\n')
   html.write('      elem_id = this.id.replace("node_","")\n')
   html.write('      $("#"+elem_id).mouseover();\n')
   html.write('   }).mouseout(function(e) {\n')
   html.write('      $("#"+elem_id).mouseout();\n')
   html.write('   }).click(function(e) { e.preventDefault(); });\n\n')

   html.write('/* Highlight nodes when action buttons are hovered */\n')

   print_jquery_highlight_action(html,'actionShowAll',node_list,'')
   print_jquery_highlight_action(html,'actionShowSubr',node_list,'Subroutine')
   print_jquery_highlight_action(html,'actionShowFunc',node_list,'Function')
   print_jquery_highlight_action(html,'actionShowInter',node_list,'Interface')
   print_jquery_highlight_action(html,'actionShowExt',node_list,'External')

   html.write('   });\n')
   html.write('</script>\n\n')

def print_script_show_blocks(html):
   
   html.write('<!-- Script to trigger show/hide blocks when a calculation mode is selected -->\n')
   html.write('<script>\n')
   html.write('$(document).ready(function(){\n')
   html.write('$(".graph_node_block").on("click", function(e){\n')
   html.write('   e.preventDefault();\n')
   html.write('\n')
   html.write('   /* get the id of the clicked block */\n')
   html.write('   elem_id = this.id\n')
   html.write('\n')
   html.write('   ShowCallGraphBlock(elem_id)\n')
   html.write('\n')
   html.write('   });\n\n')

   html.write('$(".graph_node_block").on("mouseenter", function(e){\n')
   html.write('   e.preventDefault();\n')
   html.write('   BoxShadowOn(this.id);\n')
   html.write('   });\n')
   html.write('$(".graph_node_block").on("mouseleave", function(e){\n')
   html.write('   e.preventDefault();\n')
   html.write('   BoxShadowOff(this.id);\n')
   html.write('   });\n\n')

   html.write('// === Scroll ===\n')
   html.write('$(window).scroll(function() {  // assign scroll event listener\n')
   html.write('   var currentScroll = $(window).scrollTop(); // get current position\n')
   html.write('   /*alert($(".actionBlocksContainer").attr("style"))*/\n\n')

   html.write('   /* Action buttons */\n')
   html.write('   if (currentScroll >= 60) { // apply position: fixed if you\n')
   html.write('      $(".actionBlocksContainer").css({ // scroll to that element or below it\n')
   html.write('         position: "fixed",\n')
   html.write('         width: "100%",\n')
   html.write('         top: "5px",\n')
   html.write('         transform: "translate(-50%, 0)",\n')
   html.write('      });\n')
   html.write('   } else { // apply position: static\n')
   html.write('      $(".actionBlocksContainer").css({ // if you scroll above it\n')
   html.write('         position:"static",\n')
   html.write('         transform: "",\n')
   html.write('         textAlign: "center",\n')
   html.write('      });\n')
   html.write('   }\n')

   html.write('   /* Info blocks  */\n')
   html.write('   if (currentScroll >= 60) { // apply position: fixed if you\n')
   html.write('      $(".info_block_wrapper").css({ // scroll to that element or below it\n')
   html.write('         top: currentScroll+50+"px",\n')
   html.write('      });\n')
   html.write('   } else { // apply position: static\n')
   html.write('      $(".info_block_wrapper").css({ // if you scroll above it\n')
   html.write('         top: "auto",\n')
   html.write('      });\n')
   html.write('   }\n\n')

   html.write('   });\n\n')

   html.write('});\n\n')

   html.write('function BoxShadowOn(elem_id) {\n')
   html.write('   var elem = document.getElementById("box_node_"+elem_id);\n')
   html.write('   elem.style.boxShadow = "3px 3px 3px rgba(212, 95, 95)";\n')
   html.write('}\n\n')
   html.write('function BoxShadowOff(elem_id) {\n')
   html.write('   var elem = document.getElementById("box_node_"+elem_id);\n')
   html.write('   elem.style.boxShadow = "";\n')
   html.write('}\n\n')

   html.write('function ShowCallGraphBlock(elem_id) {\n')
   html.write('   var elem = document.getElementById("node_"+elem_id);\n')
   html.write('\n')
   html.write('   if (elem.style.display === "block"){\n')
   html.write('      elem.style.display = "none";\n')
   html.write('   } else {\n')
   html.write('      elem.style.display = "block";\n')
   html.write('   }\n')
   html.write('\n')
   html.write('}\n\n')

   html.write('function CloseDivById(elem_id) {\n')
   html.write('   var elem = document.getElementById("node_"+elem_id);\n')
   html.write('   elem.style.display = "none";\n')
   html.write('} \n\n')

   html.write('function ShowAll() {\n')
   html.write('   var modeblocks = document.querySelectorAll("[id^=node_]");\n')
   html.write('      for (var i = 0; i < modeblocks.length; i++) {\n')
   html.write('      modeblocks[i].style.display = "block";\n')
   html.write('     }\n')
   html.write('}\n\n')

   html.write('function HideAll() {\n')
   html.write('   var modeblocks = document.querySelectorAll("[id^=node_]");\n')
   html.write('      for (var i = 0; i < modeblocks.length; i++) {\n')
   html.write('      modeblocks[i].style.display = "none";\n')
   html.write('     }\n')
   html.write('}\n\n')

   html.write('function ShowFunc() {\n')
   html.write('   var modeblocks = document.querySelectorAll("[id^=node_Function]");\n')
   html.write('      for (var i = 0; i < modeblocks.length; i++) {\n')
   html.write('      modeblocks[i].style.display = "block";\n')
   html.write('     }\n')
   html.write('}\n\n')

   html.write('function ShowSubr() {\n')
   html.write('   var modeblocks = document.querySelectorAll("[id^=node_Subroutine]");\n')
   html.write('      for (var i = 0; i < modeblocks.length; i++) {\n')
   html.write('      modeblocks[i].style.display = "block";\n')
   html.write('     }\n')
   html.write('}\n\n')

   html.write('function ShowInter() {\n')
   html.write('   var modeblocks = document.querySelectorAll("[id^=node_Interface]");\n')
   html.write('      for (var i = 0; i < modeblocks.length; i++) {\n')
   html.write('      modeblocks[i].style.display = "block";\n')
   html.write('     }\n')
   html.write('}\n\n')

   html.write('function ShowExt() {\n')
   html.write('   var modeblocks = document.querySelectorAll("[id^=node_External]");\n')
   html.write('      for (var i = 0; i < modeblocks.length; i++) {\n')
   html.write('      modeblocks[i].style.display = "block";\n')
   html.write('     }\n')
   html.write('}\n\n')

   html.write('</script>\n\n')

if __name__ == '__main__':
   sys.exit('This file is not inteded to be run as __main__')
