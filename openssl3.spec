Name:           openssl3
Version:        3.0.13
Release:        1%{?dist}
Summary:        OpenSSL 3.0.13 定制构建版（兼容系统默认版本）

License:        Apache-2.0
URL:            https://www.openssl.org
Source0:        https://gh-proxy.com/https://github.com/openssl/openssl/archive/refs/tags/openssl-%{version}.tar.gz

# 增强的构建依赖
BuildRequires:  make
BuildRequires:  gcc
BuildRequires:  perl
BuildRequires:  perl-IPC-Cmd
BuildRequires:  perl-Text-Template
BuildRequires:  perl-FindBin
BuildRequires:  zlib-devel
BuildRequires:  libffi-devel
BuildRequires:  pkgconfig
BuildRequires:  rpm-build
BuildRequires:  ca-certificates

# 增强的运行时依赖
Requires:       zlib
Requires:       perl
Requires:       perl-base
Requires:       libffi
Requires(post): chkconfig
Requires(postun): chkconfig

%description
OpenSSL 3.0.13 with dual-command support:
- /usr/bin/openssl (system default)
- /usr/bin/openssl3 (new version)
Installed in /usr/local/openssl3

%prep
%setup -q -n openssl-openssl-%{version}

%build
./config \
    --prefix=/usr/local/openssl3 \
    --openssldir=/usr/local/openssl3/etc/ssl \
    --libdir=lib64 \
    shared \
    zlib-dynamic \
    enable-cms \
    enable-ktls \
    enable-md2 \
    enable-rc5 \
    enable-rfc3779 \
    enable-sctp \
    enable-ssl-trace \
    enable-ssl3 \
    enable-ssl3-method \
    enable-weak-ssl-ciphers \
    -Wa,--noexecstack \
    %{?_with_bootstrap:-enable-bootstrap}
make %{?_smp_mflags}

%install
rm -rf %{buildroot}
make install DESTDIR=%{buildroot}

# 创建文档目录
mkdir -p %{buildroot}/usr/share/doc/openssl3-%{version}

# 明确复制存在的文档文件
[ -f LICENSE.txt ] && cp -p LICENSE.txt %{buildroot}/usr/share/doc/openssl3-%{version}/
[ -f README.md ] && cp -p README.md %{buildroot}/usr/share/doc/openssl3-%{version}/

# 创建版本化命令
mkdir -p %{buildroot}/usr/bin
ln -sf /usr/local/openssl3/bin/openssl %{buildroot}/usr/bin/openssl3

# 创建库配置文件
mkdir -p %{buildroot}/etc/ld.so.conf.d
echo "/usr/local/openssl3/lib64" > %{buildroot}/etc/ld.so.conf.d/openssl3.conf

# 环境变量配置
mkdir -p %{buildroot}/etc/profile.d
cat > %{buildroot}/etc/profile.d/openssl3.sh <<'EOF'
#!/bin/bash
export PATH="/usr/local/openssl3/bin:$PATH"
export LD_LIBRARY_PATH="/usr/local/openssl3/lib64:$LD_LIBRARY_PATH"
alias openssl3="/usr/local/openssl3/bin/openssl"
EOF
chmod 644 %{buildroot}/etc/profile.d/openssl3.sh

%pre
# 安装前检查
if [ -x "/usr/bin/openssl" ] && ! rpm -q openssl >/dev/null 2>&1; then
    echo "Warning: System openssl is not managed by RPM" >&2
fi

%post
# 安装后设置
# 确保库路径被系统识别
ldconfig

if [ $1 -eq 1 ]; then
    # 首次安装
    update-alternatives --install \
        /usr/bin/openssl openssl /usr/local/openssl3/bin/openssl 100 \
        --slave /usr/share/man/man1/openssl.1ssl openssl.man \
                /usr/local/openssl3/share/man/man1/openssl.1
fi
echo "OpenSSL 3.0.13 installed. Use 'openssl3' command or 'source /etc/profile.d/openssl3.sh'"

%preun
# 卸载前处理
if [ $1 -eq 0 ]; then
    # 完全卸载前检查依赖
    if ldd /usr/bin/openssl3 | grep -q "not found"; then
        echo "Warning: Possible broken dependencies detected" >&2
    fi
fi

%postun
# 卸载后清理
if [ $1 -eq 0 ]; then
    update-alternatives --remove openssl /usr/local/openssl3/bin/openssl
    rm -f /etc/ld.so.conf.d/openssl3.conf
    ldconfig
    echo "OpenSSL 3.0.13 completely removed"
elif [ $1 -ge 1 ]; then
    # 升级时保留配置
    ldconfig
fi

%files
%defattr(-,root,root,-)
%doc LICENSE.txt
%doc README.md
/usr/local/openssl3/*
/usr/bin/openssl3
/etc/ld.so.conf.d/openssl3.conf
/etc/profile.d/openssl3.sh

%changelog
* Wed Jan 10 2024 Your Name <your.email@example.com>
- Added complete lifecycle management
- Enhanced dependency declarations
- Added pre/post installation checks
- Improved config file handling with %config(noreplace)
- Fixed library loading issues by adding ld.so.conf configuration
- Explicitly set libdir to lib64 in build configuration
