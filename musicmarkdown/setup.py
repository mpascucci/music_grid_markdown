from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='musicmarkdown',
    version='0.3.2',
    description='Makrdown compiler for music grids and structures',
    long_description=long_description,
    author='Marco Pascucci',
    author_email='marpas.paris@gmail.com',
    url='https://github.com/mpascucci/music_grid_markdown',
    packages=find_packages(),
    package_data={'musicmd': ['LICENCE.txt', 'agrid.jpg' 'resources/*']},
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    # install_requires=[""]
)
