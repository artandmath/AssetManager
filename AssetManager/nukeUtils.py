"""Functions to interact with Nuke."""

# Import built-in modules
import os
import sys

try:
    # Python 2
    string_types = basestring
except NameError:
    # Python 3
    string_types = str

# Import third party modules
NUKE_LOADED = True
try:
    import nuke
except ImportError:
    # We need some Qt to mimic nukes interface functions.
    from Qt import QtWidgets  # pylint: disable=no-name-in-module

    NUKE_LOADED = False

# Import internal modules
from AssetManager import constants


def node_exists(node):
    """Check if python node object node is still attached to a Node.

    Nuke throws a ValueError if node is not attached. This happens when the
    user deleted a node that is still in use by a python script.

    Args:
        node (nuke.Node): node python object

    Returns:
        bool: True if node exists.

    """
    try:
        node.name()
    except ValueError:
        return False

    return True


def getSelectedNodes(recurseGroups=False):
    """Get current selection.

    Returns:
        list: of nuke.Node

    """
    
    selection = []
    for Class in constants.ASSET_CLASSES:
        selection += nuke.selectedNodes(Class)
        #print(selection)

    if recurseGroups:
        for node in selection:
            if node.Class() == 'Group':
                with node:
                    selection += getSelectedNodes(recurseGroups)

    return selection

def getAllNodes(recurseGroups=False):
    """Get all selection.

    Returns:
        list: of nuke.Node

    """
    
    selection = []
    for Class in constants.ASSET_CLASSES:
        selection += nuke.allNodes(Class)
        #print(selection)

    if recurseGroups:
        for node in selection:
            if node.Class() == 'Group':
                with node:
                    selection += getSelectedNodes(recurseGroups)

    return selection

def int_rollover(value):
    """Simulate integer overflow to match Nuke's ColorChip_Knob values.

    Taken from: https://stackoverflow.com/a/7771363

    Args:
        value (int): Value to simulate int overflow on.

    Returns:
        int: Value after overflow.

    """
    if not -sys.maxint - 1 <= value <= sys.maxint:
        value = (value + (sys.maxint + 1)) % (2 * (sys.maxint + 1)) - sys.maxint - 1
    return value


def to_hex(color_rgb):
    """Convert `rgba` color values to hex.

    Args:
        color_rgb (tuple): color values 0-1.

    Returns:
        str: Color in hex notation.

    """
    color_hex = int('%02x%02x%02x%02x' % (int(color_rgb[0] * 255),
                                                  int(color_rgb[1] * 255),
                                                  int(color_rgb[2] * 255),
                                                  int(color_rgb[3] * 255)), 16)
    return int_rollover(color_hex)


def to_rgb(color_hex):
    """Convert hex to rgba.

    Author: Ivan Busquets

    Args:
        color_hex (int|long): Color in hex format.

    Returns:
         tuple: RGBA color in 0-1 range.

    """
    red = (0xFF & color_hex >> 24) / 255.0
    green = (0xFF & color_hex >> 16) / 255.0
    blue = (0xFF & color_hex >> 8) / 255.0
    alpha = (0xFF & color_hex >> 0) / 255.0

    return red, green, blue, alpha


def get_unique(seq):
    """Returns all unique items in of a list of strings.

    As opposed to casting to a ``set`` this preserves the order of the items.

    Examples:
        >>> get_unique(['abc', 'def', 'abc'])
        ['abc', 'def']

    Args:
        seq (:obj:`list` of :obj;`string`): list of strings.

    Returns:
        :obj:`list` of :obj;`string`: Unique strings.
        
    """
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def get_node_tile_color(node):
    """Return the node's tile color or default node color if not set.

    Args:
        node (nuke.Node): Node to get the ``tile_color`` from.

    Returns:
        :obj:`tuple` of :obj:`float`: Colors in rgba.

    """
    color = None
    tile_color_knob = node.knob('tile_color')
    if tile_color_knob:
        color = tile_color_knob.value()
    if not color:
        color = nuke.defaultNodeColor(node.Class())

    if color:
        return to_rgb(color)[:3]


def get_node_font_color(node, hex=False):
    """Get the label color of a node.

    Note:
        When returning the color in RGB, the alpha component is stripped as
        it is not important in the nodes font color.

    Args:
        node (nuke.Node): Node to get the font color from.
        hex (bool, optional): If True, return value in hex number else return
            the color converted to normalized rgb (default).

    Returns:
        :obj:`tuple` of :obj:`float`: Color in rgba.

    """
    color_knob = node.knob('note_font_color')
    if color_knob:
        color = color_knob.value()
        if hex:
            return color
        else:
            return to_rgb(color)[:3]


def get_node_classes(no_ext=True):
    """Return all available node classes (plugins).

    Args:
        no_ext: Strip file extension to return only class name.

    Returns:
        :obj:`list` of :obj:`string`: All available node classes.

    """
    if NUKE_LOADED:
        plugins = nuke.plugins(nuke.ALL | nuke.NODIR, "*." + nuke.PLUGIN_EXT)
    else:
        plugins = ['Merge2', 'Mirror', 'Transform']
    plugins = get_unique(plugins)
    if no_ext:
        plugins = [os.path.splitext(plugin)[0] for plugin in plugins]

    return plugins


def select_node(node, zoom=1):
    """Select node and (optionally) zoom DAG to given node.

    Warnings:
        If name of node inside a group is given,
        the surrounding group will be selected instead of the node

    Args:
        node (nuke.Node, str): node or name of node. If name of node inside a group is given,
            the surrounding group will be selected instead of the node.
        zoom (int, optimal): Zoom to given node. If zoom = 0, DAG will not
            be focused on the given node.

    """
    # Get the top-most parent nodes name.
    if isinstance(node, nuke.Node):
        full_name = node.fullName()
        if '.' in full_name:
            node = full_name.split('.')[0]

    # Starting from the node name get the top-most parent node.
    if isinstance(node, string_types):
        # if node is part of a group: select the group
        if "." in node:
            node_name = node.split(".")[0]
            node = nuke.toNode(node_name)

    # Select and zoom to Node.
    if isinstance(node, nuke.Node):
        node.selectOnly()
        if zoom:
            nuke.zoom(zoom, [node.xpos(), node.ypos()])


def shade_dag_nodes_enabled():
    """Check if nodes are shaded in DAG.

    Note:
        Skipping check of the preferences node since that counts towards the
        10 nodes limit in non-commercial edition.

    Returns:
        bool: True if nodes are shaded.

    """
    if not nuke.env.get('nc'):
        pref_node = nuke.toNode("preferences")
        shaded = pref_node['ShadeDAGNodes'].value()
    else:
        shaded = SHADE_DAG_NODES_NON_COMMERCIAL

    return shaded


def ask(prompt=""):
    """Ask user a yes/no question.

    Args:
        prompt (str, optional): Question to display.

    Returns:
        bool: Users answer.

    """
    if NUKE_LOADED:
        reply = nuke.ask(prompt)
    else:
        reply = QtWidgets.QMessageBox.question(None,
                                               PACKAGE_NICE_NAME,
                                               prompt,
                                               (QtWidgets.QMessageBox.Yes |
                                                QtWidgets.QMessageBox.No))
        reply = reply == QtWidgets.QMessageBox.Yes

    return reply
