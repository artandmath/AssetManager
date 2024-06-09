"""models to server and filter nodes data to the view."""

try:
    # Python 2
    string_types = basestring
except NameError:
    # Python 3
    string_types = str

# Import built-in modules
import sys
import re
import os

# Import third-party modules
import nuke  # pylint: disable=import-error
from Qt import QtCore, QtGui, QtWidgets  # pylint: disable=no-name-in-module

# Import local modules
from AssetManager import constants
from AssetManager import schema
from AssetManager import nukeUtils


def scalar(tpl, multiplier):
    """Multiply each value in tuple by scalar.

    Examples:
        >>> scalar((1.0, 2.0, 3.0), 2.0)
        (2.0, 4.0, 6.0)

    Args:
        tpl (tuple|list): Values to multiply.
        multiplier (float): Multiplier.

    Returns:
        tuple: tpl * multiplier

    """
    return tuple([multiplier * t for t in tpl])


def get_palette(widget=None):
    """Return the application's palette.

    Args:
        widget (QtWidgets.QWidget, optional): Current widget.

    Returns:
        QtGui.QPalette: The color palette of the current application or widget.

    """
    app = QtWidgets.QApplication.instance()  # type: QtWidgets.QApplication
    try:        
        return app.palette(widget)
    except AttributeError:
        # In Nuke 12, a QCoreApplication may be returned which does not
        # have a palette. In this case return a default QPalette which seems
        # to produce the same colors for `base` and `alternateBase` anyways.
        return QtGui.QPalette()


def bisect_case_insensitive(sorted_list, new_item):
    """Locate the insertion point for new_item to maintain sorted order.

    Taken from https://stackoverflow.com/a/41903429

    Args:
        sorted_list (list): Sorted list.
        new_item (str): Item to find sorted location for.

    Returns:
        int: Index at which point new_item must be inserted.

    """
    key = new_item.lower()
    low, high = 0, len(sorted_list)
    while low < high:
        mid = (low + high) // 2
        if key < sorted_list[mid].lower():
            high = mid
        else:
            low = mid + 1
    return low


def find_substring_in_dict_keys(dictionary,
                                key_str,
                                lower=True,
                                first_only=False,
                                substring=True):
    """Find keys that include key.

    TODO:
        test performance against:
        return list(key for k in d.iterkeys() if key_str in k.lower())

    Args:
        dictionary (dict): Dictionary to search in.
        key_str (str): Find this string in keys of dictionary
        lower (bool): case insensitive matching.
        first_only (bool): If True, return only first found key.

    Returns:
        list: Found keys.

    """
    result = []
    for key in dictionary.keys():
        if lower:
            key = key.lower()
            key_str = key_str.lower()

        if substring:
            if key_str in key:
                if first_only:
                    return [key]
                else:
                    result.append(key)
        else:
            if key_str == key:
                if first_only:
                    return [key]
                else:
                    result.append(key)
    return result


class ListFilterModel(QtCore.QSortFilterProxyModel):
    """Abstract class that defines how the filter is set.

    The derived FilterProxyModel should do substring matching if
    length of filter is 1.

    """

    def __init__(self, parent, filter_delimiter=constants.FILTER_DELIMITER):
        super(ListFilterModel, self).__init__(parent)
        self.filter_list = None
        self.filter_delimiter = filter_delimiter

    def set_filter_str(self, filter_str):
        """Set filter as string with delimiter.

        Args:
            filter_str (str): Filter to use.

        """
        filter_list = [filter_s.strip().lower() for filter_s
                       in filter_str.split(self.filter_delimiter)]
        self.filter_list = filter_list
        self.invalidateFilter()

    def match(self, string):
        """Check if string is in filter_list.

        Check for substring only when filtering by one item.

        Args:
            string (str): match this string against filter

        Returns:
            bool: True if string is in ``filter_list``.

        """
        matching = True

        if not self.filter_list:
            return matching

        # Case sensitive filtering is confusing and unnecessary.
        string = string.lower()

        # Check for full name in case filter list is more than one item.
        if len(self.filter_list) > 1:
            matching = string in self.filter_list
        # Check for substring.
        elif len(self.filter_list) == 1:
            matching = self.filter_list[0] in string

        return matching


