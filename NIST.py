import sys
import json
import requests
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
    QLabel, QPushButton, QComboBox, QFileDialog, QTextEdit, QSplitter
)
from PyQt6.QtCore import Qt

# Emoji dictionary for category names
# Emoji dictionary for category names (English + Hebrew)
# Emoji dictionary for category names (English + Hebrew)
CATEGORY_EMOJIS = {
    "Access Control": "🔑 Access Control (בקרת גישה)",
    "Audit and Accountability": "📜 Audit and Accountability (רישום לוגים)",
    "Awareness and Training": "🎓 Awareness and Training (מודעות והדרכה)",
    "Configuration Management": "⚙ Configuration Management (ניהול תצורה)",
    "Contingency Planning": "🚨 Contingency Planning (תכנון מגירה)",
    "Identification and Authentication": "🆔 Identification and Authentication (זיהוי ואימות)",
    "Incident Response": "🚔 Incident Response (תגובה לאירועים)",
    "Maintenance": "🔧 Maintenance (תחזוקה)",
    "Media Protection": "📀 Media Protection (הגנה על מדיה)",
    "Personnel Security": "👮 Personnel Security (אבטחת כוח אדם)",
    "Physical and Environmental Protection": "🏢 Physical and Environmental Protection (הגנה פיזית וסביבתית)",
    "Planning": "📅 Planning (תכנון)",
    "Program Management": "📈 Program Management (ניהול תוכניות)",
    "Risk Assessment": "⚖ Risk Assessment (הערכת סיכונים)",
    "Security Assessment and Authorization": "✅ Security Assessment and Authorization (הערכת אבטחה והרשאות)",
    "System and Communications Protection": "📡 System and Communications Protection (הגנת מערכות ותקשורת)",
    "System and Information Integrity": "🔍 System and Information Integrity (שלמות מערכת ומידע)",
}



class NISTControlApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NIST SP 800-53 Control Viewer by ibarkay")
        self.setGeometry(100, 100, 1200, 700)

        # Main Layout (Horizontal Split)
        self.main_layout = QHBoxLayout(self)

        # Left Layout (Search, Category, and List)
        self.left_layout = QVBoxLayout()

        # Search Bar
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Search controls...")
        self.search_bar.textChanged.connect(self.filter_controls)
        self.left_layout.addWidget(self.search_bar)

        # Category Dropdown
        self.category_dropdown = QComboBox(self)
        self.category_dropdown.addItem("📋 All Categories")  # Default option with emoji
        self.category_dropdown.currentTextChanged.connect(self.filter_controls)
        self.left_layout.addWidget(self.category_dropdown)

        # Control List
        self.control_list = QListWidget(self)
        self.control_list.itemClicked.connect(self.show_control_details)
        self.control_list.currentRowChanged.connect(self.show_control_details)  # Enable Arrow Key Navigation
        self.left_layout.addWidget(self.control_list)

        # Export Button
        self.export_button = QPushButton("Export Controls to CSV", self)
        self.export_button.clicked.connect(self.export_controls)
        self.left_layout.addWidget(self.export_button)

        # Right Layout (Control Details)
        self.control_details = QTextEdit(self)
        self.control_details.setReadOnly(True)
        self.control_details.setPlaceholderText("Select a control to view full details...")
        self.control_details.setStyleSheet("font-size: 14px;")

        # Splitter to make it resizable
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        left_widget = QWidget()
        left_widget.setLayout(self.left_layout)
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(self.control_details)

        # Adjust initial size
        self.splitter.setSizes([500, 700])

        # Add Splitter to Layout
        self.main_layout.addWidget(self.splitter)
        self.setLayout(self.main_layout)

        # Load NIST Controls
        self.controls_df = pd.DataFrame()
        self.load_nist_controls()

    def load_nist_controls(self):
        """Load NIST SP 800-53 controls from GitHub (JSON format)."""
        url = "https://raw.githubusercontent.com/usnistgov/oscal-content/refs/heads/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            controls = []

            for group in data["catalog"]["groups"]:
                category = group["title"]
                category_name = CATEGORY_EMOJIS.get(category, f"📌 {category} (לא מוגדר)")  # Default if missing

                for control in group.get("controls", []):
                    control_info = {
                        "id": control.get("id", "Unknown"),  # ID is important for sorting
                        "title": control.get("title", "No Title Available"),
                        "category": category_name,  # English + Hebrew
                        "family": control.get("class", "Unknown"),
                        "description": self.format_text(self.extract_text(control)),
                        "guidance": self.format_text(self.extract_guidance(control)),
                        "parameters": self.extract_parameters(control),
                        "related": ", ".join([link.get("href", "Unknown") for link in control.get("links", [])])
                    }
                    controls.append(control_info)

            # 🛠 Fix: Extract the numeric part correctly and ensure sorting
            self.controls_df = pd.DataFrame(controls).sort_values(
                by="id",
                key=lambda x: x.str.extract(r'(\d+)$')[0].astype(float)  # Fix: Extract first column as Series
            )

            # Add sorted categories to dropdown
            sorted_categories = sorted(set(control["category"] for control in controls))
            self.category_dropdown.addItems(sorted_categories)

            self.display_controls()
        else:
            self.control_details.setText("Failed to load NIST controls.")



    def extract_text(self, control):
        """Extracts control description text from 'parts'."""
        if "parts" in control:
            for part in control["parts"]:
                if part.get("name") == "statement":
                    return part.get("prose", "No Description Available")
        return "No Description Available"

    def extract_guidance(self, control):
        """Extracts supplemental guidance from 'parts'."""
        if "parts" in control:
            for part in control["parts"]:
                if part.get("name") == "guidance":
                    return part.get("prose", "No Guidance Available")
        return "No Guidance Available"

    def extract_parameters(self, control):
        """Extracts parameters (like variable settings) from 'params'."""
        if "params" in control:
            return "\n".join([f"{param.get('id', 'Unknown')}: {param.get('label', 'No Parameter Label')}" for param in control["params"]])
        return "No Parameters Available"

    def format_text(self, text):
        """Formats text by adding new lines and emojis for better readability."""
        sentences = text.split(". ")
        formatted_text = "<br>".join([
            f"✔ {sentence.strip()}" for sentence in sentences if sentence
        ])
        return formatted_text

    def display_controls(self):
        """Populate list with controls."""
        self.control_list.clear()
        for index, row in self.controls_df.iterrows():
            self.control_list.addItem(f"{row['id']} - {row['title']}")

    def filter_controls(self):
        """Filter controls based on search and category selection."""
        search_text = self.search_bar.text().lower()
        selected_category = self.category_dropdown.currentText()

        filtered_df = self.controls_df[
            self.controls_df["title"].str.lower().str.contains(search_text)
        ]

        if selected_category != "📋 All Categories":
            filtered_df = filtered_df[filtered_df["category"] == selected_category]

        self.control_list.clear()
        for index, row in filtered_df.iterrows():
            self.control_list.addItem(f"{row['id']} - {row['title']}")

    def show_control_details(self, index):
        """Display full control details in the right panel when clicking or using arrow keys."""
        if isinstance(index, int):
            if index < 0 or index >= self.control_list.count():
                return
            item = self.control_list.item(index)
        else:
            item = index

        control_id = item.text().split(" - ")[0]
        control = self.controls_df[self.controls_df["id"] == control_id].iloc[0]

        details = (
            f"<h2 style='color: white;'>🔹 {control['title']}</h2>"
            f"<p><b><span style='color: orange;'>ID:</span></b> {control['id']}</p>"
            f"<p><b><span style='color: orange;'>Category:</span></b> {control['category']}</p>"
            f"<p><b><span style='color: orange;'>Family:</span></b> {control['family']}</p>"
            f"<hr>"
            f"<p style='color: white;'>{control['description']}</p>"
            f"<hr>"
            f"<p style='color: white;'>{control['guidance']}</p>"
        )
        self.control_details.setHtml(details)

    def export_controls(self):
        """Export filtered controls to CSV."""
        file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "CSV Files (*.csv);;All Files (*)")
        if file_name:
            self.controls_df.to_csv(file_name, index=False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NISTControlApp()
    window.show()
    sys.exit(app.exec())
