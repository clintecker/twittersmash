from distutils.core import setup

setup(name='twittersmash',
      version='1.0',
      description='Combine multiple RSS feeds of Tweets into a single Twitter account base on filters',
      author='Clint Ecker',
      author_email='me@clintecker.com',
      url='http://github.com/clintecker/twittersmash/tree/master',
      packages=['twittersmash', 'twittersmash.management', 'twittersmash.management.commands'],
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Web Environment',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Utilities'],
      )