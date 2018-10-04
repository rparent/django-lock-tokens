.. :changelog:

History
-------

0.2.1 (2018-10-04)
^^^^^^^^^^^^^^^^^^
- Fixes ``LockToken.save`` method to prevent potential transaction errors
- Adds a template tag to handle lock on the client side when overriding default ``change_form_template`` in ``LockableModelAdmin``
- Better handling of invalid lock token strings (see discussion here_) to prevent overwriting

.. _here: https://github.com/rparent/django-lock-tokens/issues/6

0.1.4 (2017-09-07)
^^^^^^^^^^^^^^^^^^

- Adds a ``created`` field to the ``LockToken`` model

