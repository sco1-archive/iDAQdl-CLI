from setuptools import setup

setup(
    name='iDAQclipy',
    version='0.1',
    py_modules=['iDAQ'],
    install_requires=[
        'Click',
        'bs4',
        'pytz'
    ],
    entry_points='''
        [console_scripts]
        iDAQ=iDAQ:cli
    ''',
)