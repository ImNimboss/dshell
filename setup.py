from setuptools import setup

with open('.github/README.md') as file:
    long_description = file.read()

with open('dshell/__init__.py') as file:
    lines = file.readlines()

for line in lines:
    if line.startswith('__version__: str = '):
        version = line[20:-2]
        break

setup(
    name = 'discordshell',
    version = version,
    description = 'DShell is a package that combines with discord.py and Jishaku to turn a Discord channel into a shell on which bash commands can be run.',
    long_description = long_description,
    long_description_content_type = 'text/markdown',
    author = 'ImNimboss',
    author_email = 'nim@nimboss.me',
    url = 'https://github.com/ImNimboss/dshell',
    license = 'MIT',
    packages = ['dshell'],
    keywords = [
        'shell', 'discord', 'terminal', 'powershell', 'command-prompt',
        'internet', 'console', 'shell-access', 'utility'
    ],
    install_requires = [],
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Communications',
        'Topic :: Communications :: Chat',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries',
        'Topic :: System :: Shells',
        'Topic :: System :: System Shells',
        'Topic :: System :: Systems Administration',
        'Topic :: Terminals',
        'Topic :: Terminals :: Terminal Emulators/X Terminals',
        'Topic :: Utilities'
    ], # https://pypi.org/classifiers/
    python_requires = '>=3.6.0',
    project_urls = {
        'Documentation': 'https://github.com/ImNimboss/dshell/tree/main/Documentation',
        'Issue Tracker': 'https://github.com/ImNimboss/dshell/issues',
        'Source': 'https://github.com/ImNimboss/dshell',
        'Funding': 'https://patreon.com/nimboss',
        'Creator': 'https://nimboss.me',
        'Discord': 'https://discord.gg/FcxqdJ7AQq'
    }
)