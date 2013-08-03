Name:		openblas
Version:	0.2.7
Release:	2%{?dist}
Summary:	An optimized BLAS library based on GotoBLAS2
Group:		Development/Libraries
License:	BSD
URL:		https://github.com/xianyi/OpenBLAS/
Source0:	https://github.com/xianyi/OpenBLAS/archive/v%{version}.tar.gz
# Use system lapack
Patch0:		openblas-0.2.7-system_lapack.patch
# Drop extra p from threaded library name
Patch1:		openblas-0.2.5-libname.patch
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildRequires:	gcc-gfortran
# For execstack
BuildRequires:	prelink
# LAPACK
%if 0%{?rhel} == 5 || 0%{?rhel} == 6
BuildRequires:	lapack-devel%{?_isa}
%else
BuildRequires:	lapack-static%{?_isa}
%endif

# Compability for old versions of GCC
%if 0%{?rhel} == 5
%global avxflag NO_AVX=1
%endif

# Do we have LAPACKE? (Needs at least lapack 3.4.0)
%if 0%{?fedora} > 16
%global lapacke 1
%else
%global lapacke 0
%endif

# Upstream supports the package only on these architectures.
# Runtime processor detection is not available on other archs.
ExclusiveArch:	x86_64 %{ix86}

%global base_description \
OpenBLAS is an optimized BLAS library based on GotoBLAS2 1.13 BSD \
version. The project is supported by the Lab of Parallel Software and \
Computational Science, ISCAS. http://www.rdcps.ac.cn


%description
%{base_description}

%package openmp
Summary:	An optimized BLAS library based on GotoBLAS2, OpenMP version
Group:		Development/Libraries


%description openmp
%{base_description}

This package contains the library compiled with OpenMP support.

%package threads
Summary:	An optimized BLAS library based on GotoBLAS2, pthreads version
Group:		Development/Libraries

%description threads
%{base_description}

This package contains the library compiled with threading support.

%package devel
Summary:	Development headers and libraries for OpenBLAS
Group:		Development/Libraries
Requires:	%{name}%{?_isa} = %{version}-%{release}
Requires:	%{name}-openmp%{?_isa} = %{version}-%{release}
Requires:	%{name}-threads%{?_isa} = %{version}-%{release}

%description devel
%{base_description}

This package contains the development headers and libraries.

%package static
Summary:	Static version of OpenBLAS
Group:		Development/Libraries
Requires:	%{name}-devel%{?_isa} = %{version}-%{release}

%description static
%{base_description}

This package contains the static libraries.

%prep
%setup -q -c -T

# Untar source
tar zxf %{SOURCE0}
cd OpenBLAS-%{version}
%patch0 -p1 -b .system_lapack
%patch1 -p1 -b .libname

# Get rid of bundled LAPACK sources
rm -rf lapack-netlib

# Setup LAPACK
mkdir netliblapack
cd netliblapack
ar x %{_libdir}/liblapack_pic.a
# Get rid of duplicate functions. See list in Makefile of lapack directory
for f in laswp getf2 getrf potf2 potrf lauu2 lauum trti2 trtri getrs; do
    \rm {c,d,s,z}$f.o
done

# LAPACKE
%if %{lapacke}
ar x %{_libdir}/liblapacke.a
%endif

# Create makefile
echo "TOPDIR = .." > Makefile
echo "include ../Makefile.system" >> Makefile
echo "COMMONOBJS = \\" >> Makefile
for i in *.o; do
 echo "$i \\" >> Makefile
done
echo -e "\n\ninclude \$(TOPDIR)/Makefile.tail" >> Makefile

%if %{lapacke}
# Copy include files
cp -a %{_includedir}/lapacke .
%endif
cd ..

# Make serial, threaded and OpenMP versions
cd ..
cp -ar OpenBLAS-%{version} openmp
cp -ar OpenBLAS-%{version} threaded
mv OpenBLAS-%{version} serial

%build
%if %{lapacke}
LAPACKE="NO_LAPACKE=0"
%else
LAPACKE="NO_LAPACKE=1"
%endif

make -C serial TARGET=CORE2 DYNAMIC_ARCH=1 USE_THREAD=0 USE_OPENMP=0 FC=gfortran CC=gcc COMMON_OPT="%{optflags}" NUM_THREADS=32 %{?avxflag} $LAPACKE
make -C threaded TARGET=CORE2 DYNAMIC_ARCH=1 USE_THREAD=1 USE_OPENMP=0 FC=gfortran CC=gcc COMMON_OPT="%{optflags}" NUM_THREADS=32 LIBPREFIX="libopenblasp" %{?avxflag} $LAPACKE
# USE_THREAD determines use of SMP, not of pthreads
make -C openmp TARGET=CORE2 DYNAMIC_ARCH=1 USE_THREAD=1 USE_OPENMP=1 FC=gfortran CC=gcc COMMON_OPT="%{optflags}" NUM_THREADS=32 LIBPREFIX="libopenblaso" %{?avxflag} $LAPACKE


%install
rm -rf %{buildroot}
# Install serial library and headers
make -C serial USE_THREAD=0 PREFIX=%{buildroot}%{_usr} install