class HeaderHorizontalFilterModel(ListFilterModel):
    """Filter by knob name."""

    # pylint: disable=invalid-name, unused-argument
    def filterAcceptsColumn(self, column, parent):
        """Filter header with set filter.

        Args:
            column (int): Current column.
            parent (QtCore.QModelIndex, ignored): The sources parent.

        Returns:
            bool: True if header matches the filter.

        """
        if not self.filter_list:
            return True

        header_name = self.sourceModel().headerData(column,
                                                    QtCore.Qt.Horizontal,
                                                    QtCore.Qt.DisplayRole)
        return self.match(header_name)

'''
class NodeNameFilterModel(ListFilterModel):
    """Filter the model by nodename."""

    # pylint: disable=invalid-name, unused-argument
    def filterAcceptsRow(self, row, parent):
        """Filter header with set filter.

        Args:
            row (int): Current row.
            parent (QtCore.QModelIndex, ignored): The sources parent.

        Returns:
            bool: True if header matches the filter.

        """
        if not self.filter_list:
            return True

        header_name = self.sourceModel().headerData(row,
                                                    QtCore.Qt.Vertical,
                                                    QtCore.Qt.DisplayRole)
        return self.match(header_name)
'''

class NodeFilterModel(ListFilterModel):
    """Filter by node classes."""

    # pylint: disable=invalid-name, unused-argument
    def filterAcceptsRow(self, row, parent):
        """Filter by node classes.

        Args:
            row (int): Current row.
            parent (QtCore.QModelIndex): Parent index.

        Returns:
            bool: True if node's class matches the filter.

        """
        if not self.filter_list:
            return True
        node = self.sourceModel().headerData(row,
                                             QtCore.Qt.Vertical,
                                             QtCore.Qt.UserRole)
        matchStr = 'Name:{0} >> Class:{1} >> File:{2}'.format(node.name(),node.Class(),node['file'].value())
        return self.match(matchStr)


# pylint: disable=too-few-public-methods
class EmptyColumnFilterModel(QtCore.QSortFilterProxyModel):
    """Filter out every empty column.

    Notes:
        This Filter is fairly expensive: O=pow(n,2) because it needs to run
        for every row and column.

    """

    # pylint: disable=invalid-name, unused-argument
    def filterAcceptsColumn(self, column, parent):
        """For every node check if column's name is in the node's knobs.

        Args:
            column (int): Current column.
            parent (QtCore.QModelIndex): The sources parent.

        Returns:
            bool: True if at least one node has a knob for current column.

        """
        header_name = self.sourceModel().headerData(column,
                                                    QtCore.Qt.Horizontal,
                                                    QtCore.Qt.DisplayRole)

        for row in range(self.sourceModel().rowCount()):
            node = self.sourceModel().headerData(row, QtCore.Qt.Vertical,
                                                 QtCore.Qt.UserRole)
            if header_name in node.knobs():
                return True
        return False


class NodeWrapper():
    def __init__(self, node, schema) -> None:
        super(NodeWrapper, self).__init__()
        self._node = node
        self._schema = schema
        self._tokens = self._schema.filePathToEditableTokens(self.file)

    @property
    def node(self):
        return self._node

    @property
    def name(self):
        return self._node.name()
    
    @property
    def file(self):
        return self._node['file'].value()

    @file.setter
    def file(self, path):
        undo = nuke.Undo()
        undo.begin("Change value of {0}['file']".format(self.name))
        self._node['file'].setValue(path)
        self._tokens = self._schema.filePathToEditableTokens(path)
        undo.end()
       
    @property
    def tokens(self):
        return self._tokens
    
    @property
    def isValid(self):
        for key in self.tokens.keys():
            if self.tokens[key] == constants.TOKEN_ERROR:
                return False
        return True




