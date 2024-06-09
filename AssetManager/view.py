"""Build the widget and stack the models."""

# Import third party modules
# pylint: disable=import-error
import nuke
import os
import imp

# Keeping this for development to enable auto-completion.
from Qt import QtCore, QtGui, QtWidgets, __binding__  # pylint: disable=no-name-in-module

# Import internal modules
from AssetManager import constants
from AssetManager import nukeUtils
from AssetManager import model
from AssetManager import delegate
imp.reload(delegate)

# pylint: disable=invalid-name
class NodeHeaderView(QtWidgets.QHeaderView):
    """This header view selects and zooms to node of clicked header section.

    Shows properties of node if double clicked.

    """

    def __init__(self, orientation=QtCore.Qt.Vertical, parent=None):
        """Construct the header view.

        Args:
            orientation (QtCore.Qt.Orientation): Orientation of the header.
            parent (QtWidgets.QWidget, optional): Parent widget.

        """
        super(NodeHeaderView, self).__init__(orientation, parent)

        if "PySide2" in __binding__:
            self.setSectionsClickable(True)
        elif "PySide" in __binding__:
            self.setClickable(True)

        self.shade_dag_nodes_enabled = nukeUtils.shade_dag_nodes_enabled()

        self.sectionClicked.connect(self.select_node)
        self.sectionDoubleClicked.connect(self.show_properties)

        self.setDefaultSectionSize(constants.EDITOR_CELL_HEIGHT)
        self.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self.setStretchLastSection(False)

    def paintSection(self, painter, rect, index):
        """Mimic Nuke's way of drawing nodes in DAG.

        Args:
            painter (QtGui.QPainter): Painter to perform the painting.
            rect (QtCore.QRect): Section to paint in.
            index (QtCore.QModelIndex): Current logical index.

        """
        painter.save()
        QtWidgets.QHeaderView.paintSection(self, painter, rect, index)
        painter.restore()

        bg_brush = self.model().headerData(index,
                                           QtCore.Qt.Vertical,
                                           QtCore.Qt.BackgroundRole)  # type: QtGui.QBrush

        fg_pen = self.model().headerData(index,
                                         QtCore.Qt.Vertical,
                                         QtCore.Qt.ForegroundRole)  # type: QtGui.QPen

        if self.shade_dag_nodes_enabled:
            gradient = QtGui.QLinearGradient(rect.topLeft(),
                                             rect.bottomLeft())
            gradient.setColorAt(0, bg_brush.color())
            gradient_end_color = model.scalar(bg_brush.color().getRgbF()[:3],
                                              0.6)
            gradient.setColorAt(1, QtGui.QColor.fromRgbF(*gradient_end_color))
            painter.fillRect(rect, gradient)
        else:
            painter.fillRect(rect, bg_brush)

        rect_adj = rect
        rect_adj.adjust(-1, -1, -1, -1)
        painter.setPen(fg_pen)
        text = self.model().headerData(index,
                                       QtCore.Qt.Vertical,
                                       QtCore.Qt.DisplayRole)
        painter.drawText(rect, QtCore.Qt.AlignCenter, text)
        painter.setPen(QtGui.QPen(QtGui.QColor.fromRgbF(0.0, 0.0, 0.0)))
        painter.drawRect(rect_adj)

    def get_node(self, section):
        """Return node at current section (index).

        Args:
            section (int): Index of current section in the models header data.

        Returns:
            node (nuke.Node): Node at the current section.

        """
        return self.model().headerData(section,
                                       QtCore.Qt.Vertical,
                                       QtCore.Qt.UserRole)

    def select_node(self, section):
        """Select node and zoom node graph.

        Args:
            section (int): Index of the node to zoom to.

        """
        node = self.get_node(section)
        nukeUtils.select_node(node, zoom=1)

    def show_properties(self, section):
        """Open properties bin for node at current section.

        Args:
            section (int): Index of the node to show in properties bin.

        """
        node = self.get_node(section)
        nuke.show(node)


