import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLabel
from PyQt5.QtCore import QTimer, Qt
import logging

# Explicit környezeti változó beállítása a Qt plugin útvonalhoz
os.environ[
    'QT_QPA_PLATFORM_PLUGIN_PATH'] = '/Users/kasnyiklaszlo/PycharmProjects/Cikkcímgyűjtő/.venv/lib/python3.12/site-packages/PyQt5/Qt5/plugins'


class LogHandler(logging.Handler):
    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit

    def emit(self, record):
        msg = self.format(record)
        self.text_edit.append(msg)


class CikkcimgyujtoGUI(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.initUI()

        self.refresh_interval = int(self.config['DEFAULT']['refresh_interval'])

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)

        self.countdown = self.refresh_interval

    def initUI(self):
        layout = QVBoxLayout()

        self.log_display = QTextEdit(self)
        self.log_display.setReadOnly(True)
        layout.addWidget(self.log_display)

        self.countdown_label = QLabel(self)
        self.countdown_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.countdown_label)

        self.setLayout(layout)
        self.setGeometry(300, 300, 600, 400)
        self.setWindowTitle('Cikkcímgyűjtő Log és Visszaszámláló')
        self.show()

        log_handler = LogHandler(self.log_display)
        logging.getLogger().addHandler(log_handler)

    def update_countdown(self):
        self.countdown -= 1
        if self.countdown < 0:
            self.countdown = self.refresh_interval

        minutes, seconds = divmod(self.countdown, 60)
        hours, minutes = divmod(minutes, 60)

        countdown_text = f"Következő futás: {hours:02d}:{minutes:02d}:{seconds:02d}"
        self.countdown_label.setText(countdown_text)


def run_gui(config):
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    ex = CikkcimgyujtoGUI(config)
    sys.exit(app.exec_())


if __name__ == "__main__":
    import configparser

    config = configparser.ConfigParser()
    config.read('config.ini')
    run_gui(config)
