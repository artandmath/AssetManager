# Import third party modules
from PySide6 import QtWidgets
import sys

# Import internal modules
import view

# You need one (and only one) QApplication instance per application.
# Pass in sys.argv to allow command line arguments for your app.
# If you know you won't use command line arguments QApplication([]) works too.
app = QtWidgets.QApplication(sys.argv)

# Create a Qt widget, which will be our window.
window = QtWidgets.QWidget()

layout = QtWidgets.QVBoxLayout()
window.setLayout(layout)
layout.setContentsMargins(20, 20, 20, 20)
window.setMinimumWidth(840)
window.setMinimumHeight(600)

view = view.SchemaBuilderWidget(window)
layout.addWidget(view)


window.show()  # IMPORTANT!!!!! Windows are hidden by default.

# Start the event loop.
app.exec()