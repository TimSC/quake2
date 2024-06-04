from setuptools import setup
from Cython.Build import cythonize

setup(
    name='Quake2',
    ext_modules=cythonize("client/cl_cin_extras.pyx"),
)
