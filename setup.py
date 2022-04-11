from setuptools import setup, find_packages

setup(
    name='asyncgelf',
    version='0.1.1',
    author='Sergey Malinkin',
    author_email='malinkinsa@yandex.ru',
    url='https://github.com/malinkinsa/asyncgelf',
    download_url='https://github.com/malinkinsa/asyncgelf/archive/refs/tags/0.1.1.tar.gz',
    description='Async python logging handlers that send messages in the Graylog Extended Log Format (GELF).',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    license='MIT',
    keywords='gelf logging graylog graylog2 tcp',
    packages=find_packages(),
    install_requires=[
        'asyncio',
        'httpx',
    ],
)
