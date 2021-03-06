# -*- coding: utf-8 -*-
import sys
from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt
import os.path
import codecs
import osgqt
import osgDB
import osg
import shutil
import jarvis
import traceback
import config
import datetime
import math

class MyTextEdit(QtGui.QTextEdit):
    def __init__(self, text_color, father):
        super(MyTextEdit, self).__init__("", father)
        self.setReadOnly(True)
        font = QtGui.QFont()
        font.setFamily(config.FONT_FAMILY)
        font.setPointSize(config.FONT_SIZE)
        font.setStyleHint(QtGui.QFont.TypeWriter)
        self.setFont(font)
        if config.WRAP_TEXT is False:
            self.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        self.setTextColor(QtGui.QColor(*text_color))
        self.father = father

    def keyPressEvent(self, event):
        self.father.keyPressEvent(event)
        super(MyTextEdit, self).keyPressEvent(event)

class ToolBar(QtGui.QWidget):
    def __init__(self, father):
        QtGui.QWidget.__init__(self)

        self.father = father

        layout = QtGui.QVBoxLayout(self)

        top_bar = QtGui.QHBoxLayout()
        layout.addLayout(top_bar)

        bottom_bar = QtGui.QHBoxLayout()
        layout.addLayout(bottom_bar)

        self.toogle_aspect_ratio = config.ASPECT_RATIO != 1.0
        self.aspect_ratio_btn = QtGui.QPushButton('square' if config.ASPECT_RATIO != 1.0 else 'large', self)
        self.aspect_ratio_btn.clicked.connect(self.aspect_ratio_btn_clicked)
        bottom_bar.addWidget(self.aspect_ratio_btn)

        self.left_btn = QtGui.QPushButton(u'<', self)
        self.left_btn.clicked.connect(self.left_btn_clicked)
        bottom_bar.addWidget(self.left_btn)

        self.toogle_play = True
        self.play_btn = QtGui.QPushButton(u'❙ ❙', self)
        self.play_btn.clicked.connect(self.play_btn_clicked)
        bottom_bar.addWidget(self.play_btn)

        self.right_btn = QtGui.QPushButton(u'>', self)
        self.right_btn.clicked.connect(self.right_btn_clicked)
        bottom_bar.addWidget(self.right_btn)

        if config.HIDE_SLIDER is False:
            self.slider = QtGui.QSlider(self)
            self.slider_max = self.father.osgView.loopTime * config.FPS_UI
            self.slider.setMinimum(0)
            self.slider.setMaximum(self.slider_max)
            self.slider.setOrientation(QtCore.Qt.Horizontal)
            self.slider.sliderPressed.connect(self.slider_pressed)
            self.slider.sliderReleased.connect(self.slider_released)
            self.slider.sliderMoved.connect(self.slider_moved)
            top_bar.addWidget(self.slider)

        self.time_info = QtGui.QLabel(self)
        self.time_info.setText("00:00.00/00:00.00 30FPS")
        bottom_bar.addWidget(self.time_info)
        self.update_slider = True

    def time_to_str(self, seconds):
        m, s = divmod(seconds, 60)
        ms = (seconds * 100.0) % 100
        return "%02d:%02d.%02d" % (m, s, ms)

    def update_time_info(self, current_time, duration, fps):
        if (not config.HIDE_SLIDER) and self.update_slider:
            self.slider.setValue(current_time / duration * self.slider_max)
        txt =  self.time_to_str(current_time) + "/"
        txt += self.time_to_str(duration) + " "
        txt += "(" + ("%03d" % fps) + " fps)"
        self.time_info.setText(txt)

    def aspect_ratio_btn_clicked(self):
        if self.toogle_aspect_ratio:
            config.ASPECT_RATIO = 1.0
            self.father.update_aspect_ratio(config.ASPECT_RATIO)
            self.aspect_ratio_btn.setText("large")
        else:
            config.ASPECT_RATIO = 16.0/9.0
            self.father.update_aspect_ratio(config.ASPECT_RATIO)
            self.aspect_ratio_btn.setText("square")
        self.toogle_aspect_ratio = not self.toogle_aspect_ratio

    def play_btn_clicked(self):
        if self.toogle_play:
            self.father.osgView.pause()
            self.play_btn.setText(u"►")
        else:
            self.father.osgView.play()
            self.play_btn.setText(u"❙ ❙")
        self.toogle_play = not self.toogle_play

    def left_btn_clicked(self):
        delta = -(1.0 / config.FPS_UI)
        self.father.osgView.update_time(from_delta=delta)

    def right_btn_clicked(self):
        delta = 1.0 / config.FPS_UI
        self.father.osgView.update_time(from_delta=delta)

    def slider_pressed(self):
        self.father.osgView.still_frame = True
        self.update_slider = False
        ratio = float(self.slider.value()) / self.slider_max
        self.father.osgView.update_time(from_ratio=ratio)

    def slider_moved(self):
        self.update_slider = False
        ratio = float(self.slider.value()) / self.slider_max
        self.father.osgView.update_time(from_ratio=ratio)

    def slider_released(self):
        self.update_slider = False
        ratio = float(self.slider.value()) / self.slider_max
        self.father.osgView.update_time(from_ratio=ratio)

        self.father.osgView.still_frame = False
        self.update_slider = True

