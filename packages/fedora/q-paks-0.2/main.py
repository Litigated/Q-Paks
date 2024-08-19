#!/usr/bin/env python3

import sys
import os
import subprocess
import json
import signal
from PyQt5.QtCore import QThread, pyqtSignal, QUrl, Qt
from PyQt5.QtGui import QDesktopServices, QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QScrollArea, QDialog, QProgressDialog, QMessageBox, QHBoxLayout, QTextEdit, QMainWindow


def valid_package(app_id):
    if (
        app_id.startswith("org.freedesktop.")
        or app_id.startswith("org.gnome.")
        or app_id.startswith("org.kde.")
        or app_id == ""
    ):
        return False
    return True


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

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.input, stretch=1)
        search_layout.addWidget(self.search_button)

        self.results_layout = QVBoxLayout()
        self.results_layout.addWidget(QWidget())  # Adding a blank widget seems to help
        results_widget = QWidget()
        results_widget.setLayout(self.results_layout)
        results_scrollarea = QScrollArea()
        results_scrollarea.setWidget(results_widget)
        results_scrollarea.setWidgetResizable(True)

        layout = QVBoxLayout(self)
        layout.addLayout(search_layout)
        layout.addWidget(results_scrollarea, stretch=1)

    def search_clicked(self):
        print(f"Searching for: {self.input.text()}")

        self.input.setEnabled(False)
        self.search_button.setEnabled(False)
        self.search_button.setText("Searching ...")

        self.t = SearchThread(self.input.text())
        self.t.success.connect(self.search_results)
        self.t.start()

    def search_results(self, results_json):
        self.input.setEnabled(True)
        self.search_button.setEnabled(True)
        self.search_button.setText("Search")

        # Clear the layout
        children = []
        for i in range(self.results_layout.count()):
            child = self.results_layout.itemAt(i).widget()
            if child:
                children.append(child)

        for child in children:
            child.deleteLater()

        # Add the results
        results = json.loads(results_json)
        if len(results) == 0:
            self.results_layout.addWidget(QLabel("App not found"))
        else:
            for result in results:
                print(f"Result: {result}")
                app = SearchApp(result["app_id"], result["name"])
                self.results_layout.addWidget(app)


class SearchApp(QWidget):
    install = pyqtSignal(str)

    def __init__(self, app_id, name):
        super(SearchApp, self).__init__()

        self.app_id = app_id
        self.name = name

        name = QLabel(self.name)
        name.setStyleSheet("QLabel { font-weight: bold }")
        self.info_button = QPushButton("Info")
        self.info_button.clicked.connect(self.info_clicked)
        self.install_button = QPushButton("Install")
        self.install_button.clicked.connect(self.install_clicked)

        layout = QHBoxLayout()
        layout.addWidget(name)
        layout.addStretch()
        layout.addWidget(self.info_button)
        layout.addWidget(self.install_button)

        self.setLayout(layout)

    def info_clicked(self):
        url = QUrl(f"https://flathub.org/apps/details/{self.app_id}")
        QDesktopServices.openUrl(url)

    def install_clicked(self):
        print(f"Installing: {self.app_id}")

        subprocess.run(
            [
                "/usr/bin/xterm",
                "-e",
                "/usr/bin/flatpak",
                "install",
                "--user",
                "flathub",
                self.app_id,
            ]
        )


class SearchThread(QThread):
    success = pyqtSignal(str)

    def __init__(self, query):
        super(SearchThread, self).__init__()
        self.query = query

    def run(self):
        results = []

        out = subprocess.check_output(
            [
                "flatpak",
                "search",
                "--columns=application,name",
                self.query,
            ]
        ).decode()

        if "No matches found" in out:
            self.success.emit(json.dumps(results))
            return

        for line in out.split("\n"):
            line = line.strip()
            if valid_package(line):
                parts = line.split()
                app_id = parts[0]
                name = " ".join(parts[1:])
                results.append({"app_id": app_id, "name": name})

        self.success.emit(json.dumps(results))