# pylint: disable=invalid-name
class NodeTableModel(QtCore.QAbstractTableModel):
    """Digest and store nodes and serve their data."""

    def __init__(self, nodes=None, schemaStr=''):
        """

        Args:
            nodes (:obj:`list` of :obj:`nuke.Node`, optional): Nodes to
                represent in the model.

        """
        super(NodeTableModel, self).__init__()

        self._schema = schema.Schema(schemaStr)

        self._nodeList = nodes or []  # type: list
        self._nodeWrapperDict = {node.name(): NodeWrapper(node, self._schema) for index, node in enumerate(self._nodeList)} or {}  # type: dict

        self.palette = get_palette()  # type: QtGui.QPalette

    @property
    def schema(self):
        """
        TODO: Document
        """
        return self._schema

    @property
    def nodeList(self):
        """
        TODO: Document
        """
        return self._nodeList

    @property
    def nodeNames(self):
        """
        TODO: Document
        """
        return [node.name() for node in self.nodeList]

    @property
    def nodeWrapperDict(self):
        """
        TODO: Document
        """
        return self._nodeWrapperDict

    @property
    def columnHeaders(self):
        headers = self.schema.keysEditable
        headers.append('file')
        return headers

    @nodeList.setter
    def nodeList(self, nodes):
        newNodes = set(nodes) - set(self.nodeList)
        removeNodes = set(self.nodeList) - set(nodes)

        for node in removeNodes:
            if nukeUtils.node_exists(node):
                removeIndex = self.nodeList.index(node)
                self.removeRows(parent=QtCore.QModelIndex(),
                                row=removeIndex,
                                count=1)
                for key in self.nodeWrapperDict.keys():
                    if self.nodeWrapperDict[key].node == node:
                         self.nodeWrapperDict.pop(key, None)

        for node in newNodes:
            insertIndex = bisect_case_insensitive(self.nodeNames,
                                                   node.name())
            self.insertRows(parent=QtCore.QModelIndex(),
                            row=insertIndex,
                            count=1,
                            items=[node])

    def rowCount(self, parent=QtCore.QModelIndex()):
        """Number of nodes in the model.

        Args:
            parent (QtCore.QModelIndex, optional): Parent index.

        Returns:
            int: Number of nodes.

        """

        if parent.isValid():
            return 0

        if not self.nodeList:
            return 0

        return len(self.nodeList)

    def columnCount(self, parent):
        """Number of columns in the model.

        Note: When implementing a table based model,
        PySide.QtCore.QAbstractItemModel.columnCount()
        should return 0 when the parent is valid.

        Args:
            parent (QtCore.QModelIndex): Parent index.

        Returns:
            int: Number of columns.

        """
        if parent.isValid():
            return 0

        if not self.nodeList:
            return 0

        return len(self.columnHeaders)

    def setupModelData(self):
        """Read all knob names from set self.node_list to define header.

        First all knobs to display are collected. To match this list, all
        knobs to remove and to add are collected and removed and inserted as
        needed.

        """

        # Collect all knobs to display.
        # Iterating over copy of the node list to not saw off the tree
        # we're sitting on.
        for node in list(self.nodeList):
            # If node was deleted, remove node and return.
            if not nukeUtils.node_exists(node):
                self.removeRows(row=self.nodeList.index(node),
                                count=1,
                                parent=QtCore.QModelIndex(),
                                setupModelData=False)
                for key in self.nodeWrapperDict.keys():
                    if nodeWrapperDict[key].node == node:
                         nodeWrapperDict.pop(key, None)
                # Continue with the next node, since we removed this node.
                continue

        self._nodeWrapperDict = {node.name(): NodeWrapper(node, self._schema) for index, node in enumerate(self._nodeList)}

        # This is dirty. Removing each column and then re-creatng it
        self.removeColumns(parent=QtCore.QModelIndex(),
                            column=0,
                            count=len(self.columnHeaders))

        self.insertColumns(parent=QtCore.QModelIndex(),
                            column=0,
                            count=len(self.columnHeaders),
                            items=self.columnHeaders)

    def insertColumns(self, column, count, parent, items):
        """Add items to header.

        Args:
            parent (QtCore.QModelIndex): Parent index.
            column (int): index of new columns.
            count (int, unused): Number of items to add (ignored).
            item (list): Items to add.

        Returns:
            bool: True if items were added.

        """
        count = len(items)
        self.beginInsertColumns(parent,
                                column,
                                column + count - 1)
        for i, item in enumerate(items):
            pass
        self.endInsertColumns()
        return True

    def removeColumns(self, column, count, parent):
        """Remove columns.

        Args:
            parent (QtCore.QModelIndex): Parent index.
            first (int): First column to remove.
            last (int): Last column to remove.

        Returns:
            bool: True if successfully removed.

        """
        self.beginRemoveColumns(parent, column, column + count - 1)

        for col in reversed(range(column, column + count)):
            pass
        self.endRemoveColumns()
        return True

    def insertRows(self, row, count, parent, items):
        """Add consecutive rows.

        Args:
            parent (QtCore.QModelIndex): Parent index.
            count (int, unused): Number of items to add).
            item (list): items to add.

        Returns:
            bool: True if items added.

        """
        count = len(items)
        self.beginInsertRows(parent,
                             row,
                             row + count - 1)
        for i, item in enumerate(items):
            self._nodeList.insert(row + i, item)
        self.endInsertRows()

        self.setupModelData()

        return True

    def removeRows(self, row, count, parent, setupModelData=True):
        """Remove consecutive rows.

        Args:
            row (int): First row to remove.
            count (int): Number of rows to remove.
            parent (QtCore.QModelIndex): Parent index.
            setupModelData (bool): Setup model after removing row.
                Disable to avoid recursion.

        Returns:
            bool: True if successfully removed.

        """
        self.beginRemoveRows(parent, row, row + count - 1)
        for i in reversed(range(row, row + count)):
            self._nodeList.pop(i)
        self.endRemoveRows()

        # Update horizontal header.
        if setupModelData:
            self.setupModelData()
        return True

    def data(self, index, role):
        """Returns the header data.

        For UserRole this returns the node or knob, depending on given
        orientation.

        Args:
            index (QtCore.QModelIndex): return headerData for this index
            role (QtCore.int): the current role
                QtCore.Qt.BackgroundRole: background color if knob is animated
                QtCore.Qt.EditRole: value of knob at current index
                QtCore.Qt.DisplayRole: current value of knob as str
                QtCore.Qt.UserRole: the knob itself at current index

        Returns:
            str|bool|tuple|list|nuke.Knob: The value of the current knob or the
                knob itself.

        """
        row = index.row()
        col = index.column()

        if not self.nodeList:
            self.setupModelData()
            return

        nodeWrapper = self.nodeWrapperDict[self.nodeList[row].name()]
        # Return early if node was deleted to prevent access to detached
        # python node object.
        if not nukeUtils.node_exists(nodeWrapper.node):
            self.removeRows(parent=QtCore.QModelIndex(),
                            row=row,
                            count=1)
            return

        if role == QtCore.Qt.CheckStateRole:
            return None
        if role == QtCore.Qt.TextAlignmentRole:
            return None
        
        if self.columnHeaders[col] != 'file':
            key = self.schema.keysEditable[col]
            data = nodeWrapper.tokens[key]
            if not data:
                if role == QtCore.Qt.ForegroundRole:
                    return QtGui.QColor('#FF7F50')
                if role == QtCore.Qt.DisplayRole:
                    data = 'None'
            else:
                if data == constants.TOKEN_ERROR:
                    if role == QtCore.Qt.ForegroundRole:
                        return QtGui.QColor(QtCore.Qt.red)
                    if role == QtCore.Qt.DisplayRole:
                        return 'ERROR'
        else:
            data = nodeWrapper.file
            if role == QtCore.Qt.ForegroundRole:
                return QtGui.QColor('#777777')

        '''
        if role == QtCore.Qt.FontRole:
            if not nodeWrapper.isValid:
                font = QtGui.QFont()
                font.setStrikeOut(True)
                return font
        '''

        if role == QtCore.Qt.ForegroundRole:
            if not nodeWrapper.isValid:
                return QtGui.QColor('#777777')

        if role == QtCore.Qt.DisplayRole:
            return data

        elif role == QtCore.Qt.EditRole:
            return data

        elif role == QtCore.Qt.UserRole:
            if not nodeWrapper.isValid:
                return None
            if self.columnHeaders[col] != 'file':
                return data

        

    @staticmethod
    def safe_string(string):
        """Encode unicode to string because nuke knobs don't accept unicode.

        Args:
            string: Encode this string.

        Todo:
            Fix `unicode` type comparison for Python 3.

        Returns:
            str: String encoded or string unchanged if not unicode.

        """

        # Check if running in Python 3
        if sys.version_info.major >= 3:
            return string

        if isinstance(string, unicode):
            return string.encode('utf-8')
        else:
            return string

    def setData(self, index, value, role):
        """Sets edited data to node.

        Warnings:
            Currently this only works for a few knob types.

        Args:
            index (QtCore.QModelIndex): Current index.
            value (object): New value.
            role (QtCore.Qt.int): Current Role. Only EditRole supported.

        Returns:
            bool: True if successfully set knob to new value, otherwise False.

        """
        if not index.isValid():
            return

        if role == QtCore.Qt.EditRole:
            row = index.row()
            col = index.column()
            nodeWrapper = self.nodeWrapperDict[self.nodeList[row].name()]

            key = self.schema.keysEditable[col]
            tokens = self.schema.filePathToTokens(nodeWrapper.file)
            tokens[key] = value
            path = self.schema.tokensToFilePath(tokens)

            for key in nodeWrapper.tokens.keys():
                if nodeWrapper.tokens[key] == constants.TOKEN_ERROR:
                    return True

            nodeWrapper.file = path

            return True
        return False

    def flags(self, index):
        """Make cell selectable and editable for enabled knobs.

        Args:
            index (QtCore.QModelIndex): Current index.

        Returns:
            QtCore.Qt.ItemFlag: Flag for current cell.

        """
        row = index.row()
        node = self.nodeList[row]

        flags = QtCore.Qt.NoItemFlags

        schemaVar = self.data(index, QtCore.Qt.UserRole)
        if schemaVar != None:
            flags |= QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled ^ QtCore.Qt.ItemIsUserCheckable
        return flags
    
    def headerData(self, section, orientation, role):
        """Returns the header data.

        For ``UserRole`` this returns the node or knob, depending on given
        orientation.

        Args:
            section (QtCore.int): return headerData for this section
            orientation (QtCore.Qt.Orientation): header orientation
            role (QtCore.int): the current role.
                QtCore.Qt.DisplayRole: name of node or knob
                QtCore.Qt.UserRole: the node or knob itself

        Returns:
            str|nuke.Knob: The knob or it's name.

        """
        if orientation == QtCore.Qt.Horizontal:
            if section >= len(self.columnHeaders):
                return None

            if role == QtCore.Qt.DisplayRole:
                key = self.columnHeaders[section]
                if key != 'file':
                    return '@{0}    '.format(key)
                else:
                    return key
            elif role == QtCore.Qt.UserRole:
                return self.columnHeaders[section]
            elif role == QtCore.Qt.ForegroundRole:
                key = self.columnHeaders[section]
                if key != 'file':
                    if bool(os.environ.get('ASSET_MANAGER_ENABLE_COLOR', True)):
                        return QtGui.QColor(self.schema.tokenColors[key])   
            elif role == QtCore.Qt.BackgroundRole:
                key = self.columnHeaders[section]
                if key == 'file':
                    return QtGui.QColor('#444444')
            return None

        elif orientation == QtCore.Qt.Vertical:
            if section >= len(self.nodeList):
                return None

            node = self.nodeList[section]  # type: nuke.Node
            if not nukeUtils.node_exists(node):
                self.removeRows(row=section,
                                count=1,
                                parent= QtCore.QModelIndex())
                return

            if role == QtCore.Qt.DisplayRole:
                return node.name()
            elif role == QtCore.Qt.UserRole:
                return node
            elif role == QtCore.Qt.BackgroundRole:
                return QtGui.QBrush(QtGui.QColor.fromRgbF(
                    *(nukeUtils.get_node_tile_color(node))))
            elif role == QtCore.Qt.ForegroundRole:
                return QtGui.QPen(QtGui.QColor.fromRgbF(
                    *(nukeUtils.get_node_font_color(node))))
