# coding: utf-8
from __future__ import print_function, division, absolute_import, unicode_literals
import os

from django.apps import apps
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, RequestFactory

from modelformhistory.admin import HistoryModelAdmin
from modelformhistory.apps import ModelformhistoryConfig

from modelformhistory.forms import HistoryModelFormMixin
from modelformhistory.models import Entry, ADDITION
from sampleapp.models import Foo, Bar, Baz
from sampleapp.forms import FooModelForm, FooModelFormRequest


User = get_user_model()

__all__ = ("ModelFormHistoryTestCase", "ModelFormHistoryAdminTestCase")


class MockRequest:
    pass


class MockSuperUser:
    def has_perm(self, perm):
        return True


request = MockRequest()
request.user = MockSuperUser()


class ModelFormHistoryAdminTestCase(TestCase):
    def setUp(self):
        bar = Bar.objects.create(name="bar")
        self.foo = Foo.objects.create(name="Test foo", integer=1, choose_somthing="ok", bar=bar)
        self.site = AdminSite()

    def test_modeladmin_str(self):
        ma = HistoryModelAdmin(Foo, self.site)
        form = ma.get_form(request)()
        self.assertIsInstance(form, HistoryModelFormMixin)


class ModelFormHistoryTestCase(TestCase):
    def setUp(self):
        self.user = User(username="test_user", last_name="TEST", first_name="User")
        self.user.save()

        bars = ["bar", "rab", "bra"]
        bazs = ["baz", "zab", "bza"]
        [Bar(name=bar).save() for bar in bars]
        [Baz(name=baz).save() for baz in bazs]
        bar = Bar.objects.get(name="bar")
        bazs = Baz.objects.all()

        self.foo = Foo(name="Test foo", integer=1, choose_somthing="ok", bar=bar)
        self.foo.save()
        [self.foo.baz.add(b) for b in bazs]
        self.indentical_datas = {
            "bar": self.foo.bar.id,
            "name": self.foo.name,
            "baz": [str(baz.id) for baz in self.foo.baz.all()],
            "integer": self.foo.integer,
            "choose_somthing": self.foo.choose_somthing,
            "yesorno": "1",
        }

    def check_changed_data(self, changed_data, label, initial_value, changed_value):
        self.assertEqual(str(changed_data), label)
        self.assertEqual(changed_data.label, label)
        self.assertEqual(changed_data.initial_value, initial_value)
        self.assertEqual(changed_data.changed_value, changed_value)

    def test_str(self):
        entry = Entry.create(self.user, self.foo, ADDITION, changelog=[])
        self.assertEqual(str(entry), "User TEST has added 'Foo Test foo'")

    def test_no_change(self):
        form = FooModelForm(user=self.user, instance=self.foo, data=self.indentical_datas)
        form.save()
        self.assertEqual(Entry.objects.all().count(), 0)

    def test_update_choicefield(self):
        data = self.indentical_datas.copy()

        # Save another value on the choiceField
        data["choose_somthing"] = "nok"
        form = FooModelForm(user=self.user, instance=self.foo, data=data)
        form.save()
        self.assertEqual(Entry.objects.all().count(), 1)
        entry = Entry.objects.all()[0]
        self.assertTrue(entry.is_change())
        self.assertFalse(entry.is_addition())
        self.assertFalse(entry.is_deletion())
        self.assertEqual(entry.changeddata_set.all().count(), 1)
        changed_data = entry.changeddata_set.all()[0]
        self.check_changed_data(changed_data, "Make your choice", "It's OK", "It's not OK")

    def test_update_foreign_key(self):
        data = self.indentical_datas.copy()

        # Save another value on the foreignKey
        data["bar"] = Bar.objects.get(name="rab").id
        form = FooModelForm(user=self.user, instance=self.foo, data=data)
        form.save()
        self.assertEqual(Entry.objects.all().count(), 1)
        entry = Entry.objects.all()[0]
        self.assertTrue(entry.is_change())
        self.assertFalse(entry.is_addition())
        self.assertFalse(entry.is_deletion())
        self.assertEqual(entry.changeddata_set.all().count(), 1)
        changed_data = entry.changeddata_set.all()[0]
        self.check_changed_data(changed_data, "Name of the bar", "bar", "rab")

        # Save an empty value on the foreignKey
        del data["bar"]
        form = FooModelForm(user=self.user, instance=self.foo, data=data)
        form.save()
        self.assertEqual(Entry.objects.all().count(), 2)
        entry = Entry.objects.all()[0]
        self.assertEqual(entry.changeddata_set.all().count(), 1)
        changed_data = entry.changeddata_set.all()[0]
        self.check_changed_data(changed_data, "Name of the bar", "rab", "Empty")

    def test_update_manytomany(self):
        data = self.indentical_datas.copy()

        # Save another multiple values on M2M
        data["baz"] = [b.id for b in Baz.objects.filter(name__startswith="b")]
        form = FooModelForm(user=self.user, instance=self.foo, data=data)
        form.save()
        self.assertEqual(Entry.objects.all().count(), 1)
        entry = Entry.objects.all()[0]
        self.assertTrue(entry.is_change())
        self.assertFalse(entry.is_addition())
        self.assertFalse(entry.is_deletion())
        self.assertEqual(entry.changeddata_set.all().count(), 1)
        changed_data = entry.changeddata_set.all()[0]
        self.check_changed_data(changed_data, "Select some baz", "baz, zab, bza", "baz, bza")

        # Save a single object on M2M
        data["baz"] = [Baz.objects.get(name="zab").id]
        form = FooModelForm(user=self.user, instance=self.foo, data=data)
        form.save()
        self.assertEqual(Entry.objects.all().count(), 2)
        entry = Entry.objects.all()[0]
        changed_data = entry.changeddata_set.all()[0]
        self.assertEqual(entry.changeddata_set.all().count(), 1)
        self.check_changed_data(changed_data, "Select some baz", "baz, bza", "zab")

        # Save an empty value on M2M
        del data["baz"]
        form = FooModelForm(user=self.user, instance=self.foo, data=data)
        form.save()
        self.assertEqual(Entry.objects.all().count(), 3)
        entry = Entry.objects.all()[0]
        self.assertEqual(entry.changeddata_set.all().count(), 1)
        changed_data = entry.changeddata_set.all()[0]
        self.check_changed_data(changed_data, "Select some baz", "zab", "Empty")

    def test_update_boolean(self):
        data = self.indentical_datas.copy()

        data["yesorno"] = ""
        form = FooModelForm(user=self.user, instance=self.foo, data=data)
        form.save()
        self.assertEqual(Entry.objects.all().count(), 1)
        entry = Entry.objects.all()[0]
        changed_data = entry.changeddata_set.all()[0]
        self.check_changed_data(changed_data, "Check for yes", "Yes", "No")

    def test_update_filefield(self):
        data = self.indentical_datas.copy()
        upload_file = open("images/poney.jpeg", "rb")
        file_dict = {"picture": SimpleUploadedFile(upload_file.name, upload_file.read())}
        form = FooModelForm(user=self.user, instance=self.foo, data=data, files=file_dict)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(Entry.objects.all().count(), 1)
        entry = Entry.objects.all()[0]
        self.assertEqual(entry.changeddata_set.all().count(), 1)
        changed_data = entry.changeddata_set.all()[0]
        self.check_changed_data(changed_data, "Picture", None, "poney.jpeg")

        upload_file = open("images/poney-bw.jpg", "rb")
        file_dict = {"picture": SimpleUploadedFile(upload_file.name, upload_file.read())}
        form = FooModelForm(user=self.user, instance=self.foo, data=data, files=file_dict)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(Entry.objects.all().count(), 2)
        entry = Entry.objects.all()[0]
        self.assertEqual(entry.changeddata_set.all().count(), 1)
        changed_data = entry.changeddata_set.all()[0]
        self.check_changed_data(changed_data, "Picture", "poney.jpeg", "poney-bw.jpg")

        os.remove("poney.jpeg")
        os.remove("poney-bw.jpg")

    def test_add(self):
        data = self.indentical_datas.copy()
        form = FooModelForm(user=self.user, instance=None, data=data)
        form.save()
        self.assertEqual(Entry.objects.all().count(), 1)
        entry = Entry.objects.all()[0]
        self.assertEqual(entry.changeddata_set.all().count(), 0)
        self.assertTrue(entry.is_addition())
        self.assertFalse(entry.is_change())
        self.assertEqual(entry.short_message, "User TEST has added 'Foo Test foo'")

    def test_get_history_user(self):
        form = FooModelForm(user=self.user, instance=None, data=self.indentical_datas)
        self.assertEqual(form.get_history_user(), self.user)
        form = FooModelFormRequest(request=None, instance=None, data=self.indentical_datas)
        self.assertEqual(form.get_history_user(), None)
        request = RequestFactory()
        request.user = self.user
        form = FooModelFormRequest(request=request, instance=None, data=self.indentical_datas)
        self.assertEqual(form.get_history_user(), self.user)

    def test_get_history_entries(self):
        self.assertEqual(self.foo.get_history_entries().count(), 0)
        data = self.indentical_datas.copy()
        data["name"] = "Another name"
        form = FooModelForm(user=self.user, instance=self.foo, data=data)
        form.save()
        self.assertEqual(self.foo.get_history_entries().count(), 1)
        entry = self.foo.get_history_entries()[0]
        self.assertEqual(entry.content_object, self.foo)
        self.assertEqual(entry.changeddata_set.all().count(), 1)

    def test_log_custom_history(self):
        self.foo.log_custom_history(self.user, "Doing a custom action")
        self.assertEqual(self.foo.get_history_entries().count(), 1)
        entry = self.foo.get_history_entries()[0]
        self.assertEqual(entry.get_user_full_name(), self.user.get_full_name())
        self.assertEqual(entry.short_message, "Doing a custom action")
        self.assertEqual(entry.changeddata_set.all().count(), 0)

    def test_anonymous_log_entry_without_changeddata(self):
        Entry.create(None, self.foo, short_message="Added custom action on this object")
        self.assertEqual(self.foo.get_history_entries().count(), 1)
        entry = self.foo.get_history_entries()[0]
        self.assertEqual(entry.get_user_full_name(), "Anonymous")
        self.assertEqual(entry.short_message, "Added custom action on this object")
        self.assertEqual(entry.changeddata_set.all().count(), 0)


class ModelformhistoryConfigTest(TestCase):
    def test_apps(self):
        self.assertEqual(ModelformhistoryConfig.name, "modelformhistory")
        self.assertEqual(apps.get_app_config("modelformhistory").name, "modelformhistory")
