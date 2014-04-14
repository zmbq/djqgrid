djqgrid
=======

``djqgrid`` is a Django wrapper for jqGrid.

``djqgrid`` lets you define grids in a Django-familiar way, while taking care of most of the mundane Python-JavaScript bridge for you.

Quick Example
-------------

Add ``djqgrid`` to your project
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Install with ``pip install djqgrid``
2. Add ``djqgrid`` to your ``INSTALLED_APPS``.
3. Reference the ``jqGrid`` and ``jQueryUI`` JavaScript and CSS files 
4. Reference the script at ``{% static "js/djqgrid_utils.js" %}``
5. Add the ``djqgrid`` URLs to ``urls.py``:
   ::
   
    urlpatterns += patterns('', url(r^'grid_json/', include (djqgrid.urls))

Define your model
^^^^^^^^^^^^^^^^^
::

    class MyModel(models.Model):
        name = models.CharField(max_length=40)
        desc = models.CharField(max_length=100)
        url = models.URLField()
        height = models.IntField()

Define your grid
^^^^^^^^^^^^^^^^ 
::

    class MyGrid(Grid):
        model = MyModel 

        name = TextColumn(title='Name', model_path='name')
        height = TextColumn(title='Height', model_path='height', align='right')
        desc = LinkColumn(title='Description', model_path='desc', url_builder=lambda m: m.url)

What we have here is a grid associated with ``MyModel`` objects - each grid row represents one object. The grid has three columns:

1. Name - a basic column containing ``model.name``
2. Height - containing ``model.height``, but right aligned
3. Description - containing a link - its text will be ``model.desc`` and the URL will be ``model.url``
        
One thing to note is ``align='right'`` - this property is passed directly to jqGrid in the column's `colModel`. Any property can be passed to jqGrid this way. For example ``TextColumn(title=..., model_path=..., editable=true)`` creates an editable column.

Add the grid to your view and template
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  The view: ::

    define myview(request):
        grid = MyGrid()
        return render(request, 'my_template.html', { grid: grid })
    

  The template: ::

    {% load djqgrid %}
   
    <div id="grid-div">
        {% jqgrid grid %}
    </div>


Now run the view. You should see a very nice grid that supports paging and sorting.

