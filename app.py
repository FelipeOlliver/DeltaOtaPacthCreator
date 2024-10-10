import sys
import argparse
import os
import subprocess
import re
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from datetime import *
import esptool
import detools

esp_delta_ota_magic = 0xfccdde10

MAGIC_SIZE = 4
DIGEST_SIZE = 32
RESERVED_HEADER = 64 - (MAGIC_SIZE + DIGEST_SIZE)

def check_requirements():

    commandEspTool = "esptool version"
    commandDeTools = "detools --version"
    try:
        cmd_answer = subprocess.check_output(commandEspTool, shell=True, universal_newlines=True)
        cmd_answer = cmd_answer.split(" ")[0]
        print(cmd_answer)
    except:
        os.system("pip install esptool")
        os.system("pip install pyserial")
        os.system("pip install setuptools")

    try:
        cmd_detools_answer = subprocess.check_output(commandDeTools, shell=True, universal_newlines=True)
        print(cmd_detools_answer)
        cmd_detools_answer = cmd_detools_answer.split(".")[0]
        print(cmd_detools_answer)
    except:

        os.system("winget install Microsoft.VisualStudio.2022.BuildTools")
        os.system("pip install detools")

def create_patch(chip: str, base_binary: str, new_binary: str, patch_file_name: str) -> None:
    cmd = "esptool --chip " + chip + " image_info " + base_binary
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    x = re.search(b"Validation Hash: ([A-Za-z0-9]+) \(valid\)", out)

    os.system("detools create_patch -c heatshrink " + base_binary + " " + new_binary + " " + patch_file_name)
    patch_file_without_header = "patch_file_temp.bin"
    os.system("move " + patch_file_name + " " + patch_file_without_header)

    with open(patch_file_name, "wb") as patch_file:
        patch_file.write(esp_delta_ota_magic.to_bytes(MAGIC_SIZE, 'little'))
        patch_file.write(bytes.fromhex(x[1].decode()))
        patch_file.write(bytearray(RESERVED_HEADER))
        with open(patch_file_without_header, "rb") as temp_patch:
            patch_file.write(temp_patch.read())

    os.remove(patch_file_without_header)


