from setuptools import setup, find_packages

setup(
    name='discord_tools',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'requests==2.31.0',
        'Pillow==10.1.0',
        'g4f==0.2.2.7',
        'openai==1.10.0',
        'selenium==4.16.0',
        'webdriver-manager==4.0.1',
        'beautifulsoup4==4.12.2',
        'characterai==0.8.0',
        'mtranslate==1.8'
    ],
)
