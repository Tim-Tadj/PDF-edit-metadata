# -*- coding: utf-8 -*-
from cx_Freeze import Executable, setup
import os
import sys

APP_NAME = "PDF Batch Metadata Editor"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = "Batch edit Title, Author, and Initial View for PDF files."
AUTHOR = ""
MAIN_SCRIPT = "pdf-meta-editor-gui.py"
TARGET_EXE = "PDFBatchMetadataEditor.exe"
BUILD_DIR = "build/PDFBatchMetadataEditor"
UPGRADE_CODE = "{f81d4fae-7dec-11d0-a765-00a0c91e6bf6}"
TARGET_DIR = r"[ProgramFilesFolder]\\PDF Batch Metadata Editor"
MSI_TARGET_NAME = "PDFBatchMetadataEditor"

PACKAGES = [
    "os",
    "sys",
    "re",
    "openpyxl",
    "pypdf",
    "PySide6",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
]

INCLUDES = [
    "openpyxl",
    "pypdf",
    "pypdf.errors",
    "pypdf.generic",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
]

INCLUDE_FILES = []

BIN_EXCLUDES = [
    "Qt6WebEngineCore.dll",
    "Qt6WebEngine.dll",
    "Qt6WebEngineWidgets.dll",
    "QtPdf.dll",
    "QtPdfQuick.dll",
]

PYSIDE_EXCLUDES = [
    "PySide6.Qt3DAnimation",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DExtras",
    "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic",
    "PySide6.Qt3DRender",
    "PySide6.QtCharts",
    "PySide6.QtConcurrent",
    "PySide6.QtDataVisualization",
    "PySide6.QtGraphs",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtNetworkAuth",
    "PySide6.QtOpenGL",
    "PySide6.QtOpenGLWidgets",
    "PySide6.QtPositioning",
    "PySide6.QtQml",
    "PySide6.QtQmlModels",
    "PySide6.QtQuick",
    "PySide6.QtQuick3D",
    "PySide6.QtQuickControls2",
    "PySide6.QtQuickWidgets",
    "PySide6.QtRemoteObjects",
    "PySide6.QtSensors",
    "PySide6.QtSerialPort",
    "PySide6.QtStateMachine",
    "PySide6.QtTextToSpeech",
    "PySide6.QtVirtualKeyboard",
    "PySide6.QtWebChannel",
    "PySide6.QtWebEngine",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineQuick",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebSockets",
    "PySide6.QtWebView",
    "PySide6.QtXml",
    "PySide6.QtXmlPatterns",
]

THIRD_PARTY_EXCLUDES = [
    "setuptools",
    "wheel",
    "importlib_metadata",
    "backports",
    "zipp",
]

build_exe_options = {
    "packages": PACKAGES,
    "includes": INCLUDES,
    "include_files": INCLUDE_FILES,
    "include_msvcr": True,
    "excludes": [
        "tkinter",
        *PYSIDE_EXCLUDES,
        *THIRD_PARTY_EXCLUDES,
    ],
    "build_exe": BUILD_DIR,
    "bin_excludes": BIN_EXCLUDES,
}

shortcut_table = [
    (
        "DesktopShortcut",
        "DesktopFolder",
        APP_NAME,
        "TARGETDIR",
        f"[TARGETDIR]{TARGET_EXE}",
        None,
        APP_DESCRIPTION,
        None,
        f"[TARGETDIR]{TARGET_EXE}",
        0,
        None,
        "TARGETDIR",
    ),
    (
        "ProgramMenuShortcut",
        "ProgramMenuFolder",
        APP_NAME,
        "TARGETDIR",
        f"[TARGETDIR]{TARGET_EXE}",
        None,
        APP_DESCRIPTION,
        None,
        f"[TARGETDIR]{TARGET_EXE}",
        0,
        None,
        "TARGETDIR",
    ),
]

bdist_msi_options = {
    "upgrade_code": UPGRADE_CODE,
    "add_to_path": False,
    "all_users": False,
    "initial_target_dir": TARGET_DIR,
    "target_name": MSI_TARGET_NAME,
    "data": {"Shortcut": shortcut_table},
}

base = "Win32GUI" if sys.platform == "win32" else None

executables = [
    Executable(
        MAIN_SCRIPT,
        base=base,
        target_name=TARGET_EXE,
    )
]

setup(
    name=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    author=AUTHOR,
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options,
    },
    executables=executables,
)
