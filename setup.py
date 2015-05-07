from setuptools import setup, find_packages

setup(name='pyjsonselect',
      version='0.2.2',
      description='Fully-compliant implementation of JSONSelect',
      author='Dan Vanderkam',
      author_email='danvdk@gmail.com',
      url='https://github.com/danvk/pyjsonselect/',
      packages=['jsonselect'],
      install_requires=[],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: Apache Software License',
          'Topic :: Utilities',
          'Topic :: Text Processing'
      ],
      keywords=[
          'css',
          'json',
          'jsonselect'
      ]
)
