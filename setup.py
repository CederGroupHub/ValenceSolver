from setuptools import setup, find_packages

__author__ = 'Tanjin He'
__maintainer__ = 'Tanjin He'
__email__ = 'tanjin_he@berkeley.edu'

if __name__ == "__main__":
    setup(name='ValenceSolver',
          version=1.0,
          author="Tanjin He",
          author_email="tanjin_he@berkeley.edu",
          license="MIT License",
          packages=find_packages(),
          install_requires=[
              "sympy",
              "unidecode",
          ],
          zip_safe=False)

