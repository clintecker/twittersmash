from setuptools import setup

setup(name='twittersmash',
      version='0.1',
      description='Ars Technica\'s twitter publishing application',
      author='Clint Ecker, Kurt Mackey',
      author_email='clint@arstechnica.com',
      url='https://github.com/ArsTechnica/twittersmash/tree/master',
      packages=['twittersmash',],
      entry_points={'django.apps': 'twittersmash = twittersmash'},
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Web Environment',
                   'Intended Audience :: Developers',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Utilities'],
      )

