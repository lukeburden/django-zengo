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

pip install django-zengo


### Usage ###

#### Configuring the webhook ####

Zengo comes with a view that processes messages sent by Zendesk and allows you to perform actions upon various Zendesk events.

##### Expose `zengo.views.WebhookView` #####

You need to configure your application to receive the webhook. To do so simply include it in your URL conf:

```python
from django.contrib import admin
from django.urls import path

from zengo.views import WebhookView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('zengo/webhook/', WebhookView.as_view())
]
```

###### Configure Zendesk to send events ######

Zendesk allows for many integrations, but for the purposes of Zengo we just need to be told when a ticket has been changed.

Log in as an administrator in Zendesk, and visit `Settings > Extensions > Targets > add target > HTTP target`.

Add an HTTP target with a URL of your service, and choose the `POST` method.

Note: for development, I recommend using `ngrok` to proxy requests through to your localhost.

Next, you must configure a trigger to use the target. Visit `Business Rules > Triggers > Add trigger`. Add a condition that suits your needs, such as, `Ticket is updated`, or `Ticket is created`, and select an action of `Notify target`, selecting the previously configured target. For JSON body, enter the following: 

```json
{
    "id": "{{ ticket.id }}"
}
```

You're done! Now whenever a ticket is created or updated in Zendesk, you should have an event being processed in your application.

#### Performing actions upon receiving Zendesk events ####

When Zengo receives a webhook from Zendesk, it will fire a signal indicating what has happened. In your application, you need to attach receivers to the signal that is most relevant to your need.

```python
from django.dispatch import receiver

from zengo.signals import new_ticket


@receiver(new_ticket)
def handle_new_ticket(sender, ticket, **kwargs):
    # perform your custom action here
    pass
```

#### Signals ####

- some signal
- another signal

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

