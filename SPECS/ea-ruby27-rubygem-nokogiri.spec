# Defining the package namespace
%global ns_name ea
%global ns_dir /opt/cpanel
%global pkg ruby27
%global gem_name nokogiri

%global ruby_version %(/opt/cpanel/ea-ruby27/root/usr/bin/ruby -e 'puts RUBY_VERSION')

# Force Software Collections on
%global _scl_prefix %{ns_dir}
%global scl %{ns_name}-%{pkg}
# HACK: OBS Doesn't support macros in BuildRequires statements, so we have
#       to hard-code it here.
# https://en.opensuse.org/openSUSE:Specfile_guidelines#BuildRequires
%global scl_prefix %{scl}-
%{?scl:%scl_package rubygem-%{gem_name}}

# Doing release_prefix this way for Release allows for OBS-proof versioning, See EA-4590 for more details
%define release_prefix 1

%global gem_name     nokogiri
%global gemdir      %{gem_dir}
%global geminstdir  %{gem_instdir}
%global gemsodir    %{gem_extdir_mri}/lib

# Note for packager:
# Nokogiri 1.4.3.1 gem says that Nokogiri upstream will
# no longer support ruby 1.8.6 after 2010-08-01, so
# it seems that 1.4.3.1 is the last version for F-13 and below.

Summary:    An HTML, XML, SAX, and Reader parser
Name:       %{?scl:%scl_prefix}rubygem-%{gem_name}
Version:    1.11.7
Release:    %{release_prefix}%{?dist}.cpanel
Group:      Development/Languages
License:    MIT
URL:        http://nokogiri.rubyforge.org/nokogiri/
Source0:    https://rubygems.org/gems/%{gem_name}-%{version}.gem

Requires:       %{?scl_prefix}ruby(rubygems)
Requires:       %{?scl_prefix}ruby(release)
%{?scl:Requires:%scl_runtime}

BuildRequires:  libxml2-devel
BuildRequires:  libxslt-devel
BuildRequires:  %{?scl_prefix}ruby(release)
BuildRequires:  %{?scl_prefix}ruby(rubygems)
BuildRequires:  %{?scl_prefix}rubygems-devel
BuildRequires:  %{?scl_prefix}ruby-devel
BuildRequires:  scl-utils
BuildRequires:  scl-utils-build
%{?scl:BuildRequires: %{scl}-runtime}
Provides:       %{?scl_prefix}rubygem(%{gem_name}) = %{version}

# Filter out nokogiri.so
%{?filter_provides_in: %filter_provides_in %{gemsodir}/%{gem_name}/.*\.so$}
%{?filter_setup}

%description
Nokogiri parses and searches XML/HTML very quickly, and also has
correctly implemented CSS3 selector support as well as XPath support.

Nokogiri also features an Hpricot compatibility layer to help ease the change
to using correct CSS and XPath.

%package    doc
Summary:    Documentation for %{name}
Group:      Documentation
Requires:   %{name} = %{version}-%{release}

%description    doc
This package contains documentation for %{name}.

%package    -n %{?scl:%scl_prefix}ruby-%{gem_name}
Summary:    Non-Gem support package for %{gem_name}
Group:      Development/Languages
Requires:   %{name} = %{version}-%{release}

%description    -n %{?scl:%scl_prefix}ruby-%{gem_name}
This package provides non-Gem support for %{gem_name}.

%prep
%setup -q -T -c
%{?scl:scl enable %{scl} - << \EOF}

# Gem repack
TOPDIR=$(pwd)
mkdir tmpunpackdir
pushd tmpunpackdir

gem unpack %{SOURCE0}
cd %{gem_name}-%{version}

gem specification -l --ruby %{SOURCE0} > %{gem_name}.gemspec

# remove bundled external libraries
sed -i \
    -e 's|, "ports/archives/[^"][^"]*"||g' \
    -e 's|, "ports/patches/[^"][^"]*"||g' \
    %{gem_name}.gemspec
# Actually not needed when using system libraries
sed -i -e '\@mini_portile@d' %{gem_name}.gemspec

# Ummm...
env LANG=ja_JP.UTF-8 gem build %{gem_name}.gemspec
mv %{gem_name}-%{version}.gem $TOPDIR

popd
rm -rf tmpunpackdir
%{?scl:EOF}

%build
%{?scl:scl enable %{scl} - << \EOF} \
 \
