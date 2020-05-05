import os

from setuptools import setup


def read(fname):
    """
    Helper to read README
    """
    return open(os.path.join(os.path.dirname(__file__), fname)).read().strip()


setup(
    name="buzz",
    version="3.1.2",  # DO NOT EDIT THIS LINE MANUALLY. LET bump2version UTILITY DO IT
    description="Sophisticated corpus linguistics",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    url="http://github.com/interrogator/buzz",
    author="Daniel McDonald",
    include_package_data=True,
    zip_safe=False,
    packages=["buzz"],
    scripts=["bin/parse"],
    extras_require={
        "word": [
            "buzzword>=0.1.0",
            "dash==1.1.1",
            "flask==1.1.1",
            "dash-core-components==1.1.1",
            "dash-html-components==1.0.0",
            "dash-renderer==1.0.0",
            "dash-table==4.1.0",
            "dash-daq==0.1.7",
        ]
    },
    author_email="mcddjx@gmail.com",
    license="MIT",
    keywords=["corpus", "linguistics", "nlp"],
    install_requires=[
        "nltk",
        "benepar @ git+https://github.com/interrogator/self-attentive-parser",
        "en-core-web-sm @ git+https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.2.0/en_core_web_sm-2.2.0.tar.gz",  # noqa: E501
        "joblib==0.14.1",
        "scipy==1.4.1",
        "cython==0.29.17",
        "depgrep>=0.1.3",
        "scikit-learn==0.21.2",
        "colorama==0.4.1",
        "numpy==1.17.4",
        "matplotlib==3.2.1",
        "tensorflow==2.1.0",
        "setuptools==46.1.3",
        "spacy==2.2.4",
        "pandas==1.0.3",
        "pyarrow==0.16.0",
        "tqdm==4.38.0",
        "isort==4.3.21",
    ],
)