class InstalledApp(QWidget):
    run = pyqtSignal(str)
    delete = pyqtSignal(str)

    def __init__(self, app_details):
        super(InstalledApp, self).__init__()

        self.app_details = app_details

        name = QLabel(self.app_details["Name"])
        name.setStyleSheet("QLabel { font-weight: bold }")
        size = QLabel(self.app_details["Installed"])
        size.setStyleSheet("QLabel { font-size: 10px }")
        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.run_clicked)
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_clicked)

        layout = QHBoxLayout()
        layout.addWidget(name)
        layout.addWidget(size)
        layout.addStretch()
        layout.addWidget(self.run_button)
        layout.addWidget(self.delete_button)

        self.setLayout(layout)

    def run_clicked(self):
        print(f"Running: {self.app_details['ID']}")
        self.run.emit(self.app_details["ID"])

    def delete_clicked(self):
        d = QMessageBox()
        d.setText(f"Are you sure you want to delete {self.app_details['Name']}?")
        d.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        ret = d.exec_()

        if ret == QMessageBox.Yes:
            self.delete.emit(self.app_details["ID"])


class InstalledApps(QWidget):
    def __init__(self):
        super(InstalledApps, self).__init__()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.update()

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

    def run_app(self, id):
        subprocess.Popen(["flatpak", "run", "--user", id])

    def delete_app(self, id):
        print(f"Deleting: {id}")
        subprocess.run(
            ["/usr/bin/xterm", "-e", "/usr/bin/flatpak", "uninstall", "--user", id]
        )
        self.update()

    def get_installed_apps(self):
        app_ids = []
        out = subprocess.check_output(
            ["flatpak", "list", "--user", "--columns=application"]
        ).decode()
        for line in out.split("\n"):
            line = line.strip()
            if valid_package(line):
                app_ids.append(line.strip())

        apps = {}
        for app_id in app_ids:
            out = subprocess.check_output(
                [
                    "flatpak",
                    "info",
                    "--user",
                    app_id,
                ]
            ).decode()
            lines = out.split("\n")
            app_details = {"Name": "".join(lines[0:3]).split("-")[0].strip()}
            for line in lines[3:]:
                try:
                    column_i = line.index(":")
                    key = line[0:column_i].strip()
                    val = line[column_i + 2 :].strip()
                    app_details[key] = val
                except ValueError:
                    pass

            apps[app_details["Name"]] = app_details

        return apps


class QubeAppsWindow(QMainWindow):
    def __init__(self, app):
        super(QubeAppsWindow, self).__init__()

        self.app = app
        self.setWindowTitle("Qpaks")
        self.setWindowIcon(QIcon(self.get_icon_path()))

        # Ensure Flathub is added
        subprocess.run(
            [
                "flatpak",
                "remote-add",
                "--user",
                "--if-not-exists",
                "flathub",
                "https://flathub.org/repo/flathub.flatpakrepo",
            ]
        )

        self.installed_apps = InstalledApps()

        self.update_button = QPushButton("Update Apps")
        self.update_button.clicked.connect(self.update_button_clicked)
        install_button = QPushButton("Install New App")
        install_button.clicked.connect(self.install_button_clicked)
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.update_button)
        buttons_layout.addWidget(install_button)

        layout = QVBoxLayout()
        layout.addWidget(self.installed_apps)
        layout.addStretch()
        layout.addLayout(buttons_layout)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.installed_apps.update()
        self.show()

    def update_button_clicked(self):
        subprocess.run(["/usr/bin/xterm", "-e", "flatpak", "update", "--user", "-y"])

    def install_button_clicked(self):
        d = SearchDialog()
        d.exec_()
        self.installed_apps.update()

    def get_icon_path(self):
        if sys.argv and sys.argv[0].startswith(sys.prefix):
            # Installed systemwide
            prefix = os.path.join(sys.prefix, "share/pixmaps")
        else:
            # Look for share directory relative to python file
            prefix = os.path.join(
                os.path.dirname(
                    os.path.abspath(inspect.getfile(inspect.currentframe()))
                ),
                "share",
            )
        return os.path.join(prefix, "qube-apps.png")


def main():
    # Allow Ctrl-C to smoothly quit the program instead of throwing an exception
    def signal_handler(s, frame):
        print("\nCtrl-C pressed, quitting")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    app = QApplication(sys.argv)
    window = QubeAppsWindow(app)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
