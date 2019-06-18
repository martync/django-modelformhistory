# coding: utf-8
from __future__ import print_function, division, absolute_import, unicode_literals

from .models import Entry


def log_history(user, content_object, message):
    """Shortcut to save a new Entry log for that content object

    Args:
        user (auth.User): The user
        content_object (model.Model): Any django model that will be saved
        message (str): The human readable message

    Returns:
        modelformhistory.Entry: The freshly created Entry
    """

    return Entry.create(user=user, content_object=content_object, short_message=message)
