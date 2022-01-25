%global debug_package %{nil}
%global golang_version 1.16.13

Name:		op5-lmd
Version:	%{op5version}
Release:	%{op5release}%{?dist}
Summary:	OP5 monitor lmd integration
License:	GPLv3
URL:		https://www.itrsgroup.com
Source:		%name-%version.tar.gz
Patch0:		op5build/Makefile.patch
BuildRoot:	%{_tmppath}/%{name}-%{version}

BuildRequires: git
Requires: op5-naemon
Requires: monitor-livestatus
%systemd_requires

%description
This package configures lmd integration with OP5 monitor

%package debug
Summary: OP5 monitor lmd integration (debug)
Requires: op5-naemon
Requires: monitor-livestatus
Requires: op5-lmd

%description debug
Build with debug symbols for the lmd integration in OP5 Monitor

%prep
%setup -q
# Patch Makefile to skip downloading dependencies, they were downloaded pre-build.
%patch0 -p1

%build
# LMD requires Golang > 1.16, which is not yet in EPEL
# We manually download it for now
curl -o go%{golang_version}.linux-amd64.tar.gz https://dl.google.com/go/go%{golang_version}.linux-amd64.tar.gz
tar -xf go%{golang_version}.linux-amd64.tar.gz -C $HOME/
# make sure the default golang bin is in our path
export PATH=$PATH:$HOME/go/bin/
export GOPROXY=off
make debugbuild BUILD=OP5-%{version}-debug
mv lmd/lmd lmd/lmd_debugbuild
make build BUILD=OP5-%{version}-release


%install
%{__install} -D lmd/lmd %{buildroot}/%{_bindir}/lmd
%{__install} -D lmd/lmd_debugbuild %{buildroot}/%{_bindir}/lmd_debugbuild
%{__install} -D -m 644 op5build/lmd.ini %{buildroot}%{_sysconfdir}/op5/lmd/lmd.ini
%{__install} -D -m 644 op5build/lmd.service %{buildroot}%{_unitdir}/lmd.service
%{__install} -D -m 644 op5build/lmd-debug.service %{buildroot}%{_unitdir}/lmd-debug.service
%{__install} -D -m 644 op5build/op5-lmd.logrotate %{buildroot}%{_sysconfdir}/logrotate.d/op5-lmd

# Make sure the log file exists
mkdir --parents --mode 775 %buildroot/var/log/op5
touch %buildroot/var/log/op5/lmd.log


%post
sed -i -e "s/\/rw\/live$/\/rw\/live_tmp/g" /opt/monitor/etc/mconf/livestatus.cfg
systemctl restart naemon
systemctl daemon-reload
systemctl enable lmd.service
systemctl restart lmd


%post debug
systemctl stop lmd
mv %_unitdir/lmd.service %_unitdir/lmd-release.service
ln -s %_unitdir/lmd-debug.service %_unitdir/lmd.service
systemctl daemon-reload
systemctl start lmd


%preun debug
# Only run when deleting the package completly, not when updating
if [ $1 -eq 0 ] ; then
	systemctl stop lmd
	# make sure we are acually using the debug version by verifying the lmd.service
	# file is a symlink.
	if [ -L %_unitdir/lmd.service ]; then
		rm -f %_unitdir/lmd.service
		mv %_unitdir/lmd-release.service %_unitdir/lmd.service
	fi
	systemctl daemon-reload
	systemctl start lmd
fi

%preun
%systemd_preun lmd.service

# Uninstall
if [ $1 -eq 0 ]; then
	sed -i -e "s/\/rw\/live_tmp$/\/rw\/live/g" /opt/monitor/etc/mconf/livestatus.cfg
	systemctl try-restart naemon.service >/dev/null 2>&1 || :
fi

%postun
%systemd_postun dummy-for-rpmlint


%files
%_bindir/lmd
%attr(-,monitor,apache) %config(noreplace) %_sysconfdir/op5/lmd/lmd.ini
%{_unitdir}/lmd.service
%config(noreplace) %_sysconfdir/logrotate.d/op5-lmd
%license LICENSE
%doc README.md
%dir %attr(775,monitor,apache) /var/log/op5
%ghost /var/log/op5/lmd.log


%files debug
%attr(755,root,root) %_bindir/lmd_debugbuild
%attr(664,root,root) %{_unitdir}/lmd-debug.service

%clean
rm -rf %buildroot

%changelog
* Tue Jan 25 2022 Jacob Hansen <jhansen@itrsgroup.com> - 2022.2
- Install go manually as LMD > 2.0.4 requires go 1.16 (not in EPEL yet).
* Fri Feb 12 2021 Aksel Sjögren <asjogren@itrsgroup.com> - 2021.3
- Remove EL6 and pre-systemd support.
- Use golang from OS repos when building package.
- Use pre-downloaded dependencies.
* Wed Sep 25 2019 Jacob Hansen <jhansen@op5.com> - 2019.i
- Make sure the log file is being created.
* Tue Jul 2 2019 Jacob Hansen <jhansen@op5.com> - 2019.g
- Specfile rewrite and use best-practice system paths.
