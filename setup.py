""" Setup file. """
import os

from setuptools import setup, find_packages


HERE = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(HERE, 'README.rst')).read()
CHANGES = open(os.path.join(HERE, 'CHANGES.rst')).read()

REQUIREMENTS = [
    'google-api-python-client',
    'pycrypto',
    'pyramid>=1.7',
    'pyramid_beaker',
    'pyramid_duh>=0.1.2',
    'pyramid_jinja2',
    'pyramid_webpack',
    'requests',
    'twilio',
    'six',
]

if __name__ == "__main__":
    setup(
        name='stiny',
        version="develop",
        description='Home automation assistant',
        long_description=README + '\n\n' + CHANGES,
        classifiers=[
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Framework :: Pyramid',
            'Private :: Do Not Upload',
        ],
        author='Steven Arcangeli',
        author_email='stevearc@stevearc.com',
        url='',
        platforms='any',
        include_package_data=True,
        zip_safe=True,
        packages=find_packages(exclude=('worker',)),
        entry_points={
            'paste.app_factory': [
                'main = stiny:main',
            ],
            'paste.filter_app_factory': [
                'security_headers = stiny.security:SecurityHeaders',
            ],
            'console_scripts': [
                'stiny-calendar = stiny.scripts:do_calendar',
                'stiny-setup = stiny.scripts:save_credentials',
            ],
        },
        install_requires=REQUIREMENTS,
    )
