import os

from setuptools import setup


def read(fname):
    """
    Helper to read README
    """
    return open(os.path.join(os.path.dirname(__file__), fname)).read().strip()


setup(
    name="buzz",
    version="3.1.8",  # DO NOT EDIT THIS LINE MANUALLY. LET bump2version UTILITY DO IT
    description="Sophisticated corpus linguistics",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    url="http://github.com/interrogator/buzz",
    author="Daniel McDonald",
    include_package_data=True,
    zip_safe=False,
    packages=["buzz"],
    scripts=["bin/parse"],
    extras_require={"word": ["buzzword>=1.4.0"]},
    author_email="mcddjx@gmail.com",
    license="MIT",
    keywords=["corpus", "linguistics", "nlp"],
    install_requires=[
        "nltk==3.5",
        "buzzepar>=0.1.2",
        # "en-core-web-sm @ git+https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.2.0/en_core_web_sm-2.2.0.tar.gz",  # noqa: E501
        "joblib==0.17.0",
        "scipy==1.4.1",
        "cython==0.29.21",
        "depgrep>=0.1.3",
        "scikit-learn==0.23.2",
        "colorama==0.4.4",
        "numpy==1.18.5",
        "matplotlib==3.3.2",
        "tensorflow==2.5.1",
        "setuptools==50.3.2",
        "spacy==2.3.2",
        "pandas==1.1.4",
        "seaborn==0.11.0",
        "pyarrow==2.0.0",
        "tqdm==4.51.0",
        "isort==5.6.4",
        "flake8==3.8.4"
    ],
)
