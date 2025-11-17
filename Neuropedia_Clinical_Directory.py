import sys
import os
import gspread
import json
from google.oauth2.service_account import Credentials
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QGroupBox, QComboBox, QCheckBox, QScrollArea,
    QHeaderView, QStatusBar, QSplitter, QDialog, QInputDialog, QSpacerItem, QSizePolicy,
    QTextBrowser, QSpinBox, QFrame
)
from PyQt6.QtGui import QFont, QIcon, QPixmap, QFontDatabase, QPainter, QColor
from PyQt6.QtCore import Qt, QUrl, QTimer, QSize
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from fpdf import FPDF
import webbrowser

# ==============================================================================
# --- Google Sheets API Setup ---
# ==============================================================================
# This setup uses your service account key for authentication.
# Ensure 'ncnc-staff-directory-2cf1ef3956ba.json' is in the same directory as this script.
try:
    # --- CHANGE THIS LINE TO MATCH YOUR JSON FILE NAME ---
    # You can also provide the full path if the file is not in the same directory
    json_key_file_name = "ncnc-staff-directory-2cf1ef3956ba.json"
    
    # Get the directory of the current script
    current_script_path = os.path.dirname(os.path.abspath(__file__))
    key_file_path = os.path.join(current_script_path, json_key_file_name)

    # Check if the JSON key file exists
    if not os.path.exists(key_file_path):
        raise FileNotFoundError(f"JSON key file not found at: {key_file_path}")

    # Define the required scopes for the API
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    # Load credentials from the service account key file
    CREDS = Credentials.from_service_account_file(key_file_path, scopes=SCOPES)
    # Authorize gspread client
    CLIENT = gspread.authorize(CREDS)

    # Open the spreadsheet by its URL.
    # --- MAKE SURE THIS URL IS CORRECT ---
    SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1UO1RRjt4d1JX7oU43k0PF8AhhTT5pQDhf0VXe4CW1Ws/edit?usp=sharing"
    SHEET = CLIENT.open_by_url(SPREADSHEET_URL).sheet1
    CONNECTION_STATUS = True
    print("Successfully connected to Google Sheets.")

except FileNotFoundError as e:
    print(f"Error: {e}")
    QMessageBox.critical(None, "File Error", "The JSON key file was not found. Please ensure it is in the correct directory.")
    SHEET = None
    CONNECTION_STATUS = False
except Exception as e:
    print(f"Error connecting to Google Sheets: {e}")
    QMessageBox.critical(None, "Connection Error", 
                         "Could not connect to the Google Sheet. Please check the following:\n"
                         "1. The JSON key file name is correct.\n"
                         "2. The Google Sheet has been shared with the service account email as an 'Editor'.\n"
                         "3. The Google Sheets API is enabled for your project.\n"
                         f"Details: {e}")
    SHEET = None
    CONNECTION_STATUS = False


# Theme colors
THEMES = {
    "Green": {
        "primary": "#008764",
        "primary_hover": "#006b51",
        "background": "#f5f7fa",
        "foreground": "#333",
        "secondary_background": "#fff",
        "line": "#e0e0e0",
        "dialog_button": "#f0f0f0",
        "selection": "#d1f7e0"
    },
    "Orange": {
        "primary": "#FF8C00",
        "primary_hover": "#E57E00",
        "background": "#FFF5E0",
        "foreground": "#333",
        "secondary_background": "#fff",
        "line": "#FFD7B0",
        "dialog_button": "#f0f0f0",
        "selection": "#FFEBC9"
    },
    "Yellow": {
        "primary": "#FFC107",
        "primary_hover": "#E5AD06",
        "background": "#FFFDE7",
        "foreground": "#333",
        "secondary_background": "#fff",
        "line": "#FFF2C4",
        "dialog_button": "#f0f0f0",
        "selection": "#FFF8D7"
    },
    "Dark": {
        "primary": "#607D8B",
        "primary_hover": "#455A64",
        "background": "#263238",
        "foreground": "#ECEFF1",
        "secondary_background": "#37474F",
        "line": "#455A64",
        "dialog_button": "#546E7A",
        "selection": "#455A64"
    }
}

class ColorButton(QPushButton):
    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self.color = color
        self.setObjectName("colorButton")
        self.setStyleSheet(f"background-color: {self.color}; border: 1px solid black;")

    def mousePressEvent(self, event):
        self.parent().theme_selected = self.color
        super().mousePressEvent(event)


