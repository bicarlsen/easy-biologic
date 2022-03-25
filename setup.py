import setuptools


# get __version__
exec( open( 'easy_biologic/_version.py' ).read() )

with open("README.md", "r") as fh:
    long_description = fh.read()


project_urls = {
    'Source Code': 'https://github.com/bicarlsen/easy-biologic',
    'Bug Tracker': 'https://github.com/bicarlsen/easy-biologic/issues'
}


setuptools.setup(
    name = "easy-biologic",
    version = __version__,
    author = "Brian Carlsen",
    author_email = "carlsen.bri@gmail.com",
    description = "Controller class for communicating with BioLogic devices.",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    keywords = [ 'biologic' ],
    url = "",
    project_urls = project_urls,
    packages = setuptools.find_packages(),
    python_requires = '>=3.7',
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: Microsoft :: Windows",
        "Development Status :: 3 - Alpha"
    ],
    install_requires = [],
    package_data = {
        'easy_biologic': [
            'technique_verison.json',
            f'techniques-*/*'
        ]
    }
)