class NodeTableView(QtWidgets.QTableView):
    """Table with multi-cell editing."""

    def __init__(self, parent=None):
        super(NodeTableView, self).__init__(parent)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)

        self.delegate = delegate.ItemDelegate(self)
        self.setItemDelegate(self.delegate)

        self.setHorizontalScrollMode(QtWidgets.QTableView.ScrollPerPixel)
        self.setVerticalScrollMode(QtWidgets.QTableView.ScrollPerPixel)

        self.nodesHeader = NodeHeaderView(QtCore.Qt.Vertical, parent)
        self.setVerticalHeader(self.nodesHeader)

        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        self.horizontalHeader().setMinimumSectionSize(constants.EDITOR_CELL_WIDTH)
        self.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)
        self.setWordWrap(False)
        self.horizontalHeader().setSortIndicatorShown(False)

        

    def selectionCommand(self, index, event):
        """Returns the SelectionFlags to be used when updating a selection.

        Allow to keep editing the same selection when clicking into a checkbox.
        The selection change can't be prevented in the delegate, so we have to
        return the `NoUpdate` flag here to keep the selection.

        Args:
            index (QtCore.QModelIndex): Current index.
            event (QtCore.QEvent): Current event.

        Returns:
             QtCore.QItemSelectionModel.Flag: The selection update flag.

        """
        try:
            pos = event.pos()
        except AttributeError:
            # Event is does not have a position ie. KeyPressEvent.
            return super(NodeTableView, self).selectionCommand(index, event)

        index = self.indexAt(pos)
        if not index.isValid():
            return super(NodeTableView, self).selectionCommand(index, event)

        # Prevent loosing selection when clicking a checkbox.
        if event.type() in (QtCore.QEvent.MouseButtonRelease, QtCore.QEvent.MouseMove,
                            QtCore.QEvent.MouseButtonPress):
            data = index.model().data(index, QtCore.Qt.EditRole)
            if isinstance(data, bool):
                checkbox_rect = self.delegate.get_check_box_rect(rect=self.visualRect(index))
                if checkbox_rect.contains(event.pos()):
                    return QtCore.QItemSelectionModel.NoUpdate

        return super(NodeTableView, self).selectionCommand(index, event)


    def mouseReleaseEvent(self, event):
        """Enter edit mode after single click.

        Enter the edit mode on mouse release after dragging a selection or
        selecting a single cell.

        Args:
            event (QtCore.QEvent): The current mouse event.

        """
        if event.button() == QtCore.Qt.LeftButton:
            if event.type() == QtCore.QEvent.MouseButtonRelease:
                index = self.indexAt(event.pos())
                if index.isValid():
                    self.edit(index)
                else:
                    # Close an active editor if it is open.
                    index = self.currentIndex()
                    editor = self.indexWidget(index)
                    if editor:
                        self.commitData(editor)
                        self.closeEditor(editor, QtWidgets.QAbstractItemDelegate.NoHint)

        if event.button() == QtCore.Qt.RightButton:
            # TODO: implement right click options
            pass

        return super(NodeTableView, self).mouseReleaseEvent(event)

    def commitData(self, editor):
        """Set the current editor data to the model for the whole selection.

        Args:
            editor (QtWidgets.QWidget): The current editor.

        """
        # Call parent commitData first.
        super(NodeTableView, self).commitData(editor)

        # self.currentIndex() is the QModelIndex of the cell just edited
        current_index = self.currentIndex()  # type: QtCore.QModelIndex

        # Return early if nothing is selected. This can happen when editing
        # a checkbox that doesn't rely on selection.
        if not current_index.isValid():
            return

        _model = self.currentIndex().model()
        # Get the value that the user just submitted.
        value = _model.data(self.currentIndex(), QtCore.Qt.EditRole)
        edited_knob = _model.data(self.currentIndex(), QtCore.Qt.UserRole)

        current_row = self.currentIndex().row()
        current_column = self.currentIndex().column()

        # Selection is a list of QItemSelectionRange instances.
        for isr in self.selectionModel().selection():
            rows = range(isr.top(), isr.bottom() + 1)
            columns = range(isr.left(), isr.right() +1)
            for row in rows:
                for col in columns:
                    if row != current_row or col != current_column:
                        # Other rows and columns are also in the selection.
                        # Create an index so we can apply the same value
                        # change.
                        idx = _model.index(row, col)
                        knob = _model.data(idx, QtCore.Qt.UserRole)
                        if type(knob) == type(edited_knob):
                            _model.setData(idx, value, QtCore.Qt.EditRole)


