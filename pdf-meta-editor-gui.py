# -*- coding: utf-8 -*-
import os
import sys

# Fix for cx_Freeze placing DLLs in lib/ subfolder on Windows
if getattr(sys, "frozen", False) and sys.platform == "win32":
    try:
        _exe_dir = os.path.dirname(sys.executable)
        _lib_dir = os.path.join(_exe_dir, "lib")
        if os.path.isdir(_lib_dir):
            if hasattr(os, "add_dll_directory"):
                os.add_dll_directory(_lib_dir)
            else:
                import ctypes
                ctypes.windll.kernel32.SetDllDirectoryW(_lib_dir)
    except Exception:
        pass

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QProgressBar,
    QComboBox,
    QSpacerItem,
    QSizePolicy,
    QScrollArea,
    QCheckBox,
    QGroupBox,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QKeySequence

from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError
from pypdf.generic import NameObject, TextStringObject


def set_pdf_metadata(
    input_pdf_path: str,
    output_pdf_path: str,
    new_title: str | None = None,
    new_author: str | None = None,
    new_subject: str | None = None,
    new_creator: str | None = None,
    new_producer: str | None = None,
    new_keywords: str | None = None,
    set_initial_view_defaults: bool = True,
):
    try:
        reader = PdfReader(input_pdf_path, strict=False)
    except FileNotFoundError:
        raise
    except PdfReadError as e:
        print(f"Warning: Corrupt or unreadable PDF: {os.path.basename(input_pdf_path)} - {e}")
        raise
    except Exception as e:
        print(f"Warning: Error reading PDF: {os.path.basename(input_pdf_path)} - {e}")
        raise

    writer = PdfWriter()
    try:
        writer.clone_document_from_reader(reader)
    except Exception as e:
        print(f"Warning: Could not fully clone document: {os.path.basename(input_pdf_path)} - {e}")
        try:
            writer.append_pages_from_reader(reader)
        except Exception as e_append:
            print(f"Error: Failed to append pages for {os.path.basename(input_pdf_path)}: {e_append}")
            raise Exception(f"Cloning and appending failed for {input_pdf_path}") from e_append

    metadata_update = {}
    field_map = {
        "/Title": new_title,
        "/Author": new_author,
        "/Subject": new_subject,
        "/Creator": new_creator,
        "/Producer": new_producer,
        "/Keywords": new_keywords,
    }

    for key, value in field_map.items():
        if value is not None:
            metadata_update[key] = TextStringObject(value)

    merged_metadata = {}
    try:
        existing_metadata = reader.metadata
        if existing_metadata:
            merged_metadata.update(existing_metadata)
    except Exception:
        print(f"Warning: Could not read existing metadata for {os.path.basename(input_pdf_path)}")

    merged_metadata.update(metadata_update)

    if merged_metadata:
        try:
            writer.add_metadata(merged_metadata)
        except Exception as e:
            print(f"Warning: Could not write metadata for {os.path.basename(input_pdf_path)}: {e}")

    if set_initial_view_defaults:
        try:
            if writer.root_object and isinstance(writer.root_object, dict):
                writer.root_object[NameObject("/PageMode")] = NameObject("/UseNone")
                if NameObject("/PageLayout") in writer.root_object:
                    del writer.root_object[NameObject("/PageLayout")]
                if NameObject("/OpenAction") in writer.root_object:
                    del writer.root_object[NameObject("/OpenAction")]
            else:
                print(f"Warning: Could not set initial view defaults for {os.path.basename(input_pdf_path)} - Root object issue.")
        except Exception as e:
            print(f"Warning: Could not set initial view defaults for {os.path.basename(input_pdf_path)}: {e}")

    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
    try:
        with open(output_pdf_path, "wb") as output_file:
            writer.write(output_file)
    except Exception as e:
        print(f"Error: Could not write output file {os.path.basename(output_pdf_path)}: {e}")
        if os.path.exists(output_pdf_path):
            try:
                os.remove(output_pdf_path)
            except OSError:
                pass
        raise

    return True


