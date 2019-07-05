# -*- coding: utf-8 -*-
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="beryllium",
    version="1.0.3",
    author="mannuan",
    author_email="1271990125@qq.com",
    description="A framework for spider over selenium",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mannuan/beryllium",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "selenium>=3.14.0",
        "PyVirtualDisplay>=0.2.1",
        "pymongo>=3.7.1",
        "PyMySQL>=0.9.2",
    ],
)
