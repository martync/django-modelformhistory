Django ModelForm History
====================

django-modelformhistory will save your modelform updates and store the human-readable values. The main goal is only to show the users what has been updated on a modelForms. If you search for a more lowlevel history app, consider using django-reversion or django-simple-history



Requirements
------------

 - Django 1.10.* / Django 1.11.*
 - Tested under python 2.7 and 3.6


Install
-------

```
pip install django-modelformhistory
```


Add `modelformhistory` to INSTALLED_APPS

```python
INSTALLED_APPS = (
    ...
    "modelformhistory",
)
```


Usage
-----

Inherit your modelForm with `HistoryModelFormMixin`

```python
from modelformhistory.forms import HistoryModelFormMixin

class MyModelForm(HistoryModelFormMixin, forms.ModelForm):
   ...
```



```html
{% load multiple_auth_tags %}

{% block content %}
    {% get_logged_in_users as logged_in_users %}
    <ul>
        {% for u in logged_in_users %}
            <li>
                {% if u != request.user %}
                    <b>{{ u.username }}</b> - {{ u.get_full_name }}
                {% else %}
                    <a href="{% url "multiauth_switch" forloop.counter0 %}">
                        <b>{{ u.username }}</b> - {{ u.get_full_name }}
                    </a>
                {% endif %}
            </li>
        {% endfor %}
    </ul>
    <a href="{% url "multiauth_login" %}">Add account</a>
{% endblock content %}
```


