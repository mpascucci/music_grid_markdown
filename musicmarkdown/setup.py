from setuptools import setup, find_packages

setup(
    name='musicmarkdown',
    packages=find_packages(),
    package_data={'musicmd': ['resources/*']},
    include_package_data=True,
    # install_requires=[""]
)
