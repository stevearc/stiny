""" Setup file. """
import os

from setuptools import setup, find_packages


HERE = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(HERE, 'README.rst')).read()
CHANGES = open(os.path.join(HERE, 'CHANGES.rst')).read()

REQUIREMENTS = [
    'rpi.gpio',
    'bottle',
    'google-api-python-client',
]

if __name__ == "__main__":
    setup(
        name='stiny_worker',
        version="develop",
        description='Home automation assistant',
        long_description=README + '\n\n' + CHANGES,
        classifiers=[
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Private :: Do Not Upload',
        ],
        author='Steven Arcangeli',
        author_email='stevearc@stevearc.com',
        url='',
        platforms='any',
        include_package_data=True,
        zip_safe=True,
        packages=find_packages(),
        entry_points={
            'console_scripts': [
                'stiny-worker = stiny_worker:main',
            ],
        },
        install_requires=REQUIREMENTS,
    )
