try:
    import setuptools
    from setuptools import setup, Extension
except:
    from distutils.core import setup
    from distutils.extension import Extension
import numpy as np
from Cython.Distutils import build_ext
import re
import os, sys

## If you do not wish to use findblas:
## -uncomment the SciPy imports in 'wrapper_untyped.pxi'
##  (or manually add linkage to another blas/lapack implementation
##   in this setup file)
## -comment out the line that imports 'build_ext_with_blas'
## -uncomment the next line
# from Cython.Distutils import build_ext as build_ext_with_blas

## Or alternatively, pass your own BLAS/LAPACK linkage parameters here:
custom_blas_link_args = []
custom_blas_compile_args = []
# example:
# custom_blas_link_args = ["-lopenblas"]
if len(custom_blas_link_args) or len(custom_blas_compile_args):
    build_ext_with_blas = build_ext

if not (len(custom_blas_link_args) or len(custom_blas_compile_args)):
    use_findblas = (("findblas" in sys.argv)
                     or ("-findblas" in sys.argv)
                     or ("--findblas" in sys.argv))
    if os.environ.get('USE_FINDBLAS') is not None:
        use_findblas = True
    if use_findblas:
        sys.argv = [a for a in sys.argv if a not in ("findblas", "-findblas", "--findblas")]
        from findblas.distutils import build_ext_with_blas
    else:
        build_ext_with_blas = build_ext

class build_ext_subclass( build_ext_with_blas ):
    def build_extensions(self):
        compiler = self.compiler.compiler_type
        if compiler == 'msvc': # visual studio
            for e in self.extensions:
                e.extra_compile_args += ['/O2', '/openmp']
        else: # everything else that cares about following standards
            for e in self.extensions:
                e.extra_compile_args += ['-O3', '-fopenmp', '-march=native', '-std=c99']
                e.extra_link_args += ['-fopenmp']
                
                # e.extra_compile_args += ['-O2', '-fopenmp', '-march=native', '-std=c99', '-ggdb']
                # e.extra_link_args += ['-fopenmp']
                # e.extra_link_args += ['-fopenmp=libiomp5']

                # e.extra_compile_args += ['-O2', '-march=native', '-std=c99', '-ggdb']
                

                # e.extra_compile_args += ['-fsanitize=address', '-static-libasan', '-ggdb']
                # e.extra_link_args += ['-fsanitize=address', '-static-libasan']                

        ## Note: apple will by default alias 'gcc' to 'clang', and will ship its own "special"
        ## 'clang' which has no OMP support and nowadays will purposefully fail to compile when passed
        ## '-fopenmp' flags. If you are using mac, and have an OMP-capable compiler,
        ## comment out the code below, or set 'use_omp' to 'True'.
        if not use_omp:
            for e in self.extensions:
                e.extra_compile_args = [arg for arg in e.extra_compile_args if arg != '-fopenmp']
                e.extra_link_args    = [arg for arg in e.extra_link_args    if arg != '-fopenmp']

        ## If a custom BLAS/LAPACK is provided:
        if len(custom_blas_link_args) or len(custom_blas_compile_args):
            for e in self.extensions:
                e.extra_compile_args += custom_blas_compile_args
                e.extra_link_args += custom_blas_link_args
                e.define_macros = [m for m in e.define_macros if m[0] != "USE_FINDBLAS"]

        ## SYR in OpenBLAS is currently 10-15x slower than MKL, avoid it:
        ## https://github.com/xianyi/OpenBLAS/issues/3237
        for e in self.extensions:
            has_openblas_or_atlas = False
            if not has_openblas_or_atlas:
                for arg in e.extra_compile_args:
                    if (bool(re.search("openblas", str(arg).lower()))
                        or bool(re.search("atlas", str(arg).lower()))
                    ):
                        has_openblas_or_atlas = True
                        break
            if not has_openblas_or_atlas:
                for arg in e.extra_link_args:
                    if (bool(re.search("openblas", str(arg).lower()))
                        or bool(re.search("atlas", str(arg).lower()))
                    ):
                        has_openblas_or_atlas = True
                        break
            if not has_openblas_or_atlas:
                for arg in e.define_macros:
                    if (bool(re.search("openblas", str(arg[0]).lower()))
                        or bool(re.search("atlas", str(arg[0]).lower()))
                    ):
                        has_openblas_or_atlas = True
                        break
            if has_openblas_or_atlas:
                if "AVOID_BLAS_SYR" not in [m[0] for m in e.define_macros]:
                    e.define_macros += [("AVOID_BLAS_SYR", None)]
                e.define_macros = [macro for macro in e.define_macros if macro[0] != "USE_BLAS_SYR"]

        build_ext_with_blas.build_extensions(self)


