%define not_systemd (0%{?fedora} && 0%{?fedora} < 18) || (0%{?rhel} && 0%{?rhel} < 7)
%global debug_package %{nil}
%global golang_version 1.15.6

Name:		op5-lmd
Version:	%{op5version}
Release:	%{op5release}%{?dist}
Summary:	OP5 monitor lmd integration
License:	GPLv3
URL:		http://www.op5.com
Source:		%name-%version.tar.gz
BuildRoot:	%{_tmppath}/%{name}-%{version}

%if %not_systemd
%else
BuildRequires: systemd
BuildRequires: git
%endif
Requires: op5-naemon
Requires: monitor-livestatus

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

%build
# LMD requires Golang 1.14, which is not yet in EPEL
# We manually download it for now
curl -o go%{golang_version}.linux-amd64.tar.gz https://dl.google.com/go/go%{golang_version}.linux-amd64.tar.gz
tar -xf go%{golang_version}.linux-amd64.tar.gz -C $HOME/
# make sure the default golang bin is in our path
export PATH=$PATH:$HOME/go/bin/
make debugbuild BUILD=OP5-%{version}-debug
mv lmd/lmd lmd/lmd_debugbuild
make all BUILD=OP5-%{version}-release

%pre
%if %not_systemd
service lmd stop >/dev/null 2>&1 || :
%else
systemctl stop lmd >/dev/null 2>&1 || :
if chkconfig --list lmd &>/dev/null; then
	chkconfig --del lmd
fi
%endif

%install
rm -rf %buildroot
# copy LMD binary to /usr/bin/
mkdir -p %buildroot/%_bindir/
cp -f lmd/lmd %buildroot/%_bindir/
cp -f lmd/lmd_debugbuild %buildroot/%_bindir/

# config file
mkdir -p %buildroot%_sysconfdir/op5/lmd/
cp -rf op5build/lmd.ini %buildroot%_sysconfdir/op5/lmd/

# service/init files
%if %not_systemd
	mkdir -p %buildroot%_sysconfdir/init.d
	cp op5build/lmd_initscript %{buildroot}%_sysconfdir/init.d/lmd
%else
	mkdir --parents %{buildroot}%{_unitdir}
	cp op5build/lmd.service %{buildroot}%{_unitdir}/lmd.service
	cp op5build/lmd-debug.service %{buildroot}%{_unitdir}/lmd-debug.service
%endif

# logrotation
mkdir -p %buildroot%_sysconfdir/logrotate.d
cp op5build/op5-lmd.logrotate %{buildroot}%_sysconfdir/logrotate.d/op5-lmd

# Make sure the log file exists
mkdir --parents --mode 775 %buildroot/var/log/op5
touch %buildroot/var/log/op5/lmd.log

%post
sed -i -e "s/\/rw\/live$/\/rw\/live_tmp/g" /opt/monitor/etc/mconf/livestatus.cfg
%if %not_systemd
service naemon restart || :
/sbin/chkconfig --add lmd || :
service lmd restart || :
%else
systemctl restart naemon
systemctl daemon-reload
systemctl enable lmd.service
systemctl restart lmd
%endif

%post debug
systemctl stop lmd
mv %_unitdir/lmd.service %_unitdir/lmd-release.service
ln -s %_unitdir/lmd-debug.service %_unitdir/lmd.service
systemctl daemon-reload
systemctl start lmd

%preun debug
# Only run when deleting the package completly, not when updating
if [ "$1" -eq 0 ] ; then
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
if [ "$1" -eq 0 ]; then
sed -i -e "s/\/rw\/live_tmp$/\/rw\/live/g" /opt/monitor/etc/mconf/livestatus.cfg
%if %not_systemd
	service lmd stop || :
	/sbin/chkconfig --del lmd || :
	service naemon restart || :
%else
	systemctl stop lmd || :
	systemctl disable lmd.service
	systemctl daemon-reload
	systemctl restart naemon || :
%endif
fi

%files
%attr(755,root,root) %_bindir/lmd
%attr(644,monitor,apache) %config(noreplace) %_sysconfdir/op5/lmd/lmd.ini
%if %not_systemd
%attr(0755,root,root) %_sysconfdir/init.d/lmd
%else
%attr(664,root,root) %{_unitdir}/lmd.service
%endif
%attr(644,root,root) %config(noreplace) %_sysconfdir/logrotate.d/op5-lmd
%license LICENSE
%doc README.md
%dir %attr(775,monitor,apache) /var/log/op5
%attr(644,monitor,apache) %ghost /var/log/op5/lmd.log

%files debug
%attr(755,root,root) %_bindir/lmd_debugbuild
%attr(664,root,root) %{_unitdir}/lmd-debug.service

%clean
rm -rf %buildroot

%changelog
* Wed Sep 25 2019 Jacob Hansen <jhansen@op5.com> - 2019.i
- Make sure the log file is being created.
* Tue Jul 2 2019 Jacob Hansen <jhansen@op5.com> - 2019.g
- Specfile rewrite and use best-practice system paths.
