# Ease integration of Zendesk into your Django app

[![](https://img.shields.io/pypi/v/django-zengo.svg)](https://pypi.python.org/pypi/django-zengo/)
[![](https://img.shields.io/badge/license-MIT-blue.svg)](https://pypi.python.org/pypi/django-zengo/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Codecov](https://codecov.io/gh/lukeburden/django-zengo/branch/master/graph/badge.svg)](https://codecov.io/gh/lukeburden/django-zengo)
[![CircleCI](https://circleci.com/gh/lukeburden/django-zengo.svg?style=svg)](https://circleci.com/gh/lukeburden/django-zengo)


## django-zengo

`django-zengo` is a Django app that provides conveniences for integrating with Zendesk.

It facilitates receiving webhook updates from Zendesk and detecting new tickets and comments on existing tickets.

### Installation ####

### Usage ###

## Contribute

`django-zengo` supports a variety of Python and Django versions. It's best if you test each one of these before committing. Our [Circle CI Integration](https://circleci.com) will test these when you push but knowing before you commit prevents from having to do a lot of extra commits to get the build to pass.

### Environment Setup

In order to easily test on all these Pythons and run the exact same thing that CI will execute you'll want to setup [pyenv](https://github.com/yyuu/pyenv) and install the Python versions outlined in [tox.ini](tox.ini).

If you are on Mac OS X, it's recommended you use [brew](http://brew.sh/). After installing `brew` run:

```
$ brew install pyenv pyenv-virtualenv pyenv-virtualenvwrapper
```

Then:

```
pyenv install -s 2.7.14
pyenv install -s 3.4.7
pyenv install -s 3.5.4
pyenv install -s 3.6.3
pyenv virtualenv 2.7.14
pyenv virtualenv 3.4.7
pyenv virtualenv 3.5.4
pyenv virtualenv 3.6.3
pyenv global 2.7.14 3.4.7 3.5.4 3.6.3
pip install detox
```

To run the test suite:

Make sure you are NOT inside a `virtualenv` and then:

```
$ detox
```

This will execute the testing matrix in parallel as defined in the `tox.ini`.

