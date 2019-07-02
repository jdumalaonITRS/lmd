%define daemon_user monitor
%define daemon_group apache
%define not_systemd (0%{?fedora} && 0%{?fedora} < 18) || (0%{?rhel} && 0%{?rhel} < 7)
%define lmd_path github.com/sni/lmd
%define debug_package %{nil}
%define __arch_install_post %{nil}

Name:		op5-lmd
Version:	%{op5version}
Release:	%{op5release}%{?dist}
Summary:	op5 monitor lmd integration

License:	GPLv3
URL:		http://www.op5.com
Source:		%name-%version.tar.gz
BuildRoot: 	%{_tmppath}/%{name}-%{version}
Prefix: 	/opt/monitor/var

%if %not_systemd
%else
BuildRequires: systemd
BuildRequires: git
%endif
BuildRequires: golang
Requires: op5-naemon
Requires: op5-monitor
Requires: monitor-ninja
Requires: monitor-livestatus

%description
This package configures lmd integration with op5 monitor

%prep
%setup -q

%build

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
mkdir -p %buildroot%prefix/lmd
export GOROOT=/usr/lib/golang
export GOPATH=%buildroot%prefix/lmd
git config --global url.git://github.com/.insteadOf https://github.com/
go get golang.org/x/tools/cmd/goimports
export PATH=$PATH:%buildroot%prefix/lmd/bin
make all
cp -f lmd/lmd %buildroot%prefix/lmd/bin
%if %not_systemd
mkdir -p %buildroot%_sysconfdir/init.d
cp op5build/lmd_initscript %{buildroot}%_sysconfdir/init.d/lmd
%else
mkdir --parents %{buildroot}%{_unitdir}
cp op5build/lmd.service %{buildroot}%{_unitdir}/lmd.service
%endif
touch %buildroot%prefix/lmd/lmd.log
cp -rf op5build/lmd.ini docs README.md Changes LICENSE %buildroot%prefix/lmd/
mkdir -p %buildroot%_sysconfdir/logrotate.d
cp op5build/lmd.logrotate %{buildroot}%_sysconfdir/logrotate.d/lmd

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
%defattr(644,monitor,apache,755)
%attr(755,monitor,apache) %prefix/lmd/bin/lmd
%prefix/lmd
%exclude %prefix/lmd/pkg
%exclude %prefix/lmd/src
%if %not_systemd
%attr(0755,root,root) %_sysconfdir/init.d/lmd
%else
%attr(664, root, root) %{_unitdir}/lmd.service
%endif
%attr(644, root, root) %_sysconfdir/logrotate.d/lmd

%clean
rm -rf %buildroot

%changelog
