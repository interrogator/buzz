import os

from setuptools import setup


def read(fname):
    """
    Helper to read README
    """
    return open(os.path.join(os.path.dirname(__file__), fname)).read().strip()


setup(
    name="buzz",
    version="2.0.2",  # DO NOT EDIT THIS LINE MANUALLY. LET bump2version UTILITY DO IT
    description="Sophisticated corpus linguistics",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    url="http://github.com/interrogator/buzz",
    author="Daniel McDonald",
    include_package_data=True,
    zip_safe=False,
    packages=["buzz"],
    scripts=["buzz/parse"],
    author_email="mcddjx@gmail.com",
    license="MIT",
    keywords=["corpus", "linguistics", "nlp"],
    install_requires=[
        "nltk",
        "bllipparser",
        "scipy",
        "cython",
        "depgrep",
        "scikit-learn",
        # 'benepar',
        # 'benepar[cpu]',
        "tensorflow>=1.12.1",
        "setuptools>=41.0.0",
        "spacy",
        "pandas",
        "tqdm",
        "pyparsing",
        "tabview",
        "isort",
    ],
    dependency_links=["https://github.com/interrogator/tabview/archive/master.zip"],
)