# Move include files to package specific directory, so that they don't clash with reference BLAS and LAPACK
mkdir %{buildroot}%{_includedir}/%{name}
mv %{buildroot}%{_includedir}/*.h %{buildroot}%{_includedir}/%{name}

# Copy lapacke include files
%if %{lapacke}
cp -a %{_includedir}/lapacke %{buildroot}%{_includedir}/%{name}
%endif

# Put libraries in correct location
if [ %_lib != lib ]; then
 mkdir -p %{buildroot}%{_libdir}
 mv %{buildroot}/usr/lib/libopen* %{buildroot}%{_libdir}
fi

# Fix name of static library
slibname=`basename %{buildroot}%{_libdir}/libopenblas-*.so .so`
mv %{buildroot}%{_libdir}/${slibname}.a %{buildroot}%{_libdir}/lib%{name}.a

# Install the OpenMP library
olibname=`echo ${slibname} | sed "s|lib%{name}|lib%{name}o|g"`
install -D -p -m 755 openmp/${olibname}.so %{buildroot}%{_libdir}/${olibname}.so
install -D -p -m 644 openmp/${olibname}.a %{buildroot}%{_libdir}/lib%{name}o.a

# Install the threaded library
plibname=`echo ${slibname} | sed "s|lib%{name}|lib%{name}p|g"`
install -D -p -m 755 threaded/${plibname}.so %{buildroot}%{_libdir}/${plibname}.so
install -D -p -m 644 threaded/${plibname}.a %{buildroot}%{_libdir}/lib%{name}p.a

# Fix source permissions (also applies to LAPACK)
find -name \*.f -exec chmod 644 {} \;

# Fix symlinks
pushd %{buildroot}%{_libdir}
# Serial libraries
ln -sf ${slibname}.so lib%{name}.so
ln -sf ${slibname}.so lib%{name}.so.0
# OpenMP libraries
ln -sf ${olibname}.so lib%{name}o.so
ln -sf ${olibname}.so lib%{name}o.so.0
# Threaded libraries
ln -sf ${plibname}.so lib%{name}p.so
ln -sf ${plibname}.so lib%{name}p.so.0

# Get rid of executable stacks
for lib in %{buildroot}%{_libdir}/libopenblas{,o,p}-*.so; do
 execstack -c $lib
done

%post -p /sbin/ldconfig
%postun -p /sbin/ldconfig

%post openmp -p /sbin/ldconfig
%postun openmp -p /sbin/ldconfig

%post threads -p /sbin/ldconfig
%postun threads -p /sbin/ldconfig

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
%doc serial/Changelog.txt serial/GotoBLAS* serial/LICENSE
%{_libdir}/lib%{name}-*.so
%{_libdir}/lib%{name}.so.*

%files openmp
%defattr(-,root,root,-)
%{_libdir}/lib%{name}o-*.so
%{_libdir}/lib%{name}o.so.*

%files threads
%defattr(-,root,root,-)
%{_libdir}/lib%{name}p-*.so
%{_libdir}/lib%{name}p.so.*

%files devel
%defattr(-,root,root,-)
%{_libdir}/lib%{name}.so
%{_libdir}/lib%{name}o.so
%{_libdir}/lib%{name}p.so
%{_includedir}/%{name}/

%files static
%defattr(-,root,root,-)
%{_libdir}/lib%{name}.a
%{_libdir}/lib%{name}o.a
%{_libdir}/lib%{name}p.a

%changelog
* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2.7-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Tue Jul 23 2013 Susi Lehtola <jussilehtola@fedoraproject.org> - 0.2.7-1
- Update to 0.2.7.
- Use OpenBLAS versions of LAPACK functions, as they seem to be
  working now.

* Mon Jul 08 2013 Susi Lehtola <jussilehtola@fedoraproject.org> - 0.2.5-10
- Due to long standing bug, replace all OpenBLAS LAPACK functions with
  generic ones, so that package can finally be released in stable.

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2.5-9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Tue Jan 15 2013 Susi Lehtola <jussilehtola@fedoraproject.org> - 0.2.5-8
- Added LAPACKE include files.

* Mon Jan 14 2013 Susi Lehtola <jussilehtola@fedoraproject.org> - 0.2.5-7
- Fix build on RHEL5 and ppc architecture.

* Mon Dec 24 2012 Susi Lehtola <jussilehtola@fedoraproject.org> - 0.2.5-6
- Review fixes.

* Fri Dec 21 2012 Susi Lehtola <jussilehtola@fedoraproject.org> - 0.2.5-5
- Disable LAPACKE support on distributions where it is not available due to
  a too old version of lapack.

* Mon Dec 17 2012 Susi Lehtola <jussilehtola@fedoraproject.org> - 0.2.5-4
- Don't use reference LAPACK functions that have optimized implementation.

* Wed Dec 12 2012 Susi Lehtola <jussilehtola@fedoraproject.org> - 0.2.5-3
- Use system version of LAPACK.

* Mon Nov 26 2012 Susi Lehtola <jussilehtola@fedoraproject.org> - 0.2.5-2
- Fixed 32-bit build, and build on EPEL 5.

* Mon Nov 26 2012 Susi Lehtola <jussilehtola@fedoraproject.org> - 0.2.5-1
- Update to 0.2.5.

* Thu Oct 06 2011 Jussi Lehtola <jussilehtola@fedoraproject.org> - 0.1-2.alpha2.4
- Added documentation.

* Sun Sep 18 2011 Jussi Lehtola <jussilehtola@fedoraproject.org> - 0.1-1.alpha2.4
- First release.
