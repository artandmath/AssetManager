"""Define all constant variables here."""

# pylint: disable=import-error
import nuke

PACKAGE_NICE_NAME = 'Asset Manager'

SCHEMA_DEFAULT = '/shows/{@show}/{@sequence}/{@shot}/{#product}/{@role}/{@show}{_@sequence}{_@shot}{_@role}{_@asset}{*_@variant}{_@version}{_@resolution}/{@show}{_@sequence}{_@shot}{_@role}{_@asset}{*_@variant}{_@version}{_@resolution}{*.#padding}{.#extension}'
SCHEMA_VAR_DELIMETERS = r'(?<=\{@).+?(?=\})'
SCHEMA_VAR_OPEN_DELIMETER = r'{@'
SCHEMA_VAR_CLOSE_DELIMETER = r'}'
SCHEMA_CONST_DELIMETERS = r'(?<=\{!).+?(?=\})'
SCHEMA_CONST_OPEN_DELIMETER = r'{!'
SCHEMA_CONST_CLOSE_DELIMETER = r'}'

VALID_DELIMETERS = ['_','-','.']

FILTER_DELIMITER = ','

ASSET_CLASSES = ['Read','DeepRead','ReadGeo','Camera2','Camera3','Camera4','Group','LiveGroup','Write']

FILTER_DEFAULTS = ['Class:Read','Class:DeepRead','Class:ReadGeo','Class:Camera2','-Class:Write']

# Schema token types

TOKEN_CONST = 'constant'
TOKEN_EDIT_VAR = 'userEditableVariable'
TOKEN_HIDDEN_VAR = 'nonEditableVariable'
TOKEN_ERROR = '<<!!ERROR!!>>'
TOKEN_NONE = '<<!!NONE!!>>'
# Token colors

colorsMutedList = ['OrangeRed',
                    'Tomato',
                    'Coral',
                    'DarkKhaki',
                    'MediumSeaGreen',
                    'DarkCyan',
                    'DodgerBlue',
                    'SlateBlue',
                    'Plum']
colorsBrightList = ['Crimson',
                    'OrangeRed',
                    'Orange',
                    'Khaki',
                    'LightGreen',
                    'Cyan',
                    'DeepSkyBlue',
                    'Violet',
                    'HotPink']
colorsMutedDict = {'FireBrick':'#B22222',
                    'Tomato':'#FF6347',
                    'Coral':'#FF7F50',
                    'DarkKhaki':'#BDB76B',
                    'MediumSeaGreen':'#3CB371',
                    'DarkCyan':'#008B8B',
                    'DodgerBlue':'#1E90FF',
                    'SlateBlue':'#6A5ACD',
                    'Plum':'#DDA0DD'}
colorsBrightDict = {'Crimson':'#DC143C',
                    'OrangeRed':'#FF4500',
                    'Orange':'#FFA500',
                    'Khaki':'#F0E68C',
                    'LightGreen':'#90EE90',
                    'Cyan':'#00FFFF',
                    'DeepSkyBlue':'#00BFFF',
                    'Violet':'#EE82EE',
                    'HotPink':'#FF69B4'}

TOKEN_COLORS_LIST = colorsMutedList+colorsBrightList
TOKEN_COLORS_DICT = {**colorsMutedDict, **colorsBrightDict}


# Knob classes that can't be edited directly
READ_ONLY_KNOBS = [
    nuke.Axis_Knob,
    nuke.Transform2d_Knob,
]

# Colors
# knob is animated
KNOB_ANIMATED_COLOR = (0.312839, 0.430188, 0.544651)
# knob has key at current frame
KNOB_HAS_KEY_AT_COLOR = (0.165186, 0.385106, 0.723738)

# Mix background color with node color by this amount
# if cell has no knob:
CELL_MIX_NODE_COLOR_AMOUNT_NO_KNOB = .08
# if cell has knob:
CELL_MIX_NODE_COLOR_AMOUNT_HAS_KNOB = 0.3

# Editors:
# Toolbars:
BUTTON_WIDTH = 200
BUTTON_SPACER = 40
FILTER_WIDTH = 156
LABEL_SPACER = 6

# Cell size:
EDITOR_CELL_WIDTH = 50
EDITOR_CELL_HEIGHT = 22

# editor precision
EDITOR_DECIMALS = 8

# Ask for user confirmation before loading more than this many nodes.
NUM_NODES_WARN_BEFORE_LOAD = 100

# Shading mode follows preferences when not in non-commercial mode.
# Skip checking the preferences node since that counts towards the
# 10 nodes limit in non-commercial edition.
SHADE_DAG_NODES_NON_COMMERCIAL = True
