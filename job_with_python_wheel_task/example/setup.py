from setuptools import setup, find_packages

import src

setup(
    name="example",
    version=src.__version__,
    author=src.__author__,
    url="https://databricks.com",
    author_email="john.doe@databricks.com",
    description="my example wheel",
    packages=find_packages(include=["src"]),
    entry_points={"group_1": "run=src.__main__:main"},
    install_requires=["setuptools"],
)
