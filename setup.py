from setuptools import setup

setup(
    name="GAME1",
    options = {
        'build_apps': {
            'console_apps': {
                'GAME1': 'main.py',
            },
            'platforms': [
                'win_amd64'
            ],
        },
    }
)
