#!/usr/bin/env python3
import subprocess
import sys
import os
import json
import signal
import inspect
from PyQt5.QtCore import QThread, pyqtSignal, QUrl, Qt
from PyQt5.QtGui import QDesktopServices, QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QScrollArea, QDialog, QMessageBox, QMainWindow, QComboBox

# Function to add Flatpak remotes if they don't already exist
def add_flatpak_remotes():
    remotes = [
        ("flathub", "https://flathub.org/repo/flathub.flatpakrepo", ""),
        ("flathub-floss", "https://flathub.org/repo/flathub.flatpakrepo", "--subset=floss"),
        ("flathub-verified_floss", "https://flathub.org/repo/flathub.flatpakrepo", "--subset=verified_floss"),
        ("flathub-verified", "https://flathub.org/repo/flathub.flatpakrepo", "--subset=verified"),
    ]

    try:
        # Retrieve the list of existing remotes for the user
        existing_remotes_output = subprocess.check_output(["flatpak", "remotes", "--user"]).decode().strip().split("\n")
        # Initialize a list to store the existing remote names
        existing_remotes = []
        for line in existing_remotes_output:
            split_line = line.split()
            if len(split_line) > 0:  # Ensure there is at least one element after split
                existing_remotes.append(split_line[0])  # Append the remote name to the list

    except subprocess.CalledProcessError as e:
        print(f"Failed to retrieve existing remotes: {e}")
        existing_remotes = []

    # Loop through the remotes that need to be added
    for name, url, subset in remotes:
        if name in existing_remotes:
            print(f"Remote '{name}' already exists. Skipping addition.")
            continue  # Skip adding this remote since it already exists

        # Command to add the remote if it does not already exist
        cmd = [
            "flatpak", "remote-add", "--if-not-exists", "--user",
            name, url
        ]
        if subset:
            cmd.insert(4, subset)  # Insert the subset option into the command

        try:
            # Run the command to add the remote
            subprocess.run(cmd, check=True)
            print(f"Remote '{name}' added.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to add remote '{name}': {e}")


# Function to validate that an app is not a core system package (e.g., Freedesktop, Gnome, KDE)
def valid_package(app_id):
    if (
        app_id.startswith("org.freedesktop.")
        or app_id.startswith("org.gnome.")
        or app_id.startswith("org.kde.")
        or app_id == ""
    ):
        return False
    return True

# Thread to handle searching for apps on Flathub
class SearchThread(QThread):
    success = pyqtSignal(str)

    def __init__(self, query):
        super(SearchThread, self).__init__()
        self.query = query.strip().lower()  # Lowercase query for case-insensitive matching

    def run(self):
        results = []
        try:
            # Execute the flatpak search command with specific columns
            out = subprocess.check_output(
                ["flatpak", "search", "--columns=application,name,remotes", self.query]
            ).decode()

            if "No matches found" in out:
                self.success.emit(json.dumps(results))
                return

            # Process each line of the output
            for line in out.strip().split("\n"):
                parts = line.split("\t")
                if len(parts) >= 3:
                    application_id = parts[0].strip()  # Application ID
                    name = parts[1].strip()  # App name
                    remotes = parts[2].strip().split(",")  # Remotes list
                    label = self.get_label(remotes)

                    # Match query against the name or application ID
                    if self.query in name.lower() or self.query in application_id.lower():
                        results.append({"name": name, "label": label, "application_id": application_id})

            self.success.emit(json.dumps(results))

        except subprocess.CalledProcessError as e:
            print(f"Error during search: {e}")
            self.success.emit(json.dumps([]))

    # Determine the label based on the remotes
    def get_label(self, remotes):
        if "flathub-verified-floss" in remotes:
            return "Verified & FOSS"
        elif "flathub-verified" in remotes:
            return "Verified"
        elif "flathub-floss" in remotes:
            return "FOSS"
        else:
            return ""

