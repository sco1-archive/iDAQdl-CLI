from setuptools import setup

setup(
    name='iDAQcli',
    version='0.1',
    py_modules=['iDAQcli'],
    install_requires=[
        'Click',
        'bs4',
        'pytz'
    ],
    entry_points='''
        [console_scripts]
        iDAQcli=iDAQcli:cli
    ''',
)