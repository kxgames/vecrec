import distutils.core

# Uploading to PyPI
# =================
# $ python setup.py register -r pypi
# $ python setup.py sdist upload -r pypi

version = '0.0'
distutils.core.setup(
        name='vecrec',
        version=version,
        author='Kale Kundert and Alex Mitchell',
        url='https://github.com/kxgames/vecrec',
        download_url='https://github.com/kxgames/vecrec/tarball/'+version,
        license='LICENSE.txt',
        description="A 2D vector and rectangle library.",
        long_description=open('README.rst').read(),
        keywords=['2D', 'vector', 'rectangle', 'library'],
        packages=['vecrec'],
        requires=['finalexam', 'coverage'],
)
