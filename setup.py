from setuptools import setup
from setuptools.command.install import install

import os
from os.path import isfile, isdir, join, dirname

class CustomInstallCommand(install):
    """
    Customized setuptools install command, which installs
    some NLTK data automatically
    """
    def run(self):
        from setuptools.command.install import install
        try:
            import cython
        except ImportError:
            os.system('pip install cython')
        try:
            import numpy
        except ImportError:
            os.system('pip install numpy') 
        import site
        try:
            reload(site)
        except NameError:
            pass
        install.run(self)


setup(name='buzz',
      version='1.0.5',  # DO NOT EDIT THIS LINE MANUALLY. LET bump2version UTILITY DO IT
      description='Sophisticated corpus linguistics',
      url='http://github.com/interrogator/buzz',
      author='Daniel McDonald',
      include_package_data=True,
      zip_safe=False,
      packages=['buzz'],
      scripts=['buzz/parse'],
      setup_requires=['cython', 'numpy'],
      cmdclass={'install': CustomInstallCommand,},
      package_data={'buzz': ['*.sh',
                             'buzz/*.sh',
                             '*.p',
                             'dictionaries/*.p',
                             '*.py',
                             'dictionaries/*.py']},
      author_email='mcddjx@gmail.com',
      license='MIT',
      keywords=['corpus', 'linguistics', 'nlp'],
      install_requires=['nltk',
                        'bllipparser',
                        'scipy',
                        'cython',
                        'benepar',
                        'benepar[cpu]',
                        'tensorflow==1.12.0',
                        'spacy',
                        'pandas',
                        'tqdm',
                        'pyparsing',
                        'tabview'],
      dependency_links=['https://github.com/interrogator/tabview/archive/master.zip'])