class App(QWidget):

    def __init__(self):
        super().__init__()

        self.baseFirmwarePath = ''
        self.NewFirmwarePath = ''
        self.patchFolderPath = ''
        self.baseFirmware = ''
        self.NewFirmware = ''
        self.patchFileName = ''
        self.espBoard = 'esp32c3'

        self.setFixedSize(QSize(630, 350))

        self.setWindowTitle("DOTA Patch Generate")
        self.setWindowIcon(QIcon("espc3.ico"))

        self.qLabelAppVersion = QLabel(self)
        self.qLabelAppVersion.setGeometry(570, 325, 150, 25)
        self.qLabelAppVersion.setText('v1.0.02')

        self.qLabelBaseFilePath = QLabel(self)
        self.qLabelBaseFilePath.setGeometry(30, 15, 350, 25)
        self.qLabelBaseFilePath.setText('Base firmware: ')

        self.qLabelNewFilePath = QLabel(self)
        self.qLabelNewFilePath.setGeometry(30, 55, 350, 25)
        self.qLabelNewFilePath.setText('New firmware: ')

        self.qLabelPatchFileDir = QLabel(self)
        self.qLabelPatchFileDir.setGeometry(30, 95, 350, 25)
        self.qLabelPatchFileDir.setText('Save patch to: ')

        self.qLabelEspBoardSelect = QLabel(self)
        self.qLabelEspBoardSelect.setGeometry(30, 135, 200, 25)
        self.qLabelEspBoardSelect.setText('ESP board: ')

        self.qLineEditBaseFilePath = QLineEdit(self)
        self.qLineEditBaseFilePath.setGeometry(135, 15, 350, 25)
        self.qLineEditBaseFilePath.setText('')
        self.qLineEditBaseFilePath.setReadOnly(True)

        self.qLineEditNewFilePath = QLineEdit(self)
        self.qLineEditNewFilePath.setGeometry(135, 55, 350, 25)
        self.qLineEditNewFilePath.setText('')
        self.qLineEditNewFilePath.setReadOnly(True)

        self.qLineEditPatchFileDir = QLineEdit(self)
        self.qLineEditPatchFileDir.setGeometry(135, 95, 350, 25)
        self.qLineEditPatchFileDir.setText('')
        self.qLineEditPatchFileDir.setReadOnly(True)

        self.qComboChooseESPBoard = QComboBox(self)
        self.qComboChooseESPBoard.setGeometry(105, 135, 100, 25)
        self.qComboChooseESPBoard.addItems(['esp32c3', 'esp32', 'esp32s3', 'esp32c6', 'esp32p4', 'esp32s2', 'esp32c6l', 'esp32c5', 'esp32c2', 'esp32h2'])

        self.qPushButtonBaseFilePath = QPushButton('&Browse...', self)
        self.qPushButtonBaseFilePath.setToolTip('Select the base firmware')
        self.qPushButtonBaseFilePath.setGeometry(500, 15, 100, 25)
        self.qPushButtonBaseFilePath.clicked.connect(self.baseFirmwareOpen)


        self.qPushButtonNewFilePath = QPushButton('&Browse...', self)
        self.qPushButtonNewFilePath.setToolTip('Select the new firmware')
        self.qPushButtonNewFilePath.setGeometry(500, 55, 100, 25)
        self.qPushButtonNewFilePath.clicked.connect(self.newFirmwareOpen)

        self.qPushButtonPatchFileDir = QPushButton('&Browse...', self)
        self.qPushButtonPatchFileDir.setToolTip('Select the folder for saving the generated patch:')
        self.qPushButtonPatchFileDir.setGeometry(500, 95, 100, 25)
        self.qPushButtonPatchFileDir.clicked.connect(self.patchPathOpen)

        self.qPushButtonGenerate = QPushButton('&Generate patch', self)
        self.qPushButtonGenerate.setToolTip('Generate patch file')
        self.qPushButtonGenerate.setGeometry(215, 135, 100, 25)
        self.qPushButtonGenerate.clicked.connect(self.generate)

        self.qPushButtonCancel = QPushButton('&Cancel', self)
        self.qPushButtonCancel.setToolTip('Cancel operation')
        self.qPushButtonCancel.setGeometry(320, 135, 100, 25)
        self.qPushButtonCancel.clicked.connect(self.cancel)
        self.qPushButtonCancel.setShortcut("Esc")


        self.qPlainTextEdit = QPlainTextEdit(self)
        self.qPlainTextEdit.setGeometry(30, 175, 570, 150)
        self.qPlainTextEdit.setReadOnly(True)
        self.cursor = QTextCursor(self.qPlainTextEdit.document())

        self.show()

    @pyqtSlot()
    def baseFirmwareOpen(self):
        self.baseFirmwarePath = QFileDialog.getOpenFileName(self, 'File loaded', filter='Bin files(*.bin)')[0]
        self.qLineEditBaseFilePath.setText(str(self.baseFirmwarePath))
        print(self.baseFirmwarePath)
        self.qPlainTextEdit.setPlainText(self.qPlainTextEdit.toPlainText() + datetime.now().strftime(
            "%H:%M:%S") + ' - ' + "Loaded base firmware file: " + str(self.baseFirmwarePath).split('/')[-1] + ".\n")
        self.qPlainTextEdit.setTextCursor(self.cursor)
        QApplication.processEvents()
        print(self.baseFirmwarePath.split('/')[-1])
        self.baseFirmware = (self.baseFirmwarePath.split('-')[-1]).split('.')[0]
        print(self.baseFirmware)


    @pyqtSlot()
    def newFirmwareOpen(self):
        self.NewFirmwarePath = QFileDialog.getOpenFileName(self, 'File loaded', filter='Bin files(*.bin)')[0]
        print(self.NewFirmwarePath)
        self.qLineEditNewFilePath.setText(str(self.NewFirmwarePath))
        self.qPlainTextEdit.setPlainText(self.qPlainTextEdit.toPlainText() + datetime.now().strftime(
            "%H:%M:%S") + ' - ' + "Loaded new firmware file: " + str(self.NewFirmwarePath).split('/')[-1] + ".\n")
        self.qPlainTextEdit.setTextCursor(self.cursor)
        QApplication.processEvents()
        print(self.NewFirmwarePath.split('/')[-1])
        self.newFirmware = (self.NewFirmwarePath.split('-')[-1]).split('.')[0]
        print(self.newFirmware)


    @pyqtSlot()
    def patchPathOpen(self):
        self.patchFolderPath = QFileDialog.getExistingDirectory(self, "Open Directory")
        self.qLineEditPatchFileDir.setText(str(self.patchFolderPath))
        self.qPlainTextEdit.setPlainText(self.qPlainTextEdit.toPlainText() + datetime.now().strftime(
            "%H:%M:%S") + ' - ' + "The generated patch file will be saved to: " + str(self.patchFolderPath) + ".\n")
        self.qPlainTextEdit.setTextCursor(self.cursor)
        QApplication.processEvents()
        #self.patchFolderPath = self.patchFolderPath +"/smartspeaker-"+ str(self.baseFirmware) + "to" + str(self.newFirmware) + ".bin"
        self.patchFileName = "smartspeaker-"+ str(self.baseFirmware) + "to" + str(self.newFirmware) + ".bin"
        print(self.patchFolderPath)
        print(self.patchFileName)
        self.qPlainTextEdit.setPlainText(self.qPlainTextEdit.toPlainText() + datetime.now().strftime(
            "%H:%M:%S") + ' - ' + "Patch file name: " + str(self.patchFileName) + ".\n")
        self.qPlainTextEdit.setTextCursor(self.cursor)
        QApplication.processEvents()


    @pyqtSlot()
    def generate(self):
        if self.baseFirmwarePath != '':
            if self.NewFirmwarePath != '':
                if self.patchFolderPath != '':
                    print("Generate patch")
                    try:
                        check_requirements()
                        self.espBoard = self.qComboChooseESPBoard.currentText()
                        create_patch(self.espBoard, self.baseFirmwarePath, self.NewFirmwarePath, self.patchFileName)
                        os.system("move " + self.patchFileName + " " + self.patchFolderPath)
                        self.qPlainTextEdit.setPlainText(self.qPlainTextEdit.toPlainText() + datetime.now().strftime(
                            "%H:%M:%S") + ' - ' + "Patch file created.\n")
                        self.qPlainTextEdit.setTextCursor(self.cursor)
                        QApplication.processEvents()
                    except:
                        self.qPlainTextEdit.setPlainText(self.qPlainTextEdit.toPlainText() + datetime.now().strftime(
                            "%H:%M:%S") + ' - ' + "Failed to complete patch creation.\n")
                        self.qPlainTextEdit.setTextCursor(self.cursor)
                        QApplication.processEvents()

                else:
                    self.qPlainTextEdit.setPlainText(self.qPlainTextEdit.toPlainText() + datetime.now().strftime(
                        "%H:%M:%S") + ' - ' + "Select a folder to save the generated patch file.\n")
                    self.qPlainTextEdit.setTextCursor(self.cursor)
                    QApplication.processEvents()

            else:
                self.qPlainTextEdit.setPlainText(self.qPlainTextEdit.toPlainText() + datetime.now().strftime(
                    "%H:%M:%S") + ' - ' + "Select a new firmware file first.\n")
                self.qPlainTextEdit.setTextCursor(self.cursor)
                QApplication.processEvents()

        else:
            self.qPlainTextEdit.setPlainText(self.qPlainTextEdit.toPlainText() + datetime.now().strftime(
                "%H:%M:%S") + ' - ' + "Select a base firmware file first.\n")
            self.qPlainTextEdit.setTextCursor(self.cursor)
            QApplication.processEvents()


    @pyqtSlot()
    def cancel(self):
        print("Cancel")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = App()
    sys.exit(app.exec_())