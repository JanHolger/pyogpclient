import setuptools

with open("README.md", "r") as readme:
    long_description = readme.read()
    readme.close()

setuptools.setup(
    name = "pyogpclient",
    version = "0.0.1",
    author = "Jan Bebendorf",
    author_email = "jan@bebendorf.eu",
    description = "Open Game Protocol Client for Python 3",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/JanHolger/pyogpclient",
    packages = setuptools.find_packages(),
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent"
    ],
    python_requires = ">=3.6"
)