class JarvisMain(QtGui.QWidget):

    def __init__(self, layout=None):
        self.osg_enable = True
        super(JarvisMain, self).__init__()

        self.initUI(layout)

    def message(self, object):
        try:
            fun_name = object["fun"]
            args = object.get("args", [])
            kwargs = object.get("kwargs", {})
            getattr(self, fun_name)(*args, **kwargs)
        except:
            print traceback.format_exc()
            pass

    def start(self):
        self.debugEditor.clear()
        self.errorEditor.clear()

    def finish(self):
        pass

    def display(self):
        print self.editor.toPlainText()

    def initUI(self, layout=None):
        self.setWindowTitle('Jarvis')

        self.rightBox = QtGui.QVBoxLayout(self)
        self.rightBox.setContentsMargins(0,0,0,0)
        self.rightBox.setSpacing(0)

        self.errorEditor = MyTextEdit((230, 20, 20), self)
        self.debugEditor = MyTextEdit((20, 20, 20),  self)
        
        self.rightBox.addWidget(self.errorEditor)
        self.rightBox.addWidget(self.debugEditor)
        if self.osg_enable:
            self.osgView = osgqt.PyQtOSGWidget(self)
            self.toolbar = ToolBar(self)
            self.rightBox.addWidget(self.osgView, 0, Qt.AlignCenter)
            self.rightBox.addWidget(self.toolbar)

        self.update_aspect_ratio(config.ASPECT_RATIO)

        self.filename = None
        self.show()

    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Space : 
            self.toolbar.play_btn_clicked()
        elif key == QtCore.Qt.Key_Left:
            self.toolbar.left_btn_clicked()
        elif key == QtCore.Qt.Key_Right:
            self.toolbar.right_btn_clicked()

    def update_aspect_ratio(self, ratio):
        screen = QtGui.QDesktopWidget().screenGeometry()
        screen_width = screen.width() * config.DEVICE_PIXEL_RATIO
        screen_height = screen.height() * config.DEVICE_PIXEL_RATIO
        width = screen_width * config.WIDTH_RATIO
        self.setGeometry(
            screen_width - width,
            0, width, screen_height - config.PADDING_BOTTOM
        )
        if self.osg_enable:
            self.osgView.setMinimumWidth(width)
            self.osgView.setMinimumHeight(width / ratio)

    def atomic_write(self, filename, text):
        f = open(filename + ".tmp", "w")
        f.write(text)
        f.close()
        shutil.move(filename + ".tmp", filename)

    def debugprint(self, *args):
        text = " ".join(map(lambda x: str(x), args))
        self.debugEditor.append(text)
        text = self.debugEditor.toPlainText()

        debug_file = jarvis.get_filename(jarvis.DEBUG_FILE)
        self.atomic_write(debug_file, text + "\n")

    def errorprint(self, *args):
        text = " ".join(map(lambda x: str(x), args))
        self.errorEditor.append(text)
        text = self.errorEditor.toPlainText()

        error_file = jarvis.get_filename(jarvis.ERROR_FILE)
        self.atomic_write(error_file, text + "\n")

    def reset(self):
        self.debugEditor.setText("")
        self.errorEditor.setText("")
        self.osgView.resetSceneData(None)

    def osgprint(self, data):
        self.osgView.setSceneData(data)

    def audioemit(self, data, skip = 0.0):
        self.osgView.setAudioData(data, skip)

    def setlooptime(self, loopTime):
        self.osgView.setLoopTime(loopTime)

    def runcommand(self, fun):
        fun()

    def getosgviewer(self):
        return self.osgView.getosgviewer()

    def file_dialog(self):
        fd = QtGui.QFileDialog(self)
        filename = fd.getOpenFileName()
        if os.path.isfile(filename):
            text = open(filename).read()
            self.editor.setText(text)
            self.filename = filename

            s = codecs.open(self.filename,'w','utf-8')
            s.write(unicode(self.ui.editor_window.toPlainText()))
            s.close()
