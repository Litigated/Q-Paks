# Q-Paks
Q-Paks is an application for Qubes OS, packaged for both Fedora and Debian-based systems. Q-Paks is a hard fork of Micah F Lee’s [Qubes Apps](https://github.com/micahflee/qube-apps). All credit goes to Micah F Lee, if you wish to support him, may I suggest donating [here](https://semiphemeral.com/donate/) to his new [Semiphemeral](https://semiphemeral.com) project or buy his book [here](https://hacksandleaks.com/).

After installing Q-Paks increase your AppVM or DispVM’s private storage size from 2GB to 10GB+, as some flatpaks will exceed the default private storage.
Please note that when you open Q-Paks for the first time, it may take a while. Similarly, the first search you perform may take some time as it needs to fetch Flathub's metadata.

## Pre-built Packages

You can download the pre-built packages:

- **Debian 12/Kicksecure 17/Whonix 17**: [Download .deb](https://github.com/Litigated/Q-Paks/releases/download/v0.2.1/q-paks-0.2.1.deb)
- Install with dpkg: ```sudo dpkg -i q-paks-0.2.1.deb```
- **Fedora 40**: [Download .rpm](https://github.com/Litigated/Q-Paks/releases/download/v0.2.1/q-paks-0.2.1-1.fc40.noarch.rpm)
- Install with dnf: ```sudo dnf install q-paks-0.2.1-1.fc40.noarch.rpm```

*Note: the .deb package may work on other Debian based distributions. However, only Debian 12, Kicksecure 17 and Whonix 17  have been tested.*

## Package Contents

The repository contains all the files used to create the `.deb` and `.rpm` packages, so you can review exactly what's inside.

- **Debian package files**: Located in `packages/debian/`
- **Fedora package files**: Located in `packages/fedora/`

## Building from Source

If you wish to build the packages from scratch using only the `main.py` file:

### For Debian 12/Kicksecure 17/Whonix 17

<details>
  <summary>Click to see more</summary>
  
  1. Download the ‘main.py’ from the ‘sources’ directory by typing:
```bash 
curl -O https://raw.githubusercontent.com/Litigated/Q-Paks/main/sources/main.py
```

2. Install the development tools needed:
```bash 
sudo apt-get install -y build-essential python3 python3-pyqt5 dh-make debhelper devscripts fakeroot
```

3. Create the Q-Paks building project directory change into it:
```bash
mkdir -p ~/q-paks-0.2.1
cd ~/q-paks-0.2.1
```

4. Create the necessary directories for the Q-Paks files:
```bash
mkdir -p usr/local/bin
mkdir -p usr/share/applications
mkdir -p usr/share/icons/hicolor/256x256/apps
mkdir -p DEBIAN
```

5.  Copy the main.py file into your local bin directory and make it executable:
```bash 
cp /home/user/main.py usr/local/bin/q-paks
chmod +x usr/local/bin/q-paks
```
 
6.  Create the desktop file:
```bash
cat <<EOL > usr/share/applications/q-paks.desktop
[Desktop Entry]
Name=Q-Paks
Exec=/usr/local/bin/q-paks
Icon=q-paks
Type=Application
Terminal=false
Categories=Utility;
EOL
```

7. Create the control file:
```bash 
cat <<EOL > DEBIAN/control
Package: q-paks
Version: 0.2.1
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-pyqt5, flatpak, xterm
Maintainer: Litigated <contact@litigated.uk>
Description: Q-Paks Application
 A simple application to manage Flatpak apps in Qubes OS.
Homepage: https://www.litigated.uk
EOL
```

7. Now, build the .deb package:
```bash 
dpkg-deb --build ~/q-paks-0.2.1
```

8. Move the .deb package into your desired Template or AppVM:
```bash
qvm-move ~/q-paks-0.2.1.deb
```

9. Open a terminal in the Template or AppVM, where you moved the Q-Paks pakcage into, & install the required dependencies:
```bash
sudo apt-get install python3-pyqt5 flatpak xterm -y
```

10. Finally, install the .deb package:
```bash
sudo dpkg -i ~/QubesIncoming/”YOUR DISPOSABLE VM NAME”/q-paks-0.2.1.deb
```
  
</details>

### For Fedora 40

<details>
  <summary>Click to see more</summary>
  
  1. Open a terminal in a disposable fedora 40 vm.

2. Download the ‘main.py’ from the ‘sources’ directory by typing:
```bash 
curl -O https://raw.githubusercontent.com/Litigated/Q-Paks/main/sources/main.py 
```

3. Install the development tools needed:
```bash
sudo dnf install rpm-build rpmdevtools qt5-qtbase-devel qt5-qtsvg-devel qt5-qttools-devel python3-qt5 python3-devel  -y 
```

4. Set up your build environment by merely typing:
```bash
rpmdev-setuptree 
```

5. Now, create the Q-Paks directory and enter the directory:
```bash 
mkdir ~/q-paks
cd ~/q-paks 
```

6. Inside the Q-Paks directory, create the version subdirectory:
```bash 
mkdir -p q-paks-0.2.1
```

7. Copy your downloaded main.py into the q-paks versioned directory:
```bash 
cp /home/user/main.py q-paks-0.2.1/
```

8. Create the desktop entry file:
```bash
cat <<EOF > q-paks-0.2.1/q-paks.desktop
[Desktop Entry]
Version=0.2.1
Name=Q-Paks
Comment=Manage your Flatpak applications
Exec=q-paks
Icon=q-paks
Terminal=false
Type=Application
Categories=Utility;
EOF
```

9. Now, create the tarball by typing:
```bash 
tar czvf q-paks-0.2.1.tar.gz q-paks-0.2.1 
```

10. Move the tarball into your sources directory, which was built earlier:
```bash 
mv q-paks-0.2.1.tar.gz ~/rpmbuild/SOURCES/ 
```

11. Then, create the spec file inside the spec directory by typing:
```bash 
cat <<EOF > ~/rpmbuild/SPECS/q-paks.spec
Name:           q-paks
Version:        0.2.1
Release:        1%{?dist}
Summary:        Q-Paks - Manage your Flatpak applications

License:        GPL-3+
URL:            https://litigated.uk/
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel python3-qt5 qt5-qtbase-devel
Requires:       python3-qt5 flatpak xterm

%description
<<<<<<< HEAD
Q-Paks is a fork of Qubes Apps by Micah F Lee, an application for searching, installing, and managing Flatpak applications.
=======
Q-Paks is a hard fork of Qubes Apps by Micah F Lee, an application for searching, installing, and managing Flatpak applications.
>>>>>>> recovered-files

%prep
%setup -q

%build
# Not much to build in a Python application

%install
mkdir -p %{buildroot}%{_bindir}
install -m 0755 main.py %{buildroot}%{_bindir}/q-paks

mkdir -p %{buildroot}%{_datadir}/applications/
install -m 0644 q-paks.desktop %{buildroot}%{_datadir}/applications/q-paks.desktop

%files
%{_bindir}/q-paks
%{_datadir}/applications/q-paks.desktop

%changelog
* Sun Aug 25 2024 Litigated <contact@litigated.uk> - 9.2-1
- Initial package
EOF
```

12. Build the RPM package:
```bash 
rpmbuild -ba ~/rpmbuild/SPECS/q-paks.spec
```

13. Move your newly built RPM package to into your Fedora 40 Template, AppVM or HVM:
```bash
qvm-move ~/rpmbuild/RPMS/noarch/q-paks-0.2.1-1.fc40.noarch.rpm
```

14. Finally, open the terminal in the template, appvm or hvm, you just copied your q-paks RPM package to and install Q-Paks dependencies:
```bash 
sudo dnf install python3-qt5 flatpak xterm -y
```

15. Install Q-Paks.
```bash
sudo dnf install ~/QubesIncoming/”YOUR DISPOSABLE VM NAME”/noarch/q-paks-0.2.1-1.fc40.noarch.rpm
```

</details>
