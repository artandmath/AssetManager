# Import third-party modules
import logging
import nuke
import math
from Qt import QtCore, QtWidgets  # pylint: disable=no-name-in-module

# Import local modules

UNDO_TEXT = "Change value of ['file'] via Asset Manager"

class ItemDelegate(QtWidgets.QStyledItemDelegate):
    """
    TODO: Document
    """
    def __init__(self, view, parent=None):
        super(ItemDelegate, self).__init__(parent)

        self.undo = None
        self.data = None
        self.tableView = view

        menuItem = nuke.menu("Nuke").findItem("Edit/Undo")
        action = menuItem.action()
        action.triggered.connect(self.assetManagerUndo)
        
        menuItem = nuke.menu("Nuke").findItem("Edit/Redo")
        action = menuItem.action()
        action.triggered.connect(self.assetManagerRedo)

    def createEditor(self, parent, option, index):
        """
        TODO: Document
        """
        self.undo = nuke.Undo()
        self.undo.begin()
        logging.info('AssetManager undo.begin()')

        model = index.model()

        self.data = model.data(index, QtCore.Qt.EditRole)
        return super(ItemDelegate, self).createEditor(parent,
                                                            option,
                                                            index)

    def destroyEditor(self, editor, index):
        """
        TODO: Document
        """
        model = index.model()
        if model.data(index, QtCore.Qt.EditRole) == self.data:
            self.undo.cancel()
            logging.info('AssetManager undo.cancel()')
        else:
            self.undo.name(UNDO_TEXT)
            self.undo.end()
            logging.info('AssetManager undo.end()')
    
        self.data = None
        self.undo = None

        return super(ItemDelegate, self).destroyEditor(editor,
                                                        index)
    
    def assetManagerUndo(self):
        menuItem = nuke.menu("Nuke").findItem("Edit/Undo")
        action = menuItem.action()
        if UNDO_TEXT in action.text():
            logging.info('AssetManager assetManagerUndo()')
            #print(dir(self.tableView.model()))

            self.tableView.model().sourceModel().setupModelData()
            self.tableView.horizontalHeader().setSortIndicatorShown(False)
            self.tableView.resizeColumnsToContents()
            self.tableView.horizontalHeader().setSortIndicatorShown(True)


    def assetManagerRedo(self):
        menuItem = nuke.menu("Nuke").findItem("Edit/Redo")
        action = menuItem.action()
        if UNDO_TEXT in action.text():
            logging.info('AssetManager assetManagerRedo()')
            self.tableView.model().sourceModel().setupModelData()
            self.tableView.horizontalHeader().setSortIndicatorShown(False)
            self.tableView.resizeColumnsToContents()
            self.tableView.horizontalHeader().setSortIndicatorShown(True)
