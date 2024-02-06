from setuptools import setup, find_packages

setup(
    name='asyncgelf',
    version='1.2.0',
    author='Sergey Malinkin',
    author_email='malinkinsa@yandex.ru',
    url='https://github.com/malinkinsa/asyncgelf',
    download_url='https://github.com/malinkinsa/asyncgelf/archive/refs/tags/1.2.0.tar.gz',
    description='Async python logging handlers that send messages in the Graylog Extended Log Format (GELF).',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    license='MIT',
    keywords='gelf logging graylog graylog2 tcp udp http',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Logging',
    ],
    packages=find_packages(),
    install_requires=[
        'asyncio',
        'httpx',
    ],
)