# ==============================================================================
# --- Settings Dialog Class ---
# ==============================================================================
class SettingsDialog(QDialog):
    def __init__(self, current_font, current_size, current_theme, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedSize(300, 200)
        self.current_font = current_font
        self.current_size = current_size
        self.current_theme = current_theme
        self.theme_selected = self.current_theme
        
        # We will apply the stylesheet only once on init
        self.setStyleSheet(self.get_stylesheet(self.current_theme))

        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        # Theme Section
        theme_layout = QVBoxLayout()
        theme_label = QLabel("Theme:")
        theme_layout.addWidget(theme_label)

        color_layout = QHBoxLayout()
        self.themes = {}
        for name, colors in THEMES.items():
            button = ColorButton(colors["primary"])
            button.clicked.connect(lambda _, n=name: self.set_theme(n))
            button.setToolTip(name)
            color_layout.addWidget(button)
            self.themes[name] = button

        theme_layout.addLayout(color_layout)
        main_layout.addLayout(theme_layout)

        # Font Section
        font_layout = QHBoxLayout()
        font_label = QLabel("Font:")
        self.font_combo = QComboBox()
        self.font_combo.addItems(sorted(QFontDatabase.families()))
        self.font_combo.setCurrentText(self.current_font)
        font_layout.addWidget(font_label)
        font_layout.addWidget(self.font_combo)
        main_layout.addLayout(font_layout)

        # Font Size Section
        size_layout = QHBoxLayout()
        size_label = QLabel("Font Size:")
        self.size_spinbox = QSpinBox()
        self.size_spinbox.setRange(8, 24)
        self.size_spinbox.setValue(self.current_size)
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.size_spinbox)
        main_layout.addLayout(size_layout)

        # Apply and Cancel Buttons
        button_layout = QHBoxLayout()
        apply_button = QPushButton("Apply")
        apply_button.setObjectName("dialogButton")
        apply_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("dialogButton")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(apply_button)
        button_layout.addWidget(cancel_button)
        main_layout.addLayout(button_layout)
    
    def set_theme(self, theme_name):
        self.theme_selected = theme_name
        
    def get_stylesheet(self, theme_name):
        colors = THEMES[theme_name]
        style = f"""
            QDialog {{
                background-color: {colors["background"]};
                color: {colors["foreground"]};
            }}
            QLabel {{
                color: {colors["foreground"]};
            }}
            QComboBox, QSpinBox {{
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: {colors["secondary_background"]};
                color: {colors["foreground"]};
            }}
            QPushButton {{
                color: #000;
                background-color: {colors["dialog_button"]};
                border: 1px solid #ccc;
                padding: 4px 8px;
            }}
            QPushButton:hover {{
                background-color: {colors["line"]};
            }}
        """
        return style

    def get_settings(self):
        return self.font_combo.currentText(), self.size_spinbox.value(), self.theme_selected


