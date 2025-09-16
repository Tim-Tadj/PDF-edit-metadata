# -*- coding: utf-8 -*-
"""
Setup script for cx_Freeze to build the PDF Batch Metadata Editor.

Usage:
  Build executable: python setup.py build
  Build MSI installer: python setup.py bdist_msi
"""

import sys
import os
from cx_Freeze import setup, Executable
import uuid # To generate a unique ID

# --- Configuration ---
# !! Replace these placeholders with your actual details !!
APP_NAME = "PDF Batch Metadata Editor"
APP_VERSION = "0.1.0" # Increment as needed
APP_DESCRIPTION = "Batch edit Title, Author, and Initial View for PDF files."
MAIN_SCRIPT = "pdf-meta-editor-gui.py" # <<< Your main Python script file name
COMPANY_NAME = "Witthoft Engineering" # <<< Your Company or Name
ICON_FILE = "we_icon_86I_icon.ico" # <<< Path to your .ico file (optional)
# --- End Configuration ---

# Generate a unique Upgrade Code for the MSI installer
# IMPORTANT: Keep this UUID the same across different versions
# of this specific application for upgrades to work correctly.
# Generate a new one only if this is a completely different product.
# You can generate one using: import uuid; print(uuid.uuid4())
# Example GUID: f81d4fae-7dec-11d0-a765-00a0c91e6bf6
UPGRADE_CODE = "{f81d4fae-7dec-11d0-a765-00a0c91e6bf6}" 
# --- Automatically determine base ---
base = None
if sys.platform == "win32":
    base = "Win32GUI"

# --- Define the executable ---
target_exe_name = f"{APP_NAME.replace(' ', '')}.exe" # e.g., PDFBatchMetadataEditor.exe
executables = [
    Executable(
        script=MAIN_SCRIPT,
        base=base,
        target_name=target_exe_name,
        icon=ICON_FILE if os.path.exists(ICON_FILE) else None,
    )
]

# --- Build options ---
packages = ["os", "sys", "pypdf", "PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets"]
includes = []
excludes = ["tkinter", "unittest"]
include_files = []
if os.path.exists(ICON_FILE):
    include_files.append(ICON_FILE) # Still include the icon file itself if needed elsewhere

build_exe_options = {
    "packages": packages,
    "includes": includes,
    "excludes": excludes,
    "include_files": include_files,
    "optimize": 2,
    "zip_include_packages": ["*"],
    "zip_exclude_packages": [],
}

# --- MSI Installer options ---
# Define shortcut table structure
# *** The key change is in the 'Icon' parameter for each shortcut ***
shortcut_table = [
    (
        "DesktopShortcut",        # Shortcut Identifier
        "DesktopFolder",          # Directory_
        APP_NAME,                 # Name
        "TARGETDIR",              # Component_ -> Needs to match component containing the exe
        f"[TARGETDIR]{target_exe_name}",# Target -> Reference the installed exe
        None,                     # Arguments
        APP_DESCRIPTION,          # Description
        None,                     # Hotkey
        # --- MODIFIED HERE ---
        f"[TARGETDIR]{target_exe_name}", # Icon -> Point to the EXE containing the embedded icon
        0,                        # IconIndex -> Use the first icon in the EXE
        None,                     # ShowCmd
        "TARGETDIR",              # WkDir
    ),
     (
        "ProgramMenuShortcut",      # Shortcut Identifier
        "ProgramMenuFolder",        # Directory_
        APP_NAME,                   # Name
        "TARGETDIR",                # Component_ -> Needs to match component containing the exe
        f"[TARGETDIR]{target_exe_name}",# Target -> Reference the installed exe
        None,                       # Arguments
        APP_DESCRIPTION,            # Description
        None,                       # Hotkey
        # --- MODIFIED HERE ---
        f"[TARGETDIR]{target_exe_name}", # Icon -> Point to the EXE containing the embedded icon
        0,                          # IconIndex -> Use the first icon in the EXE
        None,                       # ShowCmd
        "TARGETDIR",                # WkDir
    )
]

# MSI data including shortcuts
msi_data = {"Shortcut": shortcut_table}

bdist_msi_options = {
    "add_to_path": False,
    "initial_target_dir": r"[ProgramFilesFolder]\{}\{}".format(COMPANY_NAME, APP_NAME),
    "upgrade_code": UPGRADE_CODE,
    "data": msi_data,
    # Ensure the component containing the executable is correctly referenced if not default
    # "all_users": True, # Optional: Install for all users
}

# --- Setup configuration ---
setup(
    name=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    author=COMPANY_NAME,
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options,
    },
    executables=executables,
)

print("\n--- Build Process Finished ---")
print(f"Executable likely in: build/exe.{sys.platform}-...")
print(f"MSI installer likely in: dist/{APP_NAME}-{APP_VERSION}-...")