# 1.6.0 needs this \
export NOKOGIRI_USE_SYSTEM_LIBRARIES=yes \
\
%gem_install \
\
# Remove precompiled Java .jar file \
rm -f ./%{geminstdir}/lib/*.jar \
# For now remove JRuby support \
rm -rf ./%{geminstdir}/ext/java \
%{?scl:EOF} 

%install
%global rubylib  opt/cpanel/ea-ruby27/root/usr/lib64/gems/ruby/
%global rubybase opt/cpanel/ea-ruby27/root/usr/share/ruby/ruby-%{ruby_version}
%global gemsbase opt/cpanel/ea-ruby27/root/usr/share/gems
%global gemsdir  %{gemsbase}/gems
%global gemsmri  %{gemsdir}/nokogiri-%{version}
%global gemsextmri  %{gemsmri}/ext

mkdir -p %{buildroot}/%{gemsbase}
mkdir -p %{buildroot}/%{rubybase}
mkdir -p %{buildroot}/%{rubylib}
mkdir -p %{buildroot}/%{rubybase}/nokogiri
mkdir -p %{buildroot}/opt/cpanel/ea-ruby27/root/usr/lib64/gems/ruby/nokogiri-%{version}

cp -ra ./%{gemsbase}/* %{buildroot}/%{gemsbase}
cp -ra ./%{gemsbase}/gems/nokogiri-%{version} %{buildroot}/%{rubybase}
cp -a ./%{gemsbase}/gems/nokogiri-%{version}/lib/nokogiri.rb %{buildroot}/%{rubybase}
cp -ra ./%{gemsbase}/gems/nokogiri-%{version} %{buildroot}/%{rubylib}
cp -ra ./%{gemsbase}/gems/nokogiri-%{version}/* %{buildroot}/%{rubybase}/nokogiri
cp -a ./%{gemsbase}/gems/nokogiri-%{version}/ext/nokogiri/nokogiri.so %{buildroot}/%{rubybase}/nokogiri

cp -afr ./%{gemsbase}/gems/nokogiri-%{version}/lib/nokogiri/* %{buildroot}/%{rubybase}/nokogiri
cp -a ./opt/cpanel/ea-ruby27/root/usr/lib64/gems/ruby/nokogiri-%{version}/gem.build_complete %{buildroot}/opt/cpanel/ea-ruby27/root/usr/lib64/gems/ruby/nokogiri-%{version}

mkdir -p %{buildroot}%{_bindir}
cp -pa ./%{gemsmri}/bin/* %{buildroot}%{_bindir}

# remove all shebang
for f in $(find %{buildroot}/%{gemsmri} -name \*.rb)
do
    sed -i -e '/^#!/d' $f
    chmod 0644 $f
done

# cleanups
rm -f %{buildroot}/%{gemsmri}/{.autotest,.require_paths,.gemtest,.travis.yml}
rm -f %{buildroot}/%{gemsmri}/appveyor.yml
rm -f %{buildroot}/%{gemsmri}/.cross_rubies
rm -f %{buildroot}/%{gemsmri}/{build_all,dependencies.yml,test_all}
rm -f %{buildroot}/%{gemsmri}/.editorconfig
rm -rf %{buildroot}/%{gemsmri}/suppressions/
rm -rf %{buildroot}/%{gemsmri}/patches/

%files
%defattr(-,root, root,-)
%{_bindir}/%{gem_name}
/%{gemsbase}/gems
%dir    /%{gemsmri}/
/%{gemsbase}/specifications/%{gem_name}-%{version}.gemspec
%exclude /%{gemsbase}/doc
/%{gemsbase}/cache/nokogiri-*.gem
/%{rubybase}/
/%{rubylib}/nokogiri-%{version}

%files  doc
%defattr(-,root,root,-)
/%{gemsbase}/doc

%changelog
* Mon Jun 28 2021 Cory McIntire <cory@cpanel.net> - 1.11.7-1
- EA-9904: Update ea-ruby27-rubygem-nokogiri from v1.11.6 to v1.11.7

* Wed Jun 02 2021 Julian Brown <julian.brown@cpanel.net> - 1.11.6-1
- EA-9817: Update ea-ruby27-rubygem-nokogiri from v1.11.1 to v1.11.6

* Wed Mar 10 2021 Travis Holloway <t.holloway@cpanel.net> - 1.11.1-2
- EA-9607: Update Version to be compatible with tooling

* Thu Feb 25 2021 Cory McIntire <cory@cpanel.net> 1.11.1-1
- EA-9605: Update from v1.10.9 to v1.11.1

* Fri Sep 11 2020 Julian Brown <julian.brown@cpanel.net> 1.10.9-1
- ZC-7541 - Initial build