use_omp = (("enable-omp" in sys.argv)
           or ("-enable-omp" in sys.argv)
           or ("--enable-omp" in sys.argv))
if use_omp:
    sys.argv = [a for a in sys.argv if a not in ("enable-omp", "-enable-omp", "--enable-omp")]
if os.environ.get('ENABLE_OMP') is not None:
    use_omp = True
if sys.platform[:3] != "dar":
    use_omp = True

### Shorthand for apple computer:
### uncomment line below
# use_omp = True


force_openblas = (("openblas" in sys.argv)
                  or ("-openblas" in sys.argv)
                  or ("--openblas" in sys.argv))
if force_openblas:
    sys.argv = [a for a in sys.argv if a not in ("openblas", "-openblas", "--openblas")]
if os.environ.get('USE_OPENBLAS') is not None:
    force_openblas = True
if (force_openblas):
    custom_blas_link_args = ["-lopenblas"]
    from Cython.Distutils import build_ext
    build_ext_with_blas = build_ext

setup(
    name  = "cmfrec",
    packages = ["cmfrec"],
    version = '3.1.2-2',
    description = 'Collective matrix factorization',
    author = 'David Cortes',
    author_email = 'david.cortes.rivera@gmail.com',
    url = 'https://github.com/david-cortes/cmfrec',
    keywords = ['collaborative filtering', 'collective matrix factorization',
                'relational learning'],
    install_requires=[
        'cython',
        'numpy>=1.17',
        'scipy',
        'pandas>=0.25.0',
        'findblas'
    ],
    cmdclass = {'build_ext': build_ext_subclass},
    ext_modules = [
        Extension("cmfrec.wrapper_double",
            sources=["cmfrec/cfuns_double.pyx" if use_findblas else "cmfrec/cfuns_double_plusblas.pyx",
                     "src/collective.c", "src/common.c",
                     "src/offsets.c", "src/helpers.c", "src/lbfgs.c",
                     "src/cblas_wrappers.c"],
            include_dirs=[np.get_include(), "src"],
            define_macros = [("_FOR_PYTHON", None),
                             ("USE_DOUBLE", None),
                             ("USE_FINDBLAS" if use_findblas else "NO_FINDBLAS", None),
                             ("USE_BLAS_SYR" if use_findblas else "AVOID_BLAS_SYR", None)]
            ),
        Extension("cmfrec.wrapper_float",
            sources=["cmfrec/cfuns_float.pyx" if use_findblas else "cmfrec/cfuns_float_plusblas.pyx",
                     "src/collective.c", "src/common.c",
                     "src/offsets.c", "src/helpers.c", "src/lbfgs.c",
                     "src/cblas_wrappers.c"],
            include_dirs=[np.get_include(), "src"],
            define_macros = [("_FOR_PYTHON", None),
                             ("USE_FLOAT", None),
                             ("USE_FINDBLAS" if use_findblas else "NO_FINDBLAS", None),
                             ("USE_BLAS_SYR" if use_findblas else "AVOID_BLAS_SYR", None)]
            ),
        ]
)

if not use_omp:
    import warnings
    apple_msg  = "\n\n\nMacOS detected. Package will be built without multi-threading capabilities, "
    apple_msg += "due to Apple's lack of OpenMP support in default clang installs. In order to enable it, "
    apple_msg += "reinstall with an environment variable 'export ENABLE_OMP=1' or install from GitHub. "
    apple_msg += "You'll also need an OpenMP-capable compiler.\n\n\n"
    warnings.warn(apple_msg)