class MultiCompleter(QtWidgets.QCompleter):
    """Complete multiple words in a QLineEdit, separated by a delimiter.

    Args:
        model_list (QtCore.QStringListModel or list): Words to complete.
        delimiter (str, optional): Separate words by this string.
            (default: ",").

    """
    def __init__(self, model_list=None, delimiter=","):
        super(MultiCompleter, self).__init__(model_list)
        self.setCompletionMode(QtWidgets.QCompleter.InlineCompletion)
        self.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.delimiter = delimiter

    def pathFromIndex(self, index):
        """Complete the input.

        Args:
            index (QtCore.QModelIndex): Current index.

        Returns:
            str: Completed input.

        """
        path = super(MultiCompleter, self).pathFromIndex(index)
        lst = str(self.widget().text()).split(self.delimiter)
        if len(lst) > 1:
            path = '%s%s %s' % (self.delimiter.join(lst[:-1]),
                                self.delimiter, path)
        return path

    def splitPath(self, path):
        """Split and strip the input.

        Splits the given path into strings that are used to match at each level
        in the model().

        Args:
            path (str): String to split.

        Returns:
            :obj:`list` of :obj:`string`: Stirng split by the delimiter.

        """
        path = str(path.split(self.delimiter)[-1]).lstrip(' ')
        return [path]

'''
# pylint: disable=too-few-public-methods
class KeepOpenMenu(QtWidgets.QMenu):
    """Menu that stays open to allow toggling multiple actions.

    Warnings: broken, manu actually doesn't stay open.
    TODO: keep menu open.

    """

    def eventFilter(self, obj, event):
        """Eat the mouse event but trigger the objects action.

        Filters events if this object has been installed as an event filter
        for the watched object.

        Args:
            obj (QtCore.QObject): Watched object.
            event (QtCore.QEvent): Current event.

        Returns:
            bool: True if the event is filtered out, otherwise False (to
                process it further).

        """
        if event.type() in [QtCore.QEvent.MouseButtonRelease]:
            if isinstance(obj, QtWidgets.QMenu):
                if obj.activeAction():
                    # if the selected action does not have a submenu
                    if not obj.activeAction().menu():

                        # eat the event, but trigger the function
                        obj.activeAction().trigger()
                        return True
        return super(KeepOpenMenu, self).eventFilter(obj, event)


# pylint: disable=too-few-public-methods
class CheckAction(QtWidgets.QAction):
    """A checkable QAction."""

    def __init__(self, text, parent=None):
        """Create a checkable QAction.

        Args:
            text (str): text to display on QAction
            parent (QtWidgets.QWidget): parent widget (optional).

        """
        super(CheckAction, self).__init__(text, parent)
        self.setCheckable(True)
'''

