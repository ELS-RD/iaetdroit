from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))
REQUIREMENTS = [i.strip() for i in open("requirements.txt").readlines()]

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(name='annotations2csv',
      version='1.0.1',
      description='Generate a CSV file from Brat annotations',
      url='https://ojeulin_els@bitbucket.org/ojeulin_els/poc-zonage-cours-appel.git',
      author='Olivier Jeulin',
      author_email='o.jeulin@lefebvre-sarrut.eu',
      license='MIT',
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Developers',
          'Topic :: Text Processing :: Linguistic',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3.6'
      ],
      keywords='Brat annotation CSV development',
      packages=find_packages(exclude=['contrib', 'doc', 'tests', 'data']),
      python_requires='>=3.6',
      install_requires=[
          'intervaltree',
          'regex',
          'pyfunctional'],
      entry_points={
          'console_scripts': [
              'sample=annotations2csv:main',
          ],
      },
      )
