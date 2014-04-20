Installation
============

To install djqgrid, please follow these steps:

1. Install with ``pip install djqgrid``
2. Add ``djqgrid`` to your ``INSTALLED_APPS``.
3. Reference the ``jqGrid`` and ``jQueryUI`` JavaScript and CSS files
4. Reference the script at ``{% static "js/djqgrid_utils.js" %}``
5. Add the ``djqgrid`` URLs to ``urls.py``:
   ::

    urlpatterns += patterns('', url(r^'grid_json/', include (djqgrid.urls))