# Dialog for searching Flathub for apps
class SearchDialog(QDialog):
    def __init__(self):
        super(SearchDialog, self).__init__()
        self.setModal(True)
        self.setWindowTitle("Search Flathub for apps")
        self.setMinimumWidth(600)
        self.setMinimumHeight(300)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Search Flathub for apps")
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_clicked)

        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All Apps", "")
        self.filter_combo.addItem("FOSS Apps", "FOSS")
        self.filter_combo.addItem("Verified Apps", "Verified")
        self.filter_combo.addItem("Verified & FOSS Apps", "Verified & FOSS")

        # Layout for filters
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by:"))
        filter_layout.addWidget(self.filter_combo)

        # Layout for search input and button
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.input, stretch=1)
        search_layout.addWidget(self.search_button)

        # Layout for displaying search results
        self.results_layout = QVBoxLayout()
        self.results_layout.addWidget(QWidget())  # Adding a blank widget to help with layout
        results_widget = QWidget()
        results_widget.setLayout(self.results_layout)
        results_scrollarea = QScrollArea()
        results_scrollarea.setWidget(results_widget)
        results_scrollarea.setWidgetResizable(True)

        layout = QVBoxLayout(self)
        layout.addLayout(filter_layout)
        layout.addLayout(search_layout)
        layout.addWidget(results_scrollarea, stretch=1)

    # Slot triggered when the search button is clicked
    def search_clicked(self):
        print(f"Searching for: {self.input.text()}")

        self.input.setEnabled(False)
        self.search_button.setEnabled(False)
        self.search_button.setText("Searching ...")

        self.t = SearchThread(self.input.text())
        self.t.success.connect(self.search_results)
        self.t.start()

    # Slot to handle search results
    def search_results(self, results_json):
        self.input.setEnabled(True)
        self.search_button.setEnabled(True)
        self.search_button.setText("Search")

        # Clear previous results from the layout
        children = []
        for i in range(self.results_layout.count()):
            child = self.results_layout.itemAt(i).widget()
            if child:
                children.append(child)

        for child in children:
            child.deleteLater()

        # Add the search results to the layout
        results = json.loads(results_json)
        filter_type = self.filter_combo.currentData()

        if len(results) == 0:
            self.results_layout.addWidget(QLabel("App not found"))
        else:
            for result in results:
                if filter_type and result["label"] != filter_type:
                    continue
                app = SearchApp(result["name"], result["label"])
                self.results_layout.addWidget(app)

# Widget representing an individual app in the search results
class SearchApp(QWidget):
    install = pyqtSignal(str)

    def __init__(self, name, label):
        super(SearchApp, self).__init__()

        self.name = name
        self.label = label

        name_label = QLabel(self.name)
        name_label.setStyleSheet("QLabel { font-weight: bold }")

        if self.label:
            label_widget = QLabel(f"({self.label})")
            label_widget.setStyleSheet("QLabel { color: green; font-weight: bold }")
        else:
            label_widget = QLabel("")

        self.info_button = QPushButton("Info")
        self.info_button.clicked.connect(self.info_clicked)
        self.install_button = QPushButton("Install")
        self.install_button.clicked.connect(self.install_clicked)

        layout = QHBoxLayout()
        layout.addWidget(name_label)
        layout.addWidget(label_widget)
        layout.addStretch()
        layout.addWidget(self.info_button)
        layout.addWidget(self.install_button)

        self.setLayout(layout)

    # Open the app's Flathub page when the Info button is clicked
    def info_clicked(self):
        url = QUrl(f"https://flathub.org/apps/details/{self.name}")
        QDesktopServices.openUrl(url)

    # Install the app when the Install button is clicked
    def install_clicked(self):
        print(f"Installing: {self.name}")

        subprocess.run(
            [
                "/usr/bin/xterm",
                "-e",
                "/usr/bin/flatpak",
                "install",
                "--user",
                "flathub",
                self.name,
                "-y"
            ]
        )

        self.install.emit(self.name)

# Widget representing an installed app with options to run or delete it
class InstalledApp(QWidget):
    run = pyqtSignal(str)
    delete = pyqtSignal(str)

    def __init__(self, app_details):
        super(InstalledApp, self).__init__()

        self.app_details = app_details

        name = QLabel(self.app_details["Name"])
        name.setStyleSheet("QLabel { font-weight: bold }")

        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.run_clicked)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_clicked)

        layout = QHBoxLayout()
        layout.addWidget(name)
        layout.addStretch()
        layout.addWidget(self.run_button)
        layout.addWidget(self.delete_button)

        self.setLayout(layout)

    # Emit a signal to run the app when the Run button is clicked
    def run_clicked(self):
        print(f"Running: {self.app_details['ID']}")
        self.run.emit(self.app_details["ID"])

    # Emit a signal to delete the app when the Delete button is clicked
    def delete_clicked(self):
        d = QMessageBox()
        d.setText(f"Are you sure you want to delete {self.app_details['Name']}?")
        d.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        ret = d.exec_()

        if ret == QMessageBox.Yes:
            self.delete.emit(self.app_details["ID"])

