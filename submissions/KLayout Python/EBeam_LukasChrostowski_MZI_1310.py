'''
--- Simple MZI ---
  
by Lukas Chrostowski, 2024


   
Example simple script to
 - create a new layout with a top cell
 - create an MZI
 - export to OASIS for submission to fabrication

using SiEPIC-Tools function including connect_pins_with_waveguide and connect_cell

Use instructions:

Run in Python, e.g., VSCode

pip install required packages:
 - klayout, SiEPIC, siepic_ebeam_pdk, numpy

'''

designer_name = 'LukasChrostowski'
top_cell_name = 'EBeam_%s_MZI' % designer_name
export_type = 'static'  # static: for fabrication, PCell: include PCells in file

import pya
from pya import *

import SiEPIC
from SiEPIC._globals import Python_Env
from SiEPIC.scripts import connect_cell, connect_pins_with_waveguide, zoom_out, export_layout
from SiEPIC.utils.layout import new_layout, floorplan
from SiEPIC.extend import to_itype
from SiEPIC.verification import layout_check
 
import os

if Python_Env == 'Script':
    # For external Python mode, when installed using pip install siepic_ebeam_pdk
    import siepic_ebeam_pdk

print('EBeam_LukasChrostowski_MZI layout script')
 
tech_name = 'EBeam'

from packaging import version
if version.parse(SiEPIC.__version__) < version.parse("0.5.4"):
    raise Exception("Errors", "This example requires SiEPIC-Tools version 0.5.4 or greater.")

'''
Create a new layout using the EBeam technology,
with a top cell
and Draw the floor plan
'''    
cell, ly = new_layout(tech_name, top_cell_name, GUI=True, overwrite = True)
floorplan(cell, 605e3, 410e3)

dbu = ly.dbu

from SiEPIC.scripts import connect_pins_with_waveguide, connect_cell
waveguide_type1='SiN Strip TE 1310 nm, w=750 nm'
waveguide_type2='SiN Strip TE 1310 nm, w=800 nm'
waveguide_type_delay='SiN routing TE 1550 nm (compound waveguide)'

# Load cells from library
cell_ebeam_gc = ly.create_cell('ebeam_GC_SiN_TE_1310_8deg', 'EBeam-SiN', {})
cell_ebeam_y = ly.create_cell('ebeam_YBranch_te1310',  'EBeam-SiN')
cell_ebeam_taper = ly.create_cell('taper_bezier', 'EBeam_Beta',
                               {'wg_width1':0.75, 
                                'wg_width2':0.8,
                                'wg_length':1,
                                'silayer':pya.LayerInfo(4,0),
                                } )


# grating couplers, place at absolute positions
x,y = 60000, 16000
t = Trans(Trans.R0,x,y)
instGC1 = cell.insert(CellInstArray(cell_ebeam_gc.cell_index(), t))
t = Trans(Trans.R0,x,y+127000)
instGC2 = cell.insert(CellInstArray(cell_ebeam_gc.cell_index(), t))

# automated test label
text = Text ("opt_in_TE_1310_device_%s_MZI1" % designer_name, t)
cell.shapes(ly.layer(ly.TECHNOLOGY['Text'])).insert(text).text_size = 5/dbu

# Y branches:
instTaper1 = connect_cell(instGC1, 'opt1', cell_ebeam_taper, 'opt1')
instY1 = connect_cell(instTaper1, 'opt2', cell_ebeam_y, 'opt1')
instTaper2 = connect_cell(instGC2, 'opt1', cell_ebeam_taper, 'opt1')
instY2 = connect_cell(instTaper2, 'opt2', cell_ebeam_y, 'opt1')

# Waveguides: 

connect_pins_with_waveguide(instY1, 'opt2', instY2, 'opt3', waveguide_type=waveguide_type2,turtle_B=[60,-90])
connect_pins_with_waveguide(instY1, 'opt3', instY2, 'opt2', waveguide_type=waveguide_type2,turtle_B=[60+50,-90])

if 0:
    # 3rd MZI, with a very long delay line
    cell_ebeam_delay = ly.create_cell('spiral_paperclip', 'EBeam_Beta',
                                    {'waveguide_type':waveguide_type_delay,
                                    'length':200,
                                    'flatten':True})
    x,y = 60000, 205000
    t = Trans(Trans.R0,x,y)
    instGC1 = cell.insert(CellInstArray(cell_ebeam_gc.cell_index(), t))
    t = Trans(Trans.R0,x,y+127000)
    instGC2 = cell.insert(CellInstArray(cell_ebeam_gc.cell_index(), t))

    # automated test label
    text = Text ("opt_in_TE_1550_device_%s_MZI3" % designer_name, t)
    cell.shapes(ly.layer(ly.TECHNOLOGY['Text'])).insert(text).text_size = 5/dbu

    # Y branches:
    instY1 = connect_cell(instGC1, 'opt1', cell_ebeam_y_dream, 'opt1')
    instY1.transform(Trans(20000,0))
    instY2 = connect_cell(instGC2, 'opt1', cell_ebeam_y_dream, 'opt1')
    instY2.transform(Trans(20000,0))

    # Spiral:
    instSpiral = connect_cell(instY2, 'opt2', cell_ebeam_delay, 'optA')
    instSpiral.transform(Trans(20000,0))

    # Waveguides:
    connect_pins_with_waveguide(instGC1, 'opt1', instY1, 'opt1', waveguide_type=waveguide_type)
    connect_pins_with_waveguide(instGC2, 'opt1', instY2, 'opt1', waveguide_type=waveguide_type)
    connect_pins_with_waveguide(instY1, 'opt2', instY2, 'opt3', waveguide_type=waveguide_type)
    connect_pins_with_waveguide(instY2, 'opt2', instSpiral, 'optA', waveguide_type=waveguide_type)
    connect_pins_with_waveguide(instY1, 'opt3', instSpiral, 'optB', waveguide_type=waveguide_type,turtle_B=[5,-90])

# Zoom out
zoom_out(cell)

# Export for fabrication, removing PCells
path = os.path.dirname(os.path.realpath(__file__))
filename = os.path.splitext(os.path.basename(__file__))[0]
if export_type == 'static':
    file_out = export_layout(cell, path, filename, relative_path = '..', format='oas', screenshot=True)
else:
    file_out = os.path.join(path,'..',filename+'.oas')
    ly.write(file_out)

# Verify
file_lyrdb = os.path.join(path,filename+'.lyrdb')
num_errors = layout_check(cell = cell, verbose=False, GUI=True, file_rdb=file_lyrdb)
print('Number of errors: %s' % num_errors)

# Display the layout in KLayout, using KLayout Package "klive", which needs to be installed in the KLayout Application
if Python_Env == 'Script':
    from SiEPIC.utils import klive
    klive.show(file_out, lyrdb_filename=file_lyrdb, technology=tech_name)
