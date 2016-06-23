==================
django-lock-tokens
==================

django-lock-tokens is a Django application that provides a locking mechanism to prevent concurrency editing.

It is not user-based nor session-based, it is just token based. When you lock a resource, you are given a token string with an expiration date, and you will need to provide this token to unlock that resource.

The application provides some useful functions to handle this token mechanism with sessions if you want to, and a REST API (with a javascript client for it) to deal with lock tokens without sessions.

Requires Django >= 1.7.

Table of Contents
-----------------

1. `Install`_
2. `TL;DR`_
3. `LockableModel proxy`_
4. `Session-based usage: lock_tokens.sessions module`_
5. `Session-based usage: lock_tokens.decorators module`_
6. `REST API`_
7. `REST API Javascript client`_
8. `Settings`_

Install
-------

1. Clone this repository and from the root, type ``python setup.py install``

2. Add ``lock_tokens`` to your ``INSTALLED_APPS`` setting. As django-lock-tokens uses the ``contenttypes`` framework, make sure it is also available in your ``INSTALLED_APPS`` setting:

.. code:: python

    INSTALLED_APPS = [
        ...
        'django.contrib.contenttypes',
        ...
        'lock_tokens',
    ]

3. Run ``python manage.py migrate`` from the root of your django project to install the lock tokens model.

4. If you want to use the ``LockableAdmin`` and all the session-based functionalities, make sure you have enabled a session middleware in your settings, for example:

.. code:: python

    MIDDLEWARE_CLASSES = (
        ...
        'django.contrib.sessions.middleware.SessionMiddleware',
        ...
    )

5. If you want to use the REST API, include ``lock_tokens.urls`` in your ``urls.py`` like this:

.. code:: python

    urlpatterns = [
      ...
      url(r'^lock_tokens/', include('lock_tokens.urls', namespace='lock_tokens')),
      ...
    ]

TL;DR
-----

After having completed previous steps, using the locking mechanism in your views is as simple as this:

.. code:: python

  from django.http import HttpResponseForbidden
  from lock_tokens.exceptions import AlreadyLockedError, UnlockForbiddenError
  from lock_tokens.sessions import check_for_session, lock_for_session, unlock_for_session

  from my_app.models import MyModel

  def view_with_object_edition(request):
    """This view locks the instance of MyModel that is to be edited."""
    # Get MyModel instance:
    obj = MyModel.objects.get(...)
    try:
        lock_for_session(obj, request.session)
    except AlreadyLockedError:
        return HttpResponseForbidden("This resource is locked, sorry !")
    # ... Do stuff
    return render(...)

  def view_that_saves_object(request):
    """This view locks the instance of MyModel that is to be edited."""
    # Get MyModel instance:
    obj = MyModel.objects.get(...)
    if not check_for_session(obj, request.session):
        return HttpResponseForbidden("Cannot modify the object, you don't have the lock.")
    # ... Do stuff
    unlock_for_session(obj, request.session)
    return render(...)


``LockableModel`` proxy
-----------------------

To make one of your models lockable, use the ``LockableModel`` class. ``LockableModel`` is just a Django proxy model, which simply provides additional locking methods to your models.

So you can either make your models inherit from ``LockableModel``:

.. code:: python

  from lock_tokens.models import LockableModel

  class MyModel(LockableModel):
      ...


  obj = MyModel.get(...)
  token = obj.lock()

or you can simply use it as a proxy on a given model instance:

.. code:: python

  from lock_tokens.models import LockableModel

  from my_app.models import MyModel

  obj = MyModel.get(...)
  token = LockableModel.lock(obj)

This can be useful if you don't want to expose the locking methods for your models everywhere, or if you want to lock resources that come from a third party application.

Note that as ``LockableModel`` is just a proxy model, make your models inherit from it won't change their fields so there will be no additional migrations required.

Additionally, if your model inherits from ``LockableModel``, the ``objects`` Manager has a specific method that allows you to get and lock a model like so:

.. code:: python

  >>>obj, token = MyModel.get_and_lock(...<usual get arguments>)

If you already overrided the default ``objects`` manager with a custom one and that you want to get this method available, make your custom manager inherit from ``lock_tokens.managers.LockableModelManager``.


``LockableModel.lock(self, token=None)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Locks the given object, or renew existing lock if the token parameter is provided.

Returns a ``dict`` containing a token a its expiration date.

Raises a ``lock_tokens.exceptions.AlreadyLockedError`` if the resource is already locked, or if the token is wrong.

Example:

.. code:: python

  def test(myObject):
      try:
          token = myObject.lock()
      except AlreadyLockedError:
          print "This object is already locked"
      return token

  >>>token = test(obj)
  {"token": "9692ac52a27a40308b82b49b77357c97", "expires": "2016-06-23 09:48:06"}
  >>>test(obj)
  "This object is already locked"
  >>>test(obj, token['token'])
  {"token": "9692ac52a27a40308b82b49b77357c97", "expires": "2016-06-23 09:48:26"}


``LockableModel.unlock(self, token)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Unlocks the given object if the provided token is correct.

