import sys

import numpy as np

import PySide6
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import qWarning, QObject, QEvent, QIODevice, QTimer
from PySide6.QtWidgets import QApplication, QWidget, QMainWindow
from PySide6.QtMultimedia import QAudioFormat, QMediaDevices, QAudioSink

from narator import MultiprocessingAudioNarator


print("PySide version:", PySide6.__version__)

__version__ = "0.1.0"


class KeyListener(QObject):
    def eventFilter(self, widget: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.KeyPress:
            assert isinstance(event, QtGui.QKeyEvent)
            assert isinstance(widget, MainWindow)

            if event.key() in (QtCore.Qt.Key.Key_Enter, QtCore.Qt.Key.Key_Return):
                print("Enter")
                widget.examine()
            else:
                text = event.text()
                widget.add_symbol(text)
        
        return False
    

class InputWidget(QWidget):
    def __init__(self, parent) -> None:
        super().__init__(parent)

        self.layout = QtWidgets.QVBoxLayout(self)

        self.label1 = QtWidgets.QLabel("", self)
        self.layout.addWidget(self.label1)


class MainWindow(QMainWindow):
    def __init__(self, audio_devices) -> None:
        super().__init__()

        self.audio_devices = audio_devices
        self.audio_device = audio_devices[0]

        self.resize(500, 500)

        self.widget = InputWidget(self)
        self.setCentralWidget(self.widget)

        self.event_filter = KeyListener(parent=self)
        self.installEventFilter(self.event_filter)

        self.examples = self.read_examples()
        self.exercises = []
        self.text = ""
        self.input_text = ""
        # self.dictator = AudioNarator()
        self.dictator = MultiprocessingAudioNarator()

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(200)

        self.initialize_audio()

    def update(self):
        if self.dictator.is_available():
            result = self.dictator.get()
            self.exercises.append(result)
            print(f"Exercises added. Exercises queue lenght: {len(self.exercises)}")
            self.statusBar().showMessage(f"Audio successfully generated. {len(self.exercises)} exercies in queue.")
        
        if len(self.exercises) < 5 and not self.dictator.is_busy():
            self.request_vocalization()

    def next_exercise(self):
        if len(self.exercises) == 0:
            qWarning("There is no exercises left.")
            self.text = ""
            self.audio_generator.clear()
            return
        
        exercise = self.exercises.pop(0)
        self.text = exercise["text"]
        print(self.text)
        audio_array = exercise["data"]
        self.audio_generator.set_data(audio_array)
        self.statusBar().showMessage("Next exercise.")

    def read_examples(self) -> list[str]:
        import csv

        with open('data/examples.csv', 'r') as f:
            reader = csv.reader(f, delimiter='|')
            return [v[0] for v in reader]

    def initialize_audio(self):
        audio_format = QAudioFormat()
        audio_format.setChannelCount(1)
        audio_format.setSampleRate(24000)
        audio_format.setSampleFormat(QAudioFormat.Float)

        audio_device = self.audio_devices[0]
        if not audio_device.isFormatSupported(audio_format):
            qWarning("Default format not supported - trying to use nearest")
            audio_format = audio_device.nearestFormat(audio_format)

        self.audio_format = audio_format

        self.audio_generator = AudioGenerator(self)
        self.audio_generator.start()

        self.create_audio_output()

        self.request_vocalization()

    def create_audio_output(self):
        self.audio_sink = QAudioSink(self.audio_device, self.audio_format)

        self.audio_sink.start(self.audio_generator)

    def examine(self):
        if self.input_text == self.text:
            print("Examine: correct.")
        else:
            print("Examine: incorrect.")
            print("User input:", self.input_text, ", correct:", self.text)

        self.restart()

    def request_vocalization(self):
        index = np.random.randint(0, len(self.examples))
        text = self.examples[index]

        self.statusBar().showMessage("Request audio generation...")
        self.dictator.request(text)

    def restart(self):
        self.input_text = ""
        self.widget.label1.setText("")
        self.next_exercise()

    def add_symbol(self, text: str):
        self.input_text += text
        self.widget.label1.setText(self.widget.label1.text() + text)


class AudioGenerator(QIODevice):
    data: np.ndarray

    def __init__(self, parent):
        super().__init__(parent)

        self.data = np.zeros((1000,), dtype=np.float32)
        self.pos = 0

    def set_data(self, array: np.ndarray):
        self.data = array
        self.pos = 0

    def start(self):
        self.open(QIODevice.ReadOnly)

    def stop(self):
        self.pos = 0
        self.close()

    def clear(self):
        self.data = np.zeros((1000,), dtype=np.float32)
        self.pos = 0

    def readData(self, maxlen) -> bytes:
        data = self.data.tobytes()
        result = b''

        while maxlen > len(result):
            chunk = min(len(data) - self.pos, maxlen - len(result))
            result += data[self.pos: self.pos + chunk]
            self.pos = (self.pos + chunk) % len(data)

        return result
    
    def write(self, data) -> int:
        return 0
    
    def bytesAvailable(self) -> int:
        return len(len(self.data.tobytes()))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName(f"Idiom v{__version__}")

    devices = QMediaDevices.audioOutputs()
    if not devices:
        print('No audio outputs found.', file=sys.stderr)
        sys.exit(-1)

    window = MainWindow(devices)
    window.show()

    sys.exit(app.exec())