class MetadataWorker(QThread):
    progress = Signal(int)
    log_message = Signal(str)
    finished = Signal(int, int)

    def __init__(
        self,
        pdf_folder,
        output_folder,
        metadata_settings,
        parent=None,
    ):
        super().__init__(parent)
        self.pdf_folder = pdf_folder
        self.output_folder = output_folder
        self.metadata_settings = metadata_settings
        self.is_running = True

    def run(self):
        edited_succeeded = 0
        edited_failed = 0
        current_step = 0

        self.log_message.emit("Starting process...")

        # Collect all PDF files recursively
        pdf_files = []
        for root, dirs, files in os.walk(self.pdf_folder):
            for f in sorted(files):
                if f.lower().endswith(".pdf"):
                    full_path = os.path.join(root, f)
                    if os.path.isfile(full_path):
                        rel_path = os.path.relpath(full_path, self.pdf_folder)
                        pdf_files.append(rel_path)
        pdf_files.sort()

        total_files = len(pdf_files)

        if total_files == 0:
            self.log_message.emit("No PDF files found for processing.")
            self.finished.emit(0, 0)
            return

        self.log_message.emit(f"Found {total_files} PDF file(s).")
        os.makedirs(self.output_folder, exist_ok=True)

        for rel_path in pdf_files:
            if not self.is_running:
                break
            current_step += 1

            input_path = os.path.join(self.pdf_folder, rel_path)
            output_path = os.path.join(self.output_folder, rel_path)
            base_name = os.path.basename(rel_path)
            filename_base = os.path.splitext(base_name)[0]

            self.log_message.emit(f"Processing: '{rel_path}'...")

            if not os.path.exists(input_path):
                self.log_message.emit(f"  -> Error: Input file '{rel_path}' not found (skipped).")
                edited_failed += 1
                if total_files > 0:
                    self.progress.emit(int((current_step / total_files) * 100))
                continue

            # --- Calculate Metadata ---
            values_to_set = {}
            for field_key, settings in self.metadata_settings.items():
                mode = settings["mode"]
                specific_value = settings["value"]
                current_value = None
                if mode == "Specific":
                    current_value = specific_value
                elif mode == "Clear":
                    current_value = ""
                elif mode == "Filename" and field_key == "title":
                    current_value = filename_base
                elif mode == "FilenameAfterSpace" and field_key == "title":
                    first_space_index = filename_base.find(" ")
                    if first_space_index != -1:
                        current_value = filename_base[first_space_index + 1 :].strip()
                    else:
                        current_value = filename_base
                    if not current_value:
                        current_value = filename_base
                values_to_set[field_key] = current_value

            # --- Apply Metadata and Write Output ---
            try:
                set_pdf_metadata(
                    input_path,
                    output_path,
                    new_title=values_to_set.get("title"),
                    new_author=values_to_set.get("author"),
                    new_subject=values_to_set.get("subject"),
                    new_creator=values_to_set.get("creator"),
                    new_producer=values_to_set.get("producer"),
                    new_keywords=values_to_set.get("keywords"),
                    set_initial_view_defaults=True,
                )
                self.log_message.emit(f"  -> Success: Metadata set. Saved to '{rel_path}' in output.")
                edited_succeeded += 1
            except FileNotFoundError:
                self.log_message.emit(f"  -> Error: Input file '{rel_path}' disappeared? (skipped)")
                edited_failed += 1
            except PdfReadError as e:
                self.log_message.emit(f"  -> Error: Cannot read PDF '{rel_path}' (skipped): {e}")
                edited_failed += 1
            except Exception as e:
                self.log_message.emit(f"  -> Error: Processing/writing failed for '{rel_path}': {e}")
                edited_failed += 1

            if total_files > 0:
                self.progress.emit(int((current_step / total_files) * 100))

        status_msg = (
            "Processing finished" if self.is_running else "Processing stopped by user"
        )
        self.log_message.emit("--------------------")
        self.log_message.emit(
            f"{status_msg}. Files Processed (Metadata): {edited_succeeded}✓ {edited_failed}✗."
        )
        if self.is_running and total_files > 0:
            self.progress.emit(100)
        self.finished.emit(edited_succeeded, edited_failed)

    def stop(self):
        self.log_message.emit("Stop signal received...")
        self.is_running = False


class PdfMetadataEditorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Metadata Editor")
        self.setGeometry(100, 100, 800, 700)
        self.worker = None

        # --- Main Layout ---
        main_layout = QVBoxLayout(self)

        # --- File/Folder Selection Group ---
        file_group = QGroupBox("Files and Folders")
        file_layout = QVBoxLayout()
        pdf_folder_layout = QHBoxLayout()
        self.pdf_folder_label = QLabel("PDF Folder (Input):")
        self.pdf_folder_input = QLineEdit()
        self.pdf_folder_button = QPushButton("Select...")
        self.pdf_folder_button.clicked.connect(self.select_pdf_folder)
        pdf_folder_layout.addWidget(self.pdf_folder_label)
        pdf_folder_layout.addWidget(self.pdf_folder_input)
        pdf_folder_layout.addWidget(self.pdf_folder_button)
        file_layout.addLayout(pdf_folder_layout)
        out_folder_layout = QHBoxLayout()
        self.out_folder_label = QLabel("Output Folder (Processed Files):")
        self.out_folder_input = QLineEdit()
        self.out_folder_input.setPlaceholderText("Default: Input Folder + '_processed'")
        self.out_folder_button = QPushButton("Select...")
        self.out_folder_button.clicked.connect(self.select_output_folder)
        self.edit_in_place_checkbox = QCheckBox("Output to Input Folder")
        self.edit_in_place_checkbox.setToolTip(
            "Check this to save processed files directly in the PDF Input Folder (potentially overwriting)."
        )
        self.edit_in_place_checkbox.stateChanged.connect(self.toggle_output_folder)
        out_folder_layout.addWidget(self.out_folder_label)
        out_folder_layout.addWidget(self.out_folder_input)
        out_folder_layout.addWidget(self.out_folder_button)
        file_layout.addLayout(out_folder_layout)
        file_layout.addWidget(
            self.edit_in_place_checkbox, alignment=Qt.AlignmentFlag.AlignRight
        )
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)

        # --- Metadata Editing Group ---
        metadata_group = QGroupBox("Metadata Editing Options")
        metadata_main_layout = QVBoxLayout()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(250)
        scroll_widget = QWidget()
        scroll_area.setWidget(scroll_widget)
        form_layout = QVBoxLayout(scroll_widget)
        self.field_widgets = {}
        self.field_widgets["title"] = self._create_metadata_field_widgets(
            form_layout,
            "Title",
            [
                "Leave Title Unchanged",
                "Use Specific Title",
                "Use Filename",
                "Use Filename (After First Space)",
                "Clear Title",
            ],
            default_index=4,
        )
        self.field_widgets["author"] = self._create_metadata_field_widgets(
            form_layout,
            "Author",
            ["Leave Unchanged", "Clear Author", "Set Specific Author"],
            default_index=1,
        )
        self.field_widgets["subject"] = self._create_metadata_field_widgets(
            form_layout,
            "Subject",
            ["Leave Unchanged", "Clear Subject", "Set Specific Subject"],
            default_index=1,
        )
        self.field_widgets["creator"] = self._create_metadata_field_widgets(
            form_layout,
            "Creator",
            ["Leave Unchanged", "Clear Creator", "Set Specific Creator"],
            default_index=1,
        )
        self.field_widgets["producer"] = self._create_metadata_field_widgets(
            form_layout,
            "Producer",
            ["Leave Unchanged", "Clear Producer", "Set Specific Producer"],
            default_index=1,
        )
        self.field_widgets["keywords"] = self._create_metadata_field_widgets(
            form_layout,
            "Keywords",
            ["Leave Unchanged", "Clear Keywords", "Set Specific Keywords"],
            default_index=1,
        )
        form_layout.addStretch()
        metadata_main_layout.addWidget(scroll_area)
        metadata_group.setLayout(metadata_main_layout)
        main_layout.addWidget(metadata_group)

        # --- Progress Bar and Log ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        main_layout.addWidget(self.progress_bar)
        self.log_area = QLineEdit("Status: Idle")
        self.log_area.setReadOnly(True)
        main_layout.addWidget(self.log_area)

        # --- Action Buttons ---
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Processing")
        self.start_button.clicked.connect(self.start_processing)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_processing)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        main_layout.addLayout(button_layout)

        # Set initial states
        self._update_all_input_states()
        self.toggle_output_folder()

    # --- Helper for Creating Metadata UI Elements ---
    def _create_metadata_field_widgets(self, parent_layout, field_name, combo_items, default_index=0):
        widgets = {}
        field_key = field_name.lower()

        mode_layout = QHBoxLayout()
        widgets["mode_label"] = QLabel(f"{field_name} Action:")
        widgets["mode_combo"] = QComboBox()
        widgets["mode_combo"].addItems(combo_items)
        widgets["mode_combo"].setCurrentIndex(default_index)
        mode_layout.addWidget(widgets["mode_label"])
        mode_layout.addWidget(widgets["mode_combo"])
        mode_layout.addStretch()
        parent_layout.addLayout(mode_layout)

        specific_layout = QHBoxLayout()
        widgets["specific_label"] = QLabel(f"Specific {field_name}:")
        widgets["specific_edit"] = QLineEdit()
        specific_layout.addWidget(widgets["specific_label"])
        specific_layout.addWidget(widgets["specific_edit"])
        parent_layout.addLayout(specific_layout)

        widgets["mode_combo"].currentIndexChanged.connect(
            lambda idx, key=field_key: self._update_specific_input_state(key)
        )

        parent_layout.addSpacerItem(
            QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        )
        return widgets

    # --- UI State Update Functions ---
    def _update_specific_input_state(self, field_key):
        widgets = self.field_widgets[field_key]
        combo_text = widgets["mode_combo"].currentText()
        is_specific_mode = "Specific" in combo_text
        widgets["specific_label"].setEnabled(is_specific_mode)
        widgets["specific_edit"].setEnabled(is_specific_mode)
        if not is_specific_mode:
            widgets["specific_edit"].clear()

    def _update_all_input_states(self):
        for field_key in self.field_widgets.keys():
            self._update_specific_input_state(field_key)

    def toggle_output_folder(self):
        is_checked = self.edit_in_place_checkbox.isChecked()
        self.out_folder_input.setEnabled(not is_checked)
        self.out_folder_button.setEnabled(not is_checked)
        if is_checked:
            self.out_folder_input.clear()
            self.out_folder_input.setPlaceholderText("Outputting to Input Folder")
        else:
            pdf_folder = self.pdf_folder_input.text()
            if pdf_folder and not self.out_folder_input.text():
                self.out_folder_input.setText(pdf_folder + "_processed")
            elif not pdf_folder:
                if not self.out_folder_input.text():
                    self.out_folder_input.setPlaceholderText("Select Input Folder first")

    # --- File/Folder Selection Dialogs ---
    def select_pdf_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select PDF Input Folder")
        if folder_path:
            self.pdf_folder_input.setText(folder_path)
            self.toggle_output_folder()

    def select_output_folder(self):
        if not self.edit_in_place_checkbox.isChecked():
            folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
            if folder:
                self.out_folder_input.setText(folder)

    # --- Worker Interaction ---
    def update_log(self, message):
        self.log_area.setText(message)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    # --- Slot for Worker Finished Signal ---
    def processing_finished(self, edited_succeeded, edited_failed):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        QMessageBox.information(
            self,
            "Processing Complete",
            f"Finished.\n\n"
            f"Files Processed (Metadata): {edited_succeeded} succeeded, {edited_failed} failed.",
        )
        final_status = (
            f"Status: Completed (Processed: {edited_succeeded}✓ {edited_failed}✗)"
        )
        self.log_area.setText(final_status)
        self.worker = None

    # --- Start Processing ---
    def start_processing(self):
        pdf_folder = self.pdf_folder_input.text()

        if self.edit_in_place_checkbox.isChecked():
            output_folder = pdf_folder
        else:
            output_folder = self.out_folder_input.text()

        # --- Input Validation ---
        if not pdf_folder or not os.path.isdir(pdf_folder):
            QMessageBox.warning(self, "Input Error", "Select a valid PDF Input folder.")
            return
        if not self.edit_in_place_checkbox.isChecked() and not output_folder:
            QMessageBox.warning(
                self, "Input Error", "Select an Output folder or check 'Output to Input Folder'."
            )
            return
        if (
            not self.edit_in_place_checkbox.isChecked()
            and os.path.abspath(pdf_folder) == os.path.abspath(output_folder)
        ):
            QMessageBox.warning(
                self,
                "Input Error",
                "Output folder cannot be the same as Input folder unless 'Output to Input Folder' is checked.",
            )
            return

        # --- Metadata settings ---
        metadata_settings = {}
        for field_key, widgets in self.field_widgets.items():
            mode_text = widgets["mode_combo"].currentText()
            specific_value = widgets["specific_edit"].text()
            mode_internal = "Leave"
            if "Specific" in mode_text:
                mode_internal = "Specific"
            elif "Clear" in mode_text:
                mode_internal = "Clear"
            elif "Filename (After First Space)" in mode_text:
                mode_internal = "FilenameAfterSpace"
            elif "Filename" in mode_text:
                mode_internal = "Filename"
            metadata_settings[field_key] = {
                "mode": mode_internal,
                "value": specific_value if mode_internal == "Specific" else None,
            }

        # --- Confirmation for Outputting to Input Folder ---
        if self.edit_in_place_checkbox.isChecked():
            reply = QMessageBox.question(
                self,
                "Confirmation",
                "You have chosen 'Output to Input Folder'.\n"
                "Processed files will be saved in the same folder as the input PDFs, potentially overwriting existing files if names match.\n\n"
                "Do you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return

        # --- Start Worker ---
        self.worker = MetadataWorker(
            pdf_folder=pdf_folder,
            output_folder=output_folder,
            metadata_settings=metadata_settings,
        )
        self.worker.progress.connect(self.update_progress)
        self.worker.log_message.connect(self.update_log)
        self.worker.finished.connect(self.processing_finished)

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.log_area.setText("Status: Starting...")
        self.worker.start()

    # --- Stop Processing and Close Event ---
    def stop_processing(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.log_area.setText("Status: Stopping...")

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Confirm Exit",
                "Processing is ongoing. Stop and exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.stop_processing()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


# --- Run Application ---
if __name__ == "__main__":
    try:
        import pypdf
        from PySide6.QtWidgets import QApplication
    except ImportError as e:
        print(f"Error: Missing required library. Please install dependencies.")
        print(f"Missing: {e.name}")
        print("Try running: pip install pypdf PySide6")
        sys.exit(1)

    app = QApplication(sys.argv)
    window = PdfMetadataEditorApp()
    window.show()
    sys.exit(app.exec())