Raises a ``lock_tokens.exceptions.UnlockForbiddenError``

``LockableModel.is_locked(self)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Returns a boolean that indicates whether the given object is currently locked or not.

``LockableModel.check_lock(self, token)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Returns a boolean that indicates if the given token is valid for this object. Will also return ``True`` with a warning if the object is not locked (lock expired or no lock).


``LockableAdmin`` for admin interface
-------------------------------------

If you want to make the admin interface lock-aware, and lock objects that are edited,
simply make your ``ModelAdmin`` class inherit from ``LockableAdmin``:

.. code:: python

  from lock_tokens.admin import LockableAdmin
  from django.contrib import admin

  from my_app.models import MyModel

  class MyModelAdmin(LockableModelAdmin):
    ...

  admin.site.register(MyModel, MyModelAdmin)

With this, when accessing a given instance of ``MyModel`` from the admin interface,
it will check that the instance is not locked. If it is not, it will lock it. If it is,
then there will be a warning message displayed to inform that the object cannot be edited,
and the saving buttons will not appear. And if despite this, the change form is sent, it will raise a ``PermissionDenied`` exception so you will get a HTTP 403 error.


Session-based usage: ``lock_tokens.sessions`` module
-----------------------------------------------------

In most cases, it will be the easiest way to deal with lock tokens, as you won't need to handle them at all.

``lock_for_session(obj, session)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Lock an object in the given session. This function will try to lock the object,
and if it succeeds, it will hold the token value in a session variable.

Raises a ``lock_tokens.exceptions.AlreadyLockedError`` if the resource is already locked.

``unlock_for_session(obj, session)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Unlocks an object in the given session.

Raises a ``lock_tokens.exceptions.UnlockForbiddenError`` if the session does not hold the lock on the object.

Session-based usage: ``lock_tokens.decorators`` module
-------------------------------------------------------

This module provides view decorators for common use cases.

``locks_object(model, get_object_id_callable)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Locks an object before executing view, and keep lock token in the request session. Does not unlock it when the view returns.

Arguments:

- ``model``: the concerned django Model
- ``get_object_id_callable``: a callable that will return the concerned object id based on the view arguments

Example:

.. code:: python

  from lock_tokens.decorators import locks_object

  @locks_object(MyModel, lambda request: request.GET.get('my_model_id'))
  def myview(request):
    # In this example the view will lock the MyModel instance with the id
    # provided in the request GET parameter my_model_id
    ...

  @locks_object(MyModel, lambda request, object_id: object_id)
  def anotherview(request, object_id):
    # In this example the view will lock the MyModel instance with the id
    # provided as the second view argument
    ...

``holds_lock_on_object(model, get_object_id_callable)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Locks an object before executing view, and keep lock token in the request session. Hold lock until the view is finished executing, then release it.

Arguments:

- ``model``: the concerned django Model
- ``get_object_id_callable``: a callable that will return the concerned object id based on the view arguments

See examples for ``locks_object``.


REST API
--------

If you want to use locking mechanism from outside your views, there is a simple HTTP API to handle tokens. It does not use sessions at all, so you need to handle the tokens yourself in this case.

Here are the different entry points, where ``<app_label>`` is the name of the application of the concerned model, ``<model>`` is the name of the model, ``<object_id>`` is the id of the cmodel instance, and ``<token>`` is the lock token value.

*POST* ``/lock_tokens/<app_label>/<model>/<object_id>/``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Locks object. Returns a JSON response with "token" and "expires" keys.

Returns a 404 HTTP error if the object could not be found.

Returns a 403 HTTP error if the object is already locked.

*GET* ``/lock_tokens/<app_label>/<model>/<object_id>/<token>/``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Returns a JSON response with "token" and "expires" keys.

Returns a 404 HTTP error if the object could not be found.

Returns a 403 HTTP error if the token is incorrect.

*PATCH* ``/lock_tokens/<app_label>/<model>/<object_id>/<token>/``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Renews the lock on the object. Returns a JSON response with "token" and "expires" keys.

Returns a 404 HTTP error if the object could not be found.

Returns a 403 HTTP error if the token is incorrect.

*DELETE* ``/lock_tokens/<app_label>/<model>/<object_id>/<token>/``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Unlocks object.

Returns a 404 HTTP error if the object could not be found.

Returns a 403 HTTP error if the token is incorrect.


REST API Javascript client
--------------------------

TODO

Settings
--------

You can override ``lock_token`` default settings by adding a ``dict`` named ``LOCK_TOKENS`` to your ``settings.py`` like so:

.. code:: python

  LOCK_TOKENS = {
    'TIMEOUT': 60,
    'DATEFORMAT': "%Y%m%d%H%M%S"
  }

TIMEOUT
^^^^^^^

The validity duration for a lock token in seconds. Defaults to ``3600`` (one hour).

DATEFORMAT
^^^^^^^^^^

The format of the expiration date returned in the token ``dict``. Defaults to ``"%Y-%m-%d %H:%M:%S"``
