from setuptools import setup, find_packages


# Dependencies for using the library.
install_requires = [
    'attrs',
    'click >=7.0,<8.0',
    'fabric',
    'paramiko',
]


setup(
    name='srt-utils',
    version='0.1',
    author='Maria Sharabayko',
    author_email='maria.bakholdina@gmail.com',
    packages=find_packages(),
    install_requires=install_requires,
    extras_require={
        'testing':  ['pytest >=3.0,<4.0'],
    }
)