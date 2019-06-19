Django ModelForm History
========================

[![Build Status](https://travis-ci.org/martync/django-modelformhistory.svg?branch=master)](https://travis-ci.org/martync/django-modelformhistory)
[![Coverage Status](https://coveralls.io/repos/github/martync/django-modelformhistory/badge.svg?branch=master&refresh=cache)](https://coveralls.io/github/martync/django-modelformhistory?branch=master)

django-modelformhistory will save your modelform updates and store the human-readable values. The main goal is only to show the users what has been updated on a modelForms. If you search for a more lowlevel history app, consider using django-reversion or django-simple-history


Warning
-------

This package is under developpement. It has poor features and may be unstable. Don't use it in production yet. 


Requirements
------------

 - Django 1.10.* / Django 1.11.*
 - Tested under python 2.7 and 3.6


Install
-------

```
pip install django-modelformhistory
```


Then, add `modelformhistory` to INSTALLED_APPS


Usage
-----

Inherit your ModelForm with `HistoryModelFormMixin`

```python
from modelformhistory.forms import HistoryModelFormMixin

class MyModelForm(HistoryModelFormMixin, forms.ModelForm):
    pass
```

You can get the user that has made the change by : 

* Either pass the `request` on the form init, then the request.user will be automatically sent to the new history Entry
* or implement a `get_history_user` method on your ModelForm that will return a `auth.User` object


TODO
----

 * Provide generic views to see history by object, user & both
 * Improve doc
 * ~~Querying models history easily~~
 * ~~Add more support and tests for filefield, boolean~~
 * ~~FR translation~~