# ==============================================================================
# --- New Staff Dialog Class ---
# ==============================================================================
class NewStaffDialog(QDialog):
    def __init__(self, headers, parent=None):
        super().__init__(parent)
        # Pass font settings to stylesheet
        self.setWindowTitle("Add New Staff")
        if self.parent():
            self.setStyleSheet(self.parent().get_stylesheet(self.parent().clinician_font, self.parent().clinician_font_size, self.parent().current_theme))
        self.headers = headers
        self.editable_fields = {}

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        title_label = QLabel("Enter New Staff Details")
        title_label.setObjectName("titleLabel")
        main_layout.addWidget(title_label)

        form_layout = QVBoxLayout()
        form_layout.setSpacing(5)
        
        for header in self.headers:
            field_layout = QHBoxLayout()
            label = QLabel(f"{header}:")
            if header == "Photo":
                label.setText("Photo URL:")
            label.setFixedWidth(120)
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(f"Enter {header}...")
            self.editable_fields[header] = line_edit
            
            field_layout.addWidget(label)
            field_layout.addWidget(line_edit)
            form_layout.addLayout(field_layout)

        main_layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        clear_button = QPushButton("Clear")
        clear_button.setObjectName("dialogButton")
        clear_button.clicked.connect(self.clear_fields)
        button_layout.addWidget(clear_button)

        save_button = QPushButton("Save")
        save_button.setObjectName("dialogButton")
        save_button.clicked.connect(self.save_new_staff)
        button_layout.addWidget(save_button)
        
        main_layout.addLayout(button_layout)

    def clear_fields(self):
        for field in self.editable_fields.values():
            field.clear()

    def save_new_staff(self):
        reply = QMessageBox.question(self, 'Confirm Save',
                                     "Are you sure you want to save this new staff member?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            new_data = [self.editable_fields.get(header, QLineEdit()).text() for header in self.headers]
            self.new_staff_data = new_data
            self.accept()
        else:
            self.reject()

# ==============================================================================
# --- Main Application Class ---
# ==============================================================================
class NeuropediaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neuropedia Clinical Directory")
        self.resize(900, 700)
        self.setMinimumSize(900, 700)

        # Icon handling for both script and compiled executable
        icon_path = None
        if getattr(sys, 'frozen', False):
            # Nuitka stores the data files in a temp folder pointed to by _MEIPASS
            try:
                # This is the most reliable method for a one-file executable
                icon_path = os.path.join(sys._MEIPASS, "NCD.ico")
            except:
                # Fallback in case _MEIPASS is not set for some reason
                icon_path = "NCD.ico"
        else:
            # Standard Python script execution
            icon_path = "NCD.ico"
        
        # Now, check if the icon path exists and set it
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Warning: Icon file not found at {icon_path}. The application will run without an icon.")

        self.nam = QNetworkAccessManager()
        self.nam.finished.connect(self.handle_image_response)
        self.photo_requests = {}

        self.original_data = []
        self.headers = []
        self.current_selected_row = -1
        self.editable_fields = {}

        self.settings = self.load_settings()
        self.clinician_font = self.settings.get("font", "Roboto")
        self.clinician_font_size = self.settings.get("fontSize", 12)
        self.current_theme = self.settings.get("theme", "Green")
        self.version_rev = self.settings.get("version_rev", 14)
        
        self.init_ui()
        self.load_data()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        top_bar_layout = QHBoxLayout()
        title_label = QLabel("Neuropedia Clinical Directory")
        title_label.setObjectName("titleLabel")
        top_bar_layout.addWidget(title_label)
        top_bar_layout.addStretch()

        settings_button = QPushButton("Settings")
        settings_button.setObjectName("settingsButton")
        settings_button.clicked.connect(self.show_settings_dialog)
        top_bar_layout.addWidget(settings_button)

        about_button = QPushButton("About")
        about_button.setObjectName("aboutButton")
        about_button.clicked.connect(self.show_about_dialog)
        top_bar_layout.addWidget(about_button)
        main_layout.addLayout(top_bar_layout)

        filter_table_container = QWidget()
        filter_table_layout = QVBoxLayout(filter_table_container)
        filter_table_layout.setContentsMargins(0, 0, 0, 0)
        filter_table_layout.setSpacing(10)

        filter_group = QGroupBox("Search & Filter")
        filter_group.setObjectName("filterGroup")
        filter_layout = QHBoxLayout()
        filter_group.setLayout(filter_layout)

        # Location Filters
        location_layout = QHBoxLayout()
        location_layout.setSpacing(2)
        location_label = QLabel("Location:")
        location_label.setObjectName("filterLabel")
        location_layout.addWidget(location_label)
        self.location_checkboxes = []
        for loc in ["NPD", "NPS", "CDC"]:
            cb = QCheckBox(loc)
            cb.stateChanged.connect(self.filter_data)
            self.location_checkboxes.append(cb)
            location_layout.addWidget(cb)
        location_layout.addStretch()
        filter_layout.addLayout(location_layout)

        # Swapped "Role" and "Name" Filters
        self.role_search_edit = self.create_text_filter("Role:", filter_layout, self.filter_data)
        self.name_search_edit = self.create_text_filter("Name:", filter_layout, self.filter_data)
        
        # Other Filters
        self.age_combo = self.create_filter_dropdown("Age Group:", filter_layout)
        self.days_search_edit = self.create_text_filter("Days Available:", filter_layout, self.filter_data)
        self.specialty_search_edit = self.create_text_filter("Specialty Areas:", filter_layout, self.filter_data)
        self.languages_search_edit = self.create_text_filter("Languages:", filter_layout, self.filter_data)

        clear_button = QPushButton("Clear Filter")
        clear_button.setObjectName("clearButton")
        clear_button.clicked.connect(self.clear_filters)
        filter_layout.addWidget(clear_button)

        filter_table_layout.addWidget(filter_group)

        self.clinician_table = QTableWidget()
        self.clinician_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.clinician_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.clinician_table.itemSelectionChanged.connect(self.on_clinician_selected)
        self.clinician_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.clinician_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        filter_table_layout.addWidget(self.clinician_table)
        
        # New details container layout
        details_container = QWidget()
        details_layout_container = QVBoxLayout(details_container)
        details_layout_container.setContentsMargins(0, 0, 0, 0)
        details_layout_container.setSpacing(10)

        details_group = QGroupBox("Clinician Details")
        details_group.setObjectName("detailsGroup")
        
        # Main layout for the details group
        details_layout = QHBoxLayout()
        details_group.setLayout(details_layout)
        
        # Left side: Photo and details
        info_layout = QHBoxLayout()
        
        # Photo layout
        photo_layout = QVBoxLayout()
        self.photo_label = QLabel("No Photo")
        self.photo_label.setObjectName("photoLabel")
        self.photo_label.setFixedSize(120, 120)
        self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo_layout.addWidget(self.photo_label)
        photo_layout.addStretch()

        # Fields layout
        fields_scroll_area = QScrollArea()
        fields_scroll_area.setWidgetResizable(True)
        fields_scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        fields_widget = QWidget()
        self.fields_layout = QVBoxLayout(fields_widget)
        self.fields_layout.setSpacing(5)
        fields_scroll_area.setWidget(fields_widget)
        
        # Add photo and fields to the info_layout
        info_layout.addLayout(photo_layout)
        info_layout.addWidget(fields_scroll_area)
        
        # Right side: Specialty Areas
        specialty_layout = QVBoxLayout()
        specialty_label = QLabel("Specialty Areas:")
        specialty_label.setObjectName("filterLabel")
        self.specialty_browser = QTextBrowser()
        self.specialty_browser.setObjectName("specialtyBrowser")
        specialty_layout.addWidget(specialty_label)
        specialty_layout.addWidget(self.specialty_browser)

        # Add the two main sections to the details group layout
        details_layout.addLayout(info_layout, 1) 
        details_layout.addLayout(specialty_layout, 1) 
        
        details_layout_container.addWidget(details_group)

        update_button_layout = QHBoxLayout()
        update_button_layout.addStretch()

        new_staff_button = QPushButton("New Staff")
        new_staff_button.setObjectName("newStaffButton")
        new_staff_button.clicked.connect(self.add_new_staff)
        update_button_layout.addWidget(new_staff_button)

        refresh_button = QPushButton("Refresh")
        refresh_button.setObjectName("refreshButton")
        refresh_button.clicked.connect(self.load_data)
        update_button_layout.addWidget(refresh_button)
        
        self.update_button = QPushButton("Update Details")
        self.update_button.setObjectName("updateButton")
        self.update_button.clicked.connect(self.update_data)
        self.update_button.setEnabled(False)
        update_button_layout.addWidget(self.update_button)
        
        details_layout_container.addLayout(update_button_layout)
        
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(filter_table_container)
        splitter.addWidget(details_container)
        splitter.setSizes([450, 250])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.setObjectName("statusBar")
        self.footer_label = QLabel("Stephen/Khizar © 2025 - Neuropedia")
        self.footer_label.setObjectName("footerLabel")
        
        self.statusBar.addPermanentWidget(self.footer_label)
        
        if not CONNECTION_STATUS:
            self.statusBar.showMessage("Error: Could not connect to Google Sheets.", 5000)
        else:
            self.statusBar.showMessage("Successfully connected to Google Sheets.", 5000)
        
        # Initial stylesheet application
        self.setStyleSheet(self.get_stylesheet(self.clinician_font, self.clinician_font_size, self.current_theme))

    def create_filter_dropdown(self, label_text, parent_layout):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        label = QLabel(label_text)
        label.setObjectName("filterLabel")
        combo_box = QComboBox()
        combo_box.addItem("All")
        combo_box.currentIndexChanged.connect(self.filter_data)

        layout.addWidget(label)
        layout.addWidget(combo_box)
        parent_layout.addWidget(widget)
        
        return combo_box

    def create_text_filter(self, label_text, parent_layout, handler):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        label = QLabel(label_text)
        label.setObjectName("filterLabel")
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(f"Search by {label_text.lower()}...")
        line_edit.textChanged.connect(handler)

        layout.addWidget(label)
        layout.addWidget(line_edit)
        parent_layout.addWidget(widget)
        
        return line_edit

    def load_data(self):
        """Loads data from the Google Sheet and populates the UI elements."""
        if not SHEET:
            return

        try:
            self.statusBar.showMessage("Loading data from Google Sheets...", 0)
            QApplication.processEvents()
            all_data = SHEET.get_all_values()
            if not all_data:
                QMessageBox.warning(self, "Data Error", "The Google Sheet is empty.")
                self.statusBar.showMessage("Data load failed: Sheet is empty.", 5000)
                return

            self.headers = all_data[0]
            self.original_data = all_data[1:]

            self.clinician_table.setColumnCount(len(self.headers))
            self.clinician_table.setHorizontalHeaderLabels(self.headers)
            self.clinician_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            self.clinician_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            
            photo_col_idx = self.headers.index("Photo") if "Photo" in self.headers else -1
            if photo_col_idx != -1:
                self.clinician_table.hideColumn(photo_col_idx)

            self.populate_dropdowns()
            self.create_editable_fields()
            self.display_data(self.original_data)
            self.statusBar.showMessage("Data loaded successfully.", 5000)

        except Exception as e:
            QMessageBox.critical(self, "Data Load Error", f"Failed to load data from the sheet: {e}")
            self.statusBar.showMessage(f"Data load failed: {e}", 5000)

    def populate_dropdowns(self):
        """Populates the QComboBox widgets with unique values from the data."""
        dropdowns = {
            "Age Group Seen": self.age_combo,
        }
        
        for header, combo in dropdowns.items():
            if header in self.headers:
                header_idx = self.headers.index(header)
                values = sorted(list(set(row[header_idx] for row in self.original_data if row[header_idx])))
                combo.clear()
                combo.addItem("All")
                combo.addItems(values)

    def create_editable_fields(self):
        """Creates QLineEdit widgets for each header to enable editing."""
        while self.fields_layout.count():
            item = self.fields_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub_item = item.layout().takeAt(0)
                    if sub_item.widget():
                        sub_item.widget().deleteLater()
        
        self.editable_fields = {}
            
        for i, header in enumerate(self.headers):
            # Only create editable fields for specific headers
            if header in ["Photo", "Specialty Areas", "Languages Spoken"]:
                continue
            
            field_layout = QHBoxLayout()
            field_layout.setSpacing(5)
            label = QLabel(f"{header}:")
            label.setFixedWidth(100)
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(f"Enter {header}...")
            self.editable_fields[header] = line_edit
            
            field_layout.addWidget(label)
            field_layout.addWidget(line_edit)
            self.fields_layout.addLayout(field_layout)
        
        # Apply font settings on creation
        self.setStyleSheet(self.get_stylesheet(self.clinician_font, self.clinician_font_size, self.current_theme))
        
    def display_data(self, data):
        """Populates the QTableWidget with the provided data."""
        self.clinician_table.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):
            for col_idx, item_data in enumerate(row_data):
                self.clinician_table.setItem(row_idx, col_idx, QTableWidgetItem(str(item_data)))
        
        self.clinician_table.clearSelection()
        self.current_selected_row = -1
        self.clear_editable_fields()

    def filter_data(self):
        """Filters the data based on the selected criteria."""
        filtered_data = self.original_data
        
        selected_locations = [cb.text() for cb in self.location_checkboxes if cb.isChecked()]
        if selected_locations:
            loc_idx = self.headers.index("Location")
            filtered_data = [row for row in filtered_data if any(loc in row[loc_idx] for loc in selected_locations)]

        name_query = self.name_search_edit.text().strip().lower()
        if name_query:
            name_idx = self.headers.index("Clinicians Name")
            filtered_data = [row for row in filtered_data if name_query in row[name_idx].lower()]
        
        filters = {
            "Age Group Seen": self.age_combo.currentText(),
        }

        for header, value in filters.items():
            if value != "All" and value != "":
                header_idx = self.headers.index(header)
                filtered_data = [row for row in filtered_data if row[header_idx] == value]
        
        role_query = self.role_search_edit.text().strip().lower()
        if role_query:
            role_idx = self.headers.index("Role")
            filtered_data = [row for row in filtered_data if role_query in row[role_idx].lower()]

        days_query = self.days_search_edit.text().strip().lower()
        if days_query:
            days_idx = self.headers.index("Days Available")
            filtered_data = [row for row in filtered_data if days_query in row[days_idx].lower()]
        
        specialty_query = self.specialty_search_edit.text().strip().lower()
        if specialty_query:
            specialty_idx = self.headers.index("Specialty Areas")
            filtered_data = [row for row in filtered_data if specialty_query in row[specialty_idx].lower()]

        languages_query = self.languages_search_edit.text().strip().lower()
        if languages_query:
            languages_idx = self.headers.index("Languages Spoken")
            filtered_data = [row for row in filtered_data if languages_query in row[languages_idx].lower()]

        self.display_data(filtered_data)

    def clear_filters(self):
        """Resets all filter options and reloads the full dataset."""
        for cb in self.location_checkboxes:
            cb.setChecked(False)
        self.name_search_edit.clear()
        self.age_combo.setCurrentIndex(0)
        self.role_search_edit.clear()
        self.days_search_edit.clear()
        self.specialty_search_edit.clear()
        self.languages_search_edit.clear()
        self.display_data(self.original_data)

    def on_clinician_selected(self):
        """Populates editable fields when a clinician is selected in the table."""
        selected_items = self.clinician_table.selectedItems()
        if not selected_items:
            self.current_selected_row = -1
            self.clear_editable_fields()
            self.update_button.setEnabled(False)
            return

        row_idx = selected_items[0].row()
        self.current_selected_row = row_idx
        self.update_button.setEnabled(True)

        row_data = [self.clinician_table.item(row_idx, col).text() for col in range(self.clinician_table.columnCount())]
        
        photo_url = ""
        specialty_text = ""
        for i, header in enumerate(self.headers):
            if header == "Photo":
                photo_url = row_data[i]
            elif header == "Specialty Areas":
                specialty_text = row_data[i]
            else:
                if header in self.editable_fields:
                    self.editable_fields[header].setText(row_data[i])
        
        self.specialty_browser.setText(specialty_text)
        self.load_image_from_url(photo_url)

    def clear_editable_fields(self):
        """Clears all editable fields and the photo label."""
        for field in self.editable_fields.values():
            field.clear()
        self.photo_label.setPixmap(QPixmap())
        self.photo_label.setText("No Photo")
        self.specialty_browser.clear()

    def load_image_from_url(self, url):
        """Loads an image from a URL and displays it in the photo label."""
        self.photo_label.setText("Loading...")
        if not url or not url.strip().startswith(('http://', 'https://')):
            self.photo_label.setText("No Photo")
            return

        request = QNetworkRequest(QUrl(url))
        self.photo_requests[url] = self.photo_label
        self.nam.get(request)

    def handle_image_response(self, reply):
        """Handles the network reply for image loading."""
        url = reply.url().toString()
        label = self.photo_requests.pop(url, None)
        if label:
            if reply.error() == QNetworkReply.NetworkError.NoError:
                pixmap = QPixmap()
                pixmap.loadFromData(reply.readAll())
                if not pixmap.isNull():
                    label.setPixmap(pixmap.scaled(label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                else:
                    label.setText("Image Error")
            else:
                print(f"Error loading image from {url}: {reply.errorString()}")
                label.setText("Image Error")
        reply.deleteLater()

    def update_data(self):
        """Updates the Google Sheet with the new data from the editable fields."""
        if self.current_selected_row == -1 or not SHEET:
            QMessageBox.warning(self, "Selection Error", "Please select a clinician to update.")
            return

        selected_clinician_name = self.clinician_table.item(self.current_selected_row, self.headers.index("Clinicians Name")).text()
        original_row_idx = -1
        for i, row in enumerate(self.original_data):
            if row[self.headers.index("Clinicians Name")] == selected_clinician_name:
                original_row_idx = i + 2
                break

        if original_row_idx == -1:
            QMessageBox.critical(self, "Update Error", "Could not find the original row in the sheet.")
            return

        reply = QMessageBox.question(self, 'Confirm Update', 
                                     "Are you sure you want to update the details for this clinician?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return

        try:
            self.statusBar.showMessage("Updating data...", 0)
            QApplication.processEvents()
            new_values = []
            for header in self.headers:
                if header == "Photo":
                    photo_idx = self.headers.index("Photo")
                    new_values.append(self.clinician_table.item(self.current_selected_row, photo_idx).text())
                elif header == "Specialty Areas":
                    new_values.append(self.specialty_browser.toPlainText())
                elif header == "Languages Spoken":
                    languages_idx = self.headers.index("Languages Spoken")
                    new_values.append(self.clinician_table.item(self.current_selected_row, languages_idx).text())
                else:
                    if header in self.editable_fields:
                        new_values.append(self.editable_fields[header].text())
                    else:
                        col_idx = self.headers.index(header)
                        new_values.append(self.clinician_table.item(self.current_selected_row, col_idx).text())

            SHEET.update(range_name=f"A{original_row_idx}:{chr(ord('A') + len(self.headers) - 1)}{original_row_idx}", values=[new_values])
            QMessageBox.information(self, "Success", "Clinician details updated successfully!")
            self.load_data()
            self.version_rev += 1
            self.save_settings()
            self.statusBar.showMessage("Update successful.", 5000)

        except Exception as e:
            QMessageBox.critical(self, "API Error", f"Failed to update the Google Sheet: {e}")
            self.statusBar.showMessage(f"Save failed: {e}", 5000)

    def add_new_staff(self):
        """Checks for password before opening dialog to add a new staff member."""
        password, ok = QInputDialog.getText(self, "Password Required", "Enter password to add new staff:", QLineEdit.EchoMode.Password)
        if ok and password == "Stephendi@s":
            dialog = NewStaffDialog(self.headers, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_data = dialog.new_staff_data
                try:
                    self.statusBar.showMessage("Saving new staff...", 0)
                    QApplication.processEvents()
                    SHEET.append_row(new_data)
                    QMessageBox.information(self, "Success", "New staff member added successfully!")
                    self.load_data()
                    self.statusBar.showMessage("New staff saved successfully.", 5000)
                except Exception as e:
                    QMessageBox.critical(self, "API Error", f"Failed to add new staff: {e}")
                    self.statusBar.showMessage(f"Save failed: {e}", 5000)
        elif ok:
            QMessageBox.warning(self, "Access Denied", "Incorrect password.")

    def show_about_dialog(self):
        about_text = f"<b>Neuropedia Clinical Directory</b><br><b>Version:</b> V2.0.{self.version_rev}<br><br>" \
                     "<b>App:</b> Stephen Dias<br>" \
                     "<b>Database:</b> Khizar Naeem"
        QMessageBox.about(self, "About Neuropedia Clinical Directory", about_text)
    
    def show_settings_dialog(self):
        dialog = SettingsDialog(self.clinician_font, self.clinician_font_size, self.current_theme, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_font, new_size, new_theme = dialog.get_settings()
            self.clinician_font = new_font
            self.clinician_font_size = new_size
            self.current_theme = new_theme
            self.setStyleSheet(self.get_stylesheet(self.clinician_font, self.clinician_font_size, self.current_theme))
            self.save_settings()

    def load_settings(self):
        settings_dir = os.path.join(os.getenv("PROGRAMDATA", "."), "Neuropedia")
        settings_path = os.path.join(settings_dir, "settings.json")
        settings = {}
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r") as f:
                    settings = json.load(f)
            except Exception as e:
                print(f"Error loading settings file: {e}")
        
        # Ensure version_rev is always an integer with a fallback.
        if "version_rev" not in settings or not isinstance(settings["version_rev"], int):
            settings["version_rev"] = 14
        return settings

    def save_settings(self):
        settings_dir = os.path.join(os.getenv("PROGRAMDATA", "."), "Neuropedia")
        if not os.path.exists(settings_dir):
            try:
                os.makedirs(settings_dir)
            except OSError as e:
                print(f"Error creating settings directory: {e}")
                return
        settings_path = os.path.join(settings_dir, "settings.json")
        try:
            with open(settings_path, "w") as f:
                json.dump({"font": self.clinician_font, "fontSize": self.clinician_font_size, "theme": self.current_theme, "version_rev": self.version_rev}, f)
        except Exception as e:
            print(f"Error saving settings file: {e}")

    def get_stylesheet(self, font_name="Roboto", font_size=12, theme="Green"):
        colors = THEMES.get(theme, THEMES["Green"])
        
        return f"""
            QWidget {{
                background-color: {colors["background"]};
                color: {colors["foreground"]};
                font-family: "{font_name}", "Helvetica", "Arial", sans-serif;
                font-size: {font_size}px;
            }}
            QSplitter::handle {{
                background-color: {colors["line"]};
                border: 1px solid {colors["line"]};
                border-radius: 4px;
            }}
            #titleLabel {{
                font-size: 20px;
                color: {colors["primary"]};
                margin-bottom: 5px;
                padding-left: 5px;
            }}
            QGroupBox {{
                color: {colors["primary"]};
                border: 1px solid {colors["line"]};
                border-radius: 8px;
                margin-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
            }}
            #filterLabel {{
                font-size: 9px;
                font-weight: 500;
                color: {colors["foreground"]};
            }}
            QComboBox, QLineEdit, QTableWidget, QTableWidget::item, QTextBrowser, QSpinBox {{
                padding: 4px;
                border: 1px solid {colors["line"]};
                border-radius: 5px;
                background-color: {colors["secondary_background"]};
                color: {colors["foreground"]};
            }}
            QComboBox::drop-down {{
                border: 0px;
                width: 10px;
            }}
            QComboBox::down-arrow {{
                image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgZmlsbD0iY3VycmVudENvbG9yIiBjbGFzcz0iYmkgYmktY2hldnJvbi1kb3duIiB2aWV3Qm94PSIwIDAgMTYgMTYiPgogIDxwYXRoIGZpbGw9IiMwMDg3NjQiIGQ9MTE2LjQ2IDQuNjQ2QS41LjUgMCAwIDEgMi4zNTQgNC41bDEuMzk2IDEuMzk2IDIuMDMtMS45MzNhMS41IDEuNSAwIDEgMSAyLjEyMiAyLjEyMmwtNC4yNSA0LjI1YS41LjUgMCAwIDEtLjcwOCAwTC0uOTk5IDQuNjQ2QS41LjUuMCAwIDEtLjk5OSA0LjY0NlZ6Ii8+Cjwvc3ZnPg==);
                width: 10px;
                height: 10px;
            }}
            QTableWidget {{
                border: 1px solid {colors["line"]};
                border-radius: 8px;
                background-color: {colors["secondary_background"]};
                gridline-color: {colors["line"]};
            }}
            QTableWidget::item {{
                padding: 4px;
            }}
            QTableWidget::item:selected {{
                background-color: {colors["selection"]};
                color: {colors["foreground"]};
            }}
            QHeaderView::section {{
                background-color: {colors["primary"]};
                color: {colors["secondary_background"]};
                padding: 6px;
                border: 1px solid {colors["line"]};
                border-radius: 4px;
                font-size: 12px;
            }}
            QHeaderView::section:vertical {{
                background-color: {colors["primary"]};
            }}
            QTableCornerButton::section {{
                background-color: {colors["primary"]};
            }}
            QPushButton {{
                padding: 8px 12px;
                border: none;
                border-radius: 6px;
                color: {colors["secondary_background"]};
                background-color: {colors["primary"]};
            }}
            QPushButton:hover {{
                background-color: {colors["primary_hover"]};
            }}
            QMessageBox QPushButton, QInputDialog QPushButton {{
                color: {colors["foreground"]};
            }}
            #dialogButton {{
                background-color: {colors["dialog_button"]};
                color: {colors["foreground"]};
                border: 1px solid {colors["line"]};
            }}
            #dialogButton:hover {{
                background-color: {colors["line"]};
            }}
            #updateButton:disabled {{
                background-color: #a0a0a0;
            }}
            #locationGroupBox {{
                border: none;
            }}
            #footerLabel {{
                font-size: 10px;
                color: {colors["foreground"]};
                padding: 5px;
            }}
            QCheckBox::indicator {{
                background-color: {colors["secondary_background"]};
                border: 1px solid {colors["line"]};
                width: 11px;
                height: 11px;
            }}
            QCheckBox::indicator:checked {{
                background-color: {colors["primary"]};
                border: 1px solid {colors["primary"]};
                image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMyIgaGVpZ2h0PSIxMyIgdmlld0JveD0iMCAwIDE2IDE2Ij4KICA8cGF0aCBmaWxsPSIjRkZGIiBkPSJNMTMuODU0IDMuNjQ2YS41LjUgMCAwIDEtLjcwOCAwbC03IDdhLjUuNSAwIDAgMS0uNzA4IDBMMy4xNDYgNy41YTEgMSAwIDAg0-1LjQxNCAxLjQxNGwyLjgyOSA0LjU4NWEuNS41IDAgMCAwIC43MDcgLjcwN0wxMy44NCA0LjM1NGEuNS41IDAgMCAxIDAtLjcwN1oiLz4KPC9zdmc+);
            }}
            QCheckBox {{
                font-size: {font_size}px;
            }}
            #specialtyBrowser {{
                background-color: {colors["secondary_background"]};
                color: {colors["foreground"]};
                border: 1px solid {colors["line"]};
                border-radius: 5px;
            }}
            #photoLabel {{
                border: 2px solid {colors["primary"]};
                background-color: {colors["secondary_background"]};
            }}
        """

if __name__ == '__main__':
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    if not CONNECTION_STATUS:
        QMessageBox.critical(None, "Initialization Error", "Application failed to connect to Google Sheets. Exiting.")
        sys.exit(-1)
    else:
        ex = NeuropediaApp()
        ex.show()
        sys.exit(app.exec())
