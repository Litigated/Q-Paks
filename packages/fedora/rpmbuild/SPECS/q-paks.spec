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
Q-Paks is a fork of Qubes Apps by Micah F Lee, an application for searching, installing, and managing Flatpak applications.

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
