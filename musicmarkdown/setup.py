from setuptools import setup, find_packages

setup(
    name='musicmarkdown',
    version='0.1',
    description='Makrdown compiler for music grids and structures',
    author='Marco Pascucci',
    author_email='marpas.paris@gmail.com',
    url='https://github.com/mpascucci/music_grid_markdown',
    packages=find_packages(),
    package_data={'musicmd': ['LICENCE.txt', 'resources/*']},
    include_package_data=True,
    # install_requires=[""]
)
