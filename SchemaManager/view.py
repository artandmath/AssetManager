# Import third party modules
from PySide6 import QtWidgets, QtCore, QtGui
import sys

# Import internal modules
from schema import SchemaManager

class SchemaBuilderWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(SchemaBuilderWidget, self).__init__(parent)

        # Variables:
        self.schema_manager = SchemaManager()

        # Content
        self.main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.main_layout)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Schema edit - enter the schema
        self.schema_edit_widget = QtWidgets.QWidget(self)
        self.schema_edit_widget.setMinimumWidth(800)
        self.schema_edit_layout = QtWidgets.QHBoxLayout()
        self.schema_edit_widget.setLayout(self.schema_edit_layout)
        self.schema_edit_layout.setContentsMargins(0, 0, 0, 0)

        self.schema_label = QtWidgets.QLabel('Schema:')
        self.schema_edit_layout.addWidget(self.schema_label)
        self.schema_line_edit = QtWidgets.QLineEdit()
        self.schema_line_edit.setPlaceholderText("Tokens path")
        self.schema_line_edit.textChanged.connect(self.schema_line_edit_changed)
        self.schema_edit_layout.addWidget(self.schema_line_edit)

        self.main_layout.addWidget(self.schema_edit_widget)

        # Feedback widget - view results of schema edit
        self.feedback_widget = QtWidgets.QWidget(self)
        self.feedback_widget.setMinimumWidth(800)
        self.feedback_layout = QtWidgets.QHBoxLayout()
        self.feedback_widget.setLayout(self.feedback_layout)
        self.feedback_layout.setContentsMargins(0, 0, 0, 0)

        self.feedback_label = QtWidgets.QLabel('Feedback')
        self.feedback_label.setWordWrap(True)
        font = QtGui.QFont("Courier New", 12)
        self.feedback_label.setFont(font)
        self.feedback_layout.addWidget(self.feedback_label)

        self.main_layout.addWidget(self.feedback_widget)
        self.main_layout.addStretch()

    @QtCore.Slot(str)
    def schema_line_edit_changed(self):
        self.schema_manager.path = self.schema_line_edit.text()

        groupings_string = ''
        for tokens in self.schema_manager.tokens_list:
            groupings_string += f"{tokens}\n"

        max_length = 0
        keys = set(self.schema_manager.keys)
        for key in keys:
            max_length = max(max_length, len(key))
        tokens_string = ''
        for token in self.schema_manager.token_list_flattened:
            if token.key in keys:
                keys.remove(token.key)
                tokens_string += f"key='{token.key}' \
{' '*(max_length-len(token.key))}\
constant={(str(not token.is_editable)+' ')[0:5]} \
editable={(str(token.is_editable)+' ')[0:5]} \
optional={(str(token.is_optional)+' ')[0:5]}\n"
        error_string = ''
        for error in self.schema_manager.errors:
            error_string += f"{error}\n"

        label_string = f"ANCHOR: {self.schema_manager.anchor}\n\n\
GROUPINGS:\n{groupings_string}\n\
TOKENS:\n{tokens_string}\n\
ERRORS:\n{error_string}"
        self.feedback_label.setText(label_string)
