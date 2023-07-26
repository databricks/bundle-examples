from setuptools import setup, find_packages

import lib

setup(
    name="lib",
    version=lib.__version__,
    author=lib.__author__,
    url="https://databricks.com",
    author_email="john.doe@databricks.com",
    description="my lib wheel",
    packages=find_packages(include=["lib"]),
    install_requires=["setuptools"],
)
