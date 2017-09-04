=====
Usage
=====

To use django-lock-tokens in a project, add it to your `INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'lock_tokens.apps.LockTokensConfig',
        ...
    )

Add django-lock-tokens's URL patterns:

.. code-block:: python

    from lock_tokens import urls as lock_tokens_urls


    urlpatterns = [
        ...
        url(r'^', include(lock_tokens_urls)),
        ...
    ]