# Widget that lists all installed apps and provides options to run or delete them
class InstalledApps(QWidget):
    def __init__(self):
        super(InstalledApps, self).__init__()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.update()

    # Update the list of installed apps
    def update(self):
        # Clear the layout
        children = []
        for i in range(self.layout.count()):
            child = self.layout.itemAt(i).widget()
            if child:
                children.append(child)

        for child in children:
            child.deleteLater()

        installed_apps = self.get_installed_apps()

        if len(installed_apps) == 0:
            label = QLabel("No Flatpak apps are installed yet")
            self.layout.addWidget(label)
        else:
            for name in sorted(list(installed_apps)):
                app = InstalledApp(installed_apps[name])
                app.run.connect(self.run_app)
                app.delete.connect(self.delete_app)
                self.layout.addWidget(app)

    # Run the selected app
    def run_app(self, id):
        subprocess.Popen(["flatpak", "run", "--user", id])

    # Delete the selected app
    def delete_app(self, id):
        print(f"Deleting: {id}")
        subprocess.run(
            ["/usr/bin/xterm", "-e", "/usr/bin/flatpak", "uninstall", "--user", id]
        )
        self.update()

    # Retrieve the list of installed apps and return as a dictionary
    def get_installed_apps(self):
        apps = {}
        try:
            out = subprocess.check_output(
                ["flatpak", "list", "--user", "--columns=application,name"]
            ).decode()

            for line in out.strip().split("\n"):
                if line:
                    parts = line.split("\t")
                    if len(parts) == 2:
                        app_id, name = parts
                        if valid_package(app_id):
                            apps[name] = {
                                "ID": app_id,
                                "Name": name,
                            }

        except subprocess.CalledProcessError as e:
            print(f"Error retrieving installed apps: {e}")
    
        return apps

# Main window for the Q-Paks application
class QPaksWindow(QMainWindow):
    def __init__(self, app):
        super(QPaksWindow, self).__init__()

        self.app = app
        self.setWindowTitle("Q-Paks")
        self.setWindowIcon(QIcon(self.get_icon_path()))

        self.installed_apps = InstalledApps()

        self.update_button = QPushButton("Update Apps")
        self.update_button.clicked.connect(self.update_button_clicked)
        install_button = QPushButton("Install New App")
        install_button.clicked.connect(self.install_button_clicked)

        # Layout for the buttons at the bottom of the window
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.update_button)
        buttons_layout.addWidget(install_button)

        # Layout for the installed apps list and buttons
        layout = QVBoxLayout()
        layout.addWidget(self.installed_apps)
        layout.addStretch()
        layout.addLayout(buttons_layout)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.installed_apps.update()
        self.show()

    # Update all installed apps when the Update button is clicked
    def update_button_clicked(self):
        subprocess.run(["/usr/bin/xterm", "-e", "flatpak", "update", "--user", "-y"])

    # Open the search dialog to install new apps when the Install New App button is clicked
    def install_button_clicked(self):
        d = SearchDialog()
        d.exec_()
        self.installed_apps.update()

    # Get the path to the application icon
    def get_icon_path(self):
        if sys.argv and sys.argv[0].startswith(sys.prefix):
            prefix = os.path.join(sys.prefix, "share/pixmaps")
        else:
            prefix = os.path.join(
                os.path.dirname(
                    os.path.abspath(inspect.getfile(inspect.currentframe()))
                ),
                "share",
            )
        return os.path.join(prefix, "q-paks.png")

# Main function to initialize the application
def main():
    def signal_handler(s, frame):
        print("\nCtrl-C pressed, quitting")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    add_flatpak_remotes()  # Ensure remotes are added

    app = QApplication(sys.argv)
    window = QPaksWindow(app)
    sys.exit(app.exec_())

# Entry point of the application
if __name__ == "__main__":
    main()
