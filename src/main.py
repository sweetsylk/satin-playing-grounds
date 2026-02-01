import sys
from PyQt6.QtWidgets import QApplication
from gui import Oscilloscope

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Oscilloscope()
    window.show()
    sys.exit(app.exec())