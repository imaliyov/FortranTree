#!/usr/bin/env python3

"""
Print css style for Fortran Tree. 
To minimize the number of output files, we print styles and scripts directly to the HTML file.
"""

def print_css_style(html,action_dict, image_width):
   
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
   # Info block wrapper for horizontal positioning
   #
   html.write('.info_block_wrapper{\n')
   html.write('   position: absolute;\n')
   html.write('   left: {:}px;\n'.format(image_width))
   html.write('   overflow: auto;\n')
   html.write('   top: auto;\n')
   html.write('}\n')
   html.write('\n\n')

   #
   # Info block
   #
   html.write('.info_block{\n')
   html.write('   position: relative;\n')
   html.write('   margin-left: 30px;\n')
   html.write('   display: inline-block;\n')
   html.write('   float: left;\n')
   html.write('   width: 550px;\n')
   html.write('   height: 94vh;\n')
   html.write('   overflow: auto;\n')
   html.write('}\n\n')

   #
   # Info sub-block
   #
   html.write('.info_sub_block_container{\n')
   html.write('   display: none;\n') # side by side
   html.write('   margin-bottom: 12px;\n') 
   html.write('   margin-right: 30px;\n')
   html.write('}\n\n')

   html.write('.info_sub_block{\n')
   html.write('   position: relative;\n') # !! for close button
   html.write('   width: 100%;\n')
   html.write('   border-radius: 5px;\n')
   html.write('   border: 1px solid #000000;\n')
   html.write('   padding: 10px;\n')
   html.write('   background: #F5F3DE;\n')
   html.write('   line-height: 60%;\n')
   html.write('   font-size: 1.0em;\n')
   html.write('   font-family: Arial, Helvetica, sans-serif;\n')
   html.write('   \n')
   html.write('   /* IE 7 hack */\n')
   html.write('   *zoom:1;\n')
   html.write('   *display: inline;\n')
   html.write('   vertical-align: middle;\n')
   html.write('   }\n\n')

   html.write('.info_sub_block:hover {\n')
   html.write('   box-shadow: 3px 3px 3px rgba(212, 95, 95);\n')
   html.write('}\n\n')

   #
   # Close "button" for each info sub block
   #
   html.write('.closeDiv{\n')
   html.write('   cursor: pointer;\n')
   html.write('   position: absolute;\n')
   html.write('   margin-top:2px;\n')
   html.write('   text-align:right;\n')
   html.write('   right: 15px;\n')
   html.write('   opacity:0.6;\n')
   html.write('   display:inline-block;\n')
   html.write('   font-size: 1.6em;\n')
   html.write('}\n\n')

   html.write('.closeDiv:hover {\n')
   html.write('   opacity: 0.3;\n')
   html.write('}\n\n')

   html.write('.actionBlocksContainer{\n')
   html.write('   position: static;\n')
   html.write('   display: block;\n')
   html.write('   z-index: 99;\n')
   html.write('   left: 50%;\n')
   html.write('   text-align: center;\n')
   html.write('}\n\n')

   html.write('.actionBlock{\n')
   html.write('   cursor: pointer;\n')
   html.write('   font-size: 0.9em;\n')
   html.write('   display: inline-block;\n')
   html.write('   border-radius: 5px;\n')
   html.write('   border: 2px solid #000000;\n')
   html.write('   padding: 10px;\n')
   html.write('   /*padding-bottom: 5px;*/\n')
   html.write('   line-height: 80%;\n')
   html.write('   font-family: Arial, Helvetica, sans-serif;\n')
   html.write('   box-shadow: 0 0 5px -1px rgba(0,0,0,0.6);\n')
   html.write('}\n\n')

   html.write('.actionBlock:hover{\n')
   html.write('   color: rgba(74,74,74,0.8);\n')
   html.write('   border: 2px solid #767676;\n')
   html.write('}\n\n')

   html.write('.actionBlock:active{\n')
   html.write('   box-shadow: 0 0 9px -1px rgba(0,0,0,0.6);\n')
   html.write('   color: rgba(90,90,90,0.7);\n')
   html.write('   border: 2px solid #878787;\n')
   html.write('}\n\n')

   html.write('/* Style for action buttons */\n')
   for action in action_dict.keys():
      html.write('.{:}{{\n'.format(action_dict[action]['func']))
      html.write('   color: #{:};\n'.format(action_dict[action]['font']))
      html.write('   background: #{:};\n'.format(action_dict[action]['backgr']))
      html.write('}\n\n')

   html.write('/* Style for node-specific info blocks */\n')
   for action in action_dict.keys():
      if action in ['ShowAll','HideAll']:
         continue
      html.write('.{:}{{\n'.format(action))
      html.write('   background: #{:};\n'.format(action_dict[action]['backgr2']))
      html.write('}\n\n')

   #
   # Collapsible
   #

   html.write('/* ==== COLLAPSIBLE ==== */\n')
   html.write('\n')
   html.write('/* Style the button that is used to open and close the collapsible content */\n')
   html.write('.collapsible {\n')
   html.write('  background-color: #AAAAAA;\n')
   html.write('  border-radius: 5px;\n')
   html.write('  color: #000000;\n')
   html.write('  cursor: pointer;\n')
   html.write('  padding-top: 1.0px;\n')
   html.write('  width: 100%;\n')
   html.write('  border: none;\n')
   html.write('  text-align: center;\n')
   html.write('  outline: none;\n')
   html.write('  font-size: 0.85em;\n')
   html.write('  border-left: solid 6px #888888;\n')
   html.write('  margin-bottom:-10px;\n')
   html.write('}\n\n')

   html.write('.active, .collapsible:hover {\n')
   html.write('  background-color: #BEBEBE;\n')
   html.write('  border-radius: 5px 5px 0 0;\n')
   html.write('}\n\n')

   html.write('/* Style the collapsible content. Hidden by default */\n')
   html.write('.collapsibleContent {\n')
   html.write('  padding-bottom: 2%;\n')
   html.write('  padding-top: 3%;\n')
   html.write('  display: none;\n')
   html.write('  overflow: hidden;\n')
   html.write('  background-color: #D1D1D1;\n')
   html.write('  border-left: solid 6px #888888;\n')
   html.write('  border-radius: 0 0 5px 5px;\n')
   html.write('}\n\n')

   html.write('.collapsibleText{\n')
   html.write('   width: 100%;\n')
   html.write('   line-height: normal;\n')
   html.write('   white-space: normal;\n')
   html.write('   margin-left: 10px;\n')
   html.write('   font-size: 1.1em;\n')
   html.write('}\n\n')

   html.write('</style>\n\n')

if __name__ == '__main__':
   sys.exit('This file is not inteded to be run as __main__')