# pylint: disable=line-too-long, too-many-instance-attributes
class AssetManagerWidget(QtWidgets.QWidget):
    """The main GUI for the table view and filtering.

    Filtering is achieved by stacking multiple custom QSortFilterProxyModels.
    The node list and filters are accessible through pythonic properties.

    Examples:
        >>> from node_table import view
        >>> table = view.NodeTableWidget()
        >>> table.node_list = nuke.selectedNodes()
        >>> table.node_class_filter = 'Merge2, Blur'
        >>> table.knob_name_filter = 'disabled, cached'

    """

    def __init__(self, node_list=None, parent=None):
        """    Args:
        node_list (list): list of nuke.Node nodes (optional).
        parent (QtGui.QWidget): parent widget (optional)

        Args:
            node_list (:obj:`list` of :obj:`str`, optional): Nodes to display.
            parent (QtWidgets.QWidget, optional): Parent widget.

        """
        super(AssetManagerWidget, self).__init__(parent)

        # Widget
        self.setWindowTitle(constants.PACKAGE_NICE_NAME)

        # Variables:
        self._nodeList = []  # make sure it's iterable
        self._grouped_nodes = False
        self._nodeFilter = None

        # Content
        # TODO: untangle this bad mix of ui and controller functions.
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)

         # Schema Override Widget
        self.schemaOverrideWidget = QtWidgets.QWidget(self)
        self.schemaOverrideLayout = QtWidgets.QHBoxLayout(self.schemaOverrideWidget)
        self.schemaOverrideLayout.setContentsMargins(0, 0, 0, 0)
        self.schemaOverrideWidget.setLayout(self.schemaOverrideLayout)

        # Schema user override
        enableOverride = bool(os.environ.get('ASSET_MANAGER_ENABLE_OVERRIDE', True))
        if enableOverride:
            self.schemaOverrideLabel = QtWidgets.QLabel('Schema:')
            self.schemaOverrideLayout.addWidget(self.schemaOverrideLabel)
            self.schemaOverrideLineEdit = QtWidgets.QLineEdit(self.schemaOverrideWidget)
            self.schemaOverrideLineEdit.setPlaceholderText("By default Asset Manager will extract schema tokens from $ASSET_MANAGER_SCHEMA, see tool tip for schema override syntax")
            self.schemaOverrideLineEdit.setToolTip("""
                                                    Filepath schemas are built from token variables in the form of:<br><br>
                                                    <b>{@token}</b> for user editable token variable<br>
                                                    <b>{#token}</b> for non-editiable token variable<br>
                                                    <b>{*@token}</b> for optional user editable token variable<br>
                                                    <b>{*#token}</b> for optional non-editable token variable<br>
                                                    Anything else in the string is constant<br><br>
                                                    
                                                    Syntax examples:<br><br>
                                                    <i>/shows/{@show}/{@sequence}/{@shot}/{#product}/{@role}/{@sequence}{_@shot}{_@role}{_@asset}{*_@variant}{_@version}{_@resolution}/{@sequence}{_@shot}{_@role}{_@asset}{*_@variant}{_@version}{_@resolution}{.#padding}{.#extension}</i><br><br>
                                                    <i>/shows/{@SHOW}/s{@SEQ}/{@SHOT}/{#PROD}/{@ROLE}/s{@SEQ}{_@SHOT}{_@ROLE}{_@ASSET}{*_@VAR}{_@VERS}{_@RES}/s{@SEQ}{_@SHOT}{_@ROLE}{_@ASSET}{*_@VAR}{_@VERS}{_@RES}.%04d{.#EXT}</i><br><br>
                                                    <i>/jobs/{@Client}/{@Job}/{@Entity}/outputs/{@Task}/{@Entity}{_@Task}{_@Asset}{_@Version}{*/@Variant}/{@Entity}{_@Task}{_@Asset}{_@Version}{*_@Variant}{.#Padding}{.#Extension}</i><br><br>

                                                    A character after the open bracket '{' and before '@' or '#" denotes a token delimeter. It will usually be '_' or '-' or '.'.
                                                    The delimeter (along with other non-alphanumeric characters) will then need to be removed/banned from artist's fileout tools: a limitation of using a file-system based asset manager.<br><br>
                                                    Optional tokens will typically be used for variants. Limit of 1 optional token per schema before any '.' delimeter (i.e. padding can be declared as optional)<br><br>
                                                                                            
                                                    If your pipeline uses multiple schemas (e.g. separate schemas for cameras, CG renders, client deliveravles, etc) consider storing the token strings inside your own environment variables.
                                                    Enter the environment variable in shell format:
                                                    <br><br><i>$CAMERA_SCHEMA</i> or <i>$RENDER_SCHEMA</i> or <i>$DELIVERABLES_SCHEMA</i> etc<br><br>
                                                
                                                    <b style="color:red">THE ABOVE SCHEMAS ARE EXAMPLES ONLY - IF YOU ARE USING THIS TOOL TO PROTOTYPE A PIPELINE, THINK LONG AND HARD AND BEFORE COMMITTING TO A SCHEMA.<br><br>
                                                    A SUCCESSFUL PIPELINE COULD LEAVE YOU ENCUMBERED WITH YOUR SCHEMA DECISIONS FOR A VERY LONG TIME &#128540;</b><br><br>
                                                    Disable this text field by setting any value into the environment variable to an empty string <i>ASSET_MANAGER_DISABLE_OVERRIDE=""</i>
                                                """)
        
            self.schemaOverrideLineEdit.textChanged.connect(self.schemaOverrideChanged)
            self.schemaOverrideLayout.addWidget(self.schemaOverrideLineEdit)

            # Add Schema Override widget to layout
            self.layout.addWidget(self.schemaOverrideWidget)

        # Tokens Directory Widget
        self.tokenDirVarsWidget = QtWidgets.QWidget(self)
        self.tokenDirVarsLayout = QtWidgets.QHBoxLayout(self.tokenDirVarsWidget)
        self.tokenDirVarsLayout.setContentsMargins(0, 0, 0, 3)
        self.tokenDirVarsWidget.setLayout(self.tokenDirVarsLayout)

        self.tokenDirVarsLabel = QtWidgets.QLabel('Directory tokens:')
        self.tokenDirVarsLayout.addWidget(self.tokenDirVarsLabel)
        self.tokenDirVarsLabel2 = QtWidgets.QLabel('widget')
        self.tokenDirVarsLayout.addWidget(self.tokenDirVarsLabel2)
        self.tokenDirVarsLayout.addStretch()

        self.layout.addWidget(self.tokenDirVarsWidget)

        # Tokens Path Widget
        self.tokenFileVarsWidget = QtWidgets.QWidget(self)
        self.tokenFileVarsLayout = QtWidgets.QHBoxLayout(self.tokenFileVarsWidget)
        self.tokenFileVarsLayout.setContentsMargins(0, 0, 0, 5)
        self.tokenFileVarsWidget.setLayout(self.tokenFileVarsLayout)

        self.tokenFileVarsLayout.addSpacing(33)
        self.tokenFileVarsLabel = QtWidgets.QLabel('File tokens:')
        self.tokenFileVarsLayout.addWidget(self.tokenFileVarsLabel)
        self.tokenFileVarsLabel2 = QtWidgets.QLabel('widget')
        self.tokenFileVarsLayout.addWidget(self.tokenFileVarsLabel2)
        self.tokenFileVarsLayout.addStretch()

        self.layout.addWidget(self.tokenFileVarsWidget)

        # Schema Divider
        self.shemaDivider = QtWidgets.QFrame(self)
        self.shemaDivider.setFrameShape(QtWidgets.QFrame.HLine)
        self.layout.addWidget(self.shemaDivider)

        # Button Bar Widget
        self.buttonBarWidget = QtWidgets.QWidget(self)
        self.buttonBarLayout = QtWidgets.QHBoxLayout(self.buttonBarWidget)
        self.buttonBarLayout.setContentsMargins(0, 2, 0, 2)
        self.buttonBarWidget.setLayout(self.buttonBarLayout)

        # Load nodes label
        self.loadNodesLabel = QtWidgets.QLabel('Populate spreadsheet with:')
        self.buttonBarLayout.addWidget(self.loadNodesLabel)

        
        # Load All Nodes
        self.buttonBarLayout.addSpacing(constants.BUTTON_SPACER)
        self.loadAllButton = QtWidgets.QPushButton('all asset nodes')
        self.loadAllButton.setMaximumWidth(constants.BUTTON_WIDTH)
        self.loadAllButton.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Maximum)
        self.loadAllButton.setToolTip('Populate the spreadsheet with asset nodes of the following classes from <b>all nodes</b> in the node graph:<br><br>' + '<br>'.join(constants.ASSET_CLASSES))
        self.loadAllButton.released.connect(self.loadAll)
        self.buttonBarLayout.addWidget(self.loadAllButton)

        # Load Selected Nodes
        self.loadSelectedButton = QtWidgets.QPushButton('asset nodes in selection')
        self.loadSelectedButton.setMaximumWidth(constants.BUTTON_WIDTH)
        self.loadSelectedButton.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Maximum)
        self.loadSelectedButton.setToolTip('Populate the spreadsheet with asset nodes of the following classes from <b>selected nodes</b> in the node graph:<br><br>' + '<br>'.join(constants.ASSET_CLASSES))
        self.loadSelectedButton.released.connect(self.loadSelected)
        self.buttonBarLayout.addWidget(self.loadSelectedButton)

        ''''
        # Colorize Tokens
        self.colorizeTokens = QtWidgets.QCheckBox('Colorize tokens')
        self.colorizeTokens.setChecked(True) 
        self.colorizeTokens.setDisabled(True) 
        self.buttonBarLayout.addSpacing(constants.BUTTON_SPACER)
        self.buttonBarLayout.addWidget(self.colorizeTokens)
        self.buttonBarLayout.addStretch()
        '''

        # Filter line edit
        self.buttonBarLayout.addSpacing(constants.BUTTON_SPACER)
        self.filterLineEdit = QtWidgets.QLineEdit(self.buttonBarWidget)
        self.filterLineEdit.setPlaceholderText('Filter')
        self.filterLineEdit.setAcceptDrops(True)
        self.filterCompleter = MultiCompleter(self.nodeList)
        self.nodeFilterModel = self.filterCompleter.model()
        self.filterLineEdit.setCompleter(self.filterCompleter)
        self.filterLineEdit.textChanged.connect(self.nodeFilterChanged)
        self.filterLineEdit.setToolTip('Filter the spreadsheet using the following syntax:<br><br>')
        self.buttonBarLayout.addWidget(self.filterLineEdit)

        # Add Button Bar Widget to layout
        self.layout.addWidget(self.buttonBarWidget)



        '''
        # Button Bar Divider
        self.buttonBarDivider = QtWidgets.QFrame(self)
        self.buttonBarDivider.setFrameShape(QtWidgets.QFrame.HLine)
        self.layout.addWidget(self.buttonBarDivider)

        # Filter Widget
        self.filterWidget = QtWidgets.QWidget(self)
        self.filterLayout = QtWidgets.QHBoxLayout(self.filterWidget)
        self.filterLayout.setContentsMargins(0, 2, 0, 2)
        self.filterWidget.setLayout(self.filterLayout)

        # Filter Dropdown Menu
        self.filterMenu = KeepOpenMenu('Filter:')

        self.allFiltersAction = CheckAction('all', self.filterMenu)
        self.filterMenu.addAction(self.allFiltersAction)
        #self.all_knobs_action.triggered[bool].connect(self.all_knob_states_changed)

        self.filterMenu.addSeparator()

        for filter in constants.FILTER_DEFAULTS:
            if filter[0] == '-':
                filter = filter[1:]
            action = CheckAction(filter, self.filterMenu)
            self.filterMenu.addAction(action)
            #self.hidden_knobs_action.triggered[bool].connect(self.hidden_knobs_changed)

        # Filter Dropdown Button
        self.filterDropdownButton = QtWidgets.QPushButton('Filter:')
        self.filterDropdownButton.setMaximumWidth(constants.FILTER_WIDTH)
        self.filterDropdownButton.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Maximum)
        self.filterDropdownButton.setToolTip('Tooltip TBC')
        self.filterDropdownButton.setMenu(self.filterMenu)
        self.filterLayout.addWidget(self.filterDropdownButton)

        # Separate filter menu and filter line edit
        self.filterLayout.addSpacing(constants.LABEL_SPACER)
        self.filterLabel = QtWidgets.QLabel('and')
        self.filterLayout.addWidget(self.filterLabel)
        self.filterLineEdit = QtWidgets.QLineEdit(self.buttonBarWidget)
        self.filterLayout.addSpacing(constants.LABEL_SPACER)

        # Filter line edit
        self.filterLineEdit.setPlaceholderText('Examples: assetname, partial filename, -Write, Class:Read, version:003, v003, etc')
        self.filterLineEdit.setToolTip('Filter te spreadsheet using the following syntax:<br><br>')
        self.filterLayout.addWidget(self.filterLineEdit)

        # Add Filter bar to layout
        self.layout.addWidget(self.filterWidget)
        '''

        # Spreadsheet

        self.tableModel = model.NodeTableModel()
        self.tableView = NodeTableView(self)
        self.layout.addWidget(self.tableView)

        # Filter by Node name
        self.nodeFilterModel = model.NodeFilterModel(self)
        self.nodeFilterModel.setSourceModel(self.tableModel)
        self.tableView.setModel(self.nodeFilterModel)

        self.schemaOverrideChanged()

    def loadSelected(self):
        """Sets the node list to current selection."""
        self.nodeList = nukeUtils.getSelectedNodes(self.grouped_nodes)

    def loadAll(self):
        """Sets the node list to current selection."""
        self.nodeList = nukeUtils.getAllNodes(self.grouped_nodes)


    @property
    def nodeList(self):
        """:obj:`list` of :obj:`nuke.Node`: List of loaded nodes before all
            filtering.

        Setting this attribute updates all models and warns when loading too
        many nodes.

        """
        self._nodeList = [node for node in self._nodeList
                           if nukeUtils.node_exists(node)]
        return self._nodeList

    @nodeList.setter
    def nodeList(self, nodes):
        numNodes = len(nodes)

        # Ask for confirmation before loading too many nodes.
        if numNodes > constants.NUM_NODES_WARN_BEFORE_LOAD:
            proceed = nukeUtils.ask('{numNodes} Nodes may take a '
                                     'long time. \n'
                                     'Dou you wish to proceed?'.format(
                                         numNodes=numNodes))

            if not proceed:
                return

        self._nodeList = nodes or []
        self.tableModel.nodeList = self.nodeList

        self.filterCompleter.setModel(
            QtCore.QStringListModel(self.nodeList))

        self.tableView.horizontalHeader().setSortIndicatorShown(False)
        self.tableView.resizeColumnsToContents()
        self.tableView.horizontalHeader().setSortIndicatorShown(True)

    '''
    @QtCore.Slot(bool)
    def grouped_nodes_changed(self, checked=None):
        """Update the hidden knobs state filter.

        Args:
            checked (bool): If True, knobs with hidden state are displayed.

        """
        # PySide doesn't pass checked state
        if checked is None:
            checked = self.grouped_nodes_action.isChecked()
        self.grouped_nodes = checked
        self.tableView.horizontalHeader().setSortIndicatorShown(False)
        self.tableView.resizeColumnsToContents()
        self.tableView.horizontalHeader().setSortIndicatorShown(True)
    '''

    @property
    def grouped_nodes(self):
        """bool: Show selected nodes inside of selected group nodes."""
        return self._grouped_nodes

    @grouped_nodes.setter
    def grouped_nodes(self, checked):
        self._grouped_nodes = checked
        self.load_selected()
        self.grouped_nodes_action.setChecked(checked)

    '''
    @QtCore.Slot(bool)
    def hidden_knobs_changed(self, checked=None):
        """Update the hidden knobs state filter.

        Args:
            checked (bool): If True, knobs with hidden state are displayed.

        """
        # PySide doesn't pass checked state
        if checked is None:
            checked = self.hidden_knobs_action.isChecked()
        self.hidden_knobs = checked
        self.tableView.horizontalHeader().setSortIndicatorShown(False)
        self.tableView.resizeColumnsToContents()
        self.tableView.horizontalHeader().setSortIndicatorShown(True)


    @property
    def hidden_knobs(self):
        """bool: Show hidden knobs of the node."""
        return self._hidden_knobs

    @hidden_knobs.setter
    def hidden_knobs(self, checked):
        self._hidden_knobs = checked
        self.knob_states_filter_model.hidden_knobs = checked
        self.tableView.horizontalHeader().setSortIndicatorShown(False)
        self.tableView.resizeColumnsToContents()
        self.tableView.horizontalHeader().setSortIndicatorShown(True)

        self.hidden_knobs_action.setChecked(checked)

    @QtCore.Slot(bool)
    def disabled_knobs_changed(self, checked=None):
        """Update the disabled knobs state filter.

        Args:
            checked (bool): If True, knobs with disabled state are displayed.

        """
        # PySide doesn't pass checked state
        if checked is None:
            checked = self.disabled_knobs_action.isChecked()
        self.disabled_knobs = checked
        self.tableView.horizontalHeader().setSortIndicatorShown(False)
        self.tableView.resizeColumnsToContents()
        self.tableView.horizontalHeader().setSortIndicatorShown(True)


    @property
    def disabled_knobs(self):
        """bool: Show disabled knobs."""
        return self._disabled_knobs

    @disabled_knobs.setter
    def disabled_knobs(self, checked=None):
        self._disabled_knobs = checked
        self.knob_states_filter_model.disabled_knobs = checked
        self.tableView.horizontalHeader().setSortIndicatorShown(False)
        self.tableView.resizeColumnsToContents()
        self.tableView.horizontalHeader().setSortIndicatorShown(True)

        self.disabled_knobs_action.setChecked(checked)
        self.update_all_knob_states_action()

    @QtCore.Slot(bool)
    def all_knob_states_changed(self, checked=True):
        """Update the knob states filter.

        Args:
            checked: If True, show knobs with hidden or disabled state.

        """
        # PySide doesn't pass checked state
        if checked is None:
            checked = self.all_knobs_action.isChecked()
        self.all_knob_states = checked
        self.tableView.horizontalHeader().setSortIndicatorShown(False)
        self.tableView.resizeColumnsToContents()
        self.tableView.horizontalHeader().setSortIndicatorShown(True)


    @property
    def all_knob_states(self):
        """bool: Knobs with hidden or disabled knob states are displayed."""
        self._all_knob_states = self.hidden_knobs and self._disabled_knobs
        return self._all_knob_states

    @all_knob_states.setter
    def all_knob_states(self, checked=None):
        self._all_knob_states = checked
        self.hidden_knobs = checked
        self.disabled_knobs = checked

    def update_all_knob_states_action(self):
        """Update action (checkbox) 'All' knob states."""
        self.all_knobs_action.setChecked(all([self.hidden_knobs,
                                              self.disabled_knobs]))

    @QtCore.Slot(str)
    def knob_name_filter_changed(self, value=None):
        """Update the knob name filter.

        Args:
            value (str): list of knob names to display.

        """
        if not value:
            value = self.knob_name_filter_line_edit.text()
        self.knob_name_filter = value
        self.tableView.horizontalHeader().setSortIndicatorShown(False)
        self.tableView.resizeColumnsToContents()
        self.tableView.horizontalHeader().setSortIndicatorShown(True)


    @property
    def knob_name_filter(self):
        """str: List of knob names separated by delimiters."""
        return self._knob_name_filter

    @knob_name_filter.setter
    def knob_name_filter(self, filter_str=None):
        if filter_str is None:
            filter_str = self.knob_name_filter_line_edit.text()
        else:
            self.knob_name_filter_line_edit.setText(filter_str)
        self._knob_name_filter = filter_str
        self.knob_name_filter_model.set_filter_str(filter_str)
    '''
    
    @property
    def nodeFilter(self):
        """str: List of node names separated by delimiters."""
        return self._nodeFilter

    @nodeFilter.setter
    def nodeFilter(self, filterItems=None):
        self._nodeFilter = filterItems
        self.nodeFilterModel.set_filter_str(filterItems)
        #self.empty_column_filter_model.invalidateFilter()

    @QtCore.Slot(str)
    def nodeFilterChanged(self, filterItems):
        """Update the node names filter.

        Args:
            node_names (str): List of node names separated by delimiter.

        """
        if not filterItems:
            filterItems = self.filterLineEdit.text()
        self.nodeFilter = filterItems
        self.tableView.horizontalHeader().setSortIndicatorShown(False)
        self.tableView.resizeColumnsToContents()
        self.tableView.horizontalHeader().setSortIndicatorShown(True)


    @QtCore.Slot(str)
    def node_class_filter_changed(self, node_classes=None):
        """Update the node class filter.

        Args:
            node_classes (str): delimited str list of node Classes to display.

        """
        if not node_classes:
            node_classes = self.node_class_filter_line_edit.text()
        self.node_class_filter = node_classes
        self.tableView.horizontalHeader().setSortIndicatorShown(False)
        self.tableView.resizeColumnsToContents()
        self.tableView.horizontalHeader().setSortIndicatorShown(True)


    @QtCore.Slot(str)
    def schemaOverrideChanged(self):
        """Update the node class filter.

        Args:
            node_classes (str): delimited str list of node Classes to display.

        """
        schemaStr = self.schemaOverrideLineEdit.text()
        if schemaStr == '':
            schemaStr = str(os.environ.get('ASSET_MANAGER_SCHEMA', constants.SCHEMA_DEFAULT))

        self.tableModel.schema.updateSchemaFromString(schemaStr)

        self.tokenDirVarsLabel2.setText(self.tableModel.schema.schemaPathHeadColor)
        self.tokenFileVarsLabel2.setText(self.tableModel.schema.schemaPathTailColor)
        self.tableView.horizontalHeader().setSortIndicatorShown(False)
        self.tableView.resizeColumnsToContents()
        self.tableView.horizontalHeader().setSortIndicatorShown(True)

