import os

from setuptools import setup


def read(fname):
    """
    Helper to read README
    """
    return open(os.path.join(os.path.dirname(__file__), fname)).read().strip()


setup(
    name="buzz",
    version="3.0.6",  # DO NOT EDIT THIS LINE MANUALLY. LET bump2version UTILITY DO IT
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
        "bllipparser",
        "scipy",
        "cython",
        "depgrep>=0.1.3",
        "scikit-learn",
        "colorama",
        # 'benepar',
        # 'benepar[cpu]',
        "tensorflow>=1.12.1",
        "setuptools>=41.0.0",
        "spacy==2.1.6",
        "pandas==0.25.0",
        "tqdm==4.33.0",
        "isort==4.3.21",
    ],
)
