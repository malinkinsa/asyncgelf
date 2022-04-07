from setuptools import setup, find_packages

setup(
    name='asyncgelf',
    version='0.0.2',
    author='Sergey Malinkin',
    author_email='malinkinsa@yandex.ru',
    url='https://github.com/malinkinsa/asyncgelf',
    description='Async python logging handlers that send messages in the Graylog Extended Log Format (GELF).',
    long_description='',
    packages=find_packages(),
    install_requires=[
        'asyncio',
    ],
)
