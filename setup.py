import re
from setuptools import setup, find_packages

version = re.search(
    r'^__VERSION__\s*=\s*"(.*)"', open("curvequery/__init__.py").read(), re.M
).group(1)

setup(
    name="curvequery",
    version=version,
    packages=find_packages(),
    author="Chadwick Stryker",
    author_email="chad.stryker@tektronix.com",
    url="TBD",
    install_requires=["pyvisa==1.9.1"],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.7",
    ],
)
