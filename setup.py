import os
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()
# LICENSE = open(os.path.join(os.path.dirname(__file__), 'LICENSE.txt')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='djqgrid',
    version='0.2.2',
    packages=['djqgrid', 'djqgrid.templatetags'],
    include_package_data=True,
    license='MIT license',
    description='A Django wrapper for jqGrid',
    long_description=README,
    url='https://github.com/zmbq/djqgrid/',
    author='Itay Zandbank',
    author_email='zmbq@platonix.com',
    install_requires=['django>=1.6'],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Development Status :: 3 - Alpha',
    ],
    keywords='django jqgrid client-side grid',
)