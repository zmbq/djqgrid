import copy
from zlib import crc32
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.utils import six
from django.utils.datastructures import SortedDict
import views
from columns import Column
from grid_registrar import register_grid

__author__ = 'zmbq'

# The meta class implementation is taken from the Django Form class, only with name changes
def _get_declared_columns(bases, attrs, with_base_columns=True):
    """
    Create a list of grid column instances from the passed in 'attrs', plus any
    similar columns on the base classes (in 'bases'). This is used by Grid metaclass.

    If 'with_base_columns' is True, all columns from the bases are used.
    Otherwise, only columns in the 'declared_columns' attribute on the bases are
    used. The distinction is useful in ModelForm subclassing.
    Also integrates any additional media definitions.
    """
    columns = [(column_name, attrs.pop(column_name)) for column_name, obj in list(six.iteritems(attrs)) if isinstance(obj, Column)]
    columns.sort(key=lambda x: x[1]._count)

    # If this class is subclassing another Form, add that Form's columns.
    # Note that we loop over the bases in *reverse*. This is necessary in
    # order to preserve the correct order of columns.
    if with_base_columns:
        for base in bases[::-1]:
            if hasattr(base, 'base_columns'):
                columns = list(six.iteritems(base.base_columns)) + columns
    else:
        for base in bases[::-1]:
            if hasattr(base, 'declared_columns'):
                columns = list(six.iteritems(base.declared_columns)) + columns

    return SortedDict(columns)

class DeclarativeColumnsMetaclass(type):
    """
    Metaclass that converts Column attributes to a dictionary called
    'base_columns', taking into account parent class 'base_columns' as well.
    """
    def __new__(cls, name, bases, attrs):
        attrs['base_columns'] = _get_declared_columns(bases, attrs)
        new_class = super(DeclarativeColumnsMetaclass,
                     cls).__new__(cls, name, bases, attrs)
        return new_class

class BaseGrid(object):
    """
    The base Grid object.

    Use this to create a Grid.

    Attributes:
        model: The model's class this grid will show. Each grid row will show information of one model instance.
    """
    _default_options = dict(datatype = 'json',
                            mtype = 'get',
                            viewrecords = True,
                            gridview = True,
                            autoencode= False,
                            height = '100%',
                            autowidth = True,
                            shrinkToFit = True,
                            rowNum = 20)

    def __init__(self, **kwargs):
        """
        Creates a Grid

        Args:
            **kwargs: All the arguments will go to the grid's ``option`` array.

        The grid's ``option`` array will be used to instantiate the jqGrid on the browser side:
        ``$("#grid").jqGrid(options)``

        If you want to pass handlers for events, such as ``loadComplete``, wrap then with ``function`` so that
        the options are rendered correctly in JavaScript. For example:

        ``grid = MyGrid(loadComplete=function('loadCompleteHandler'))``

        For more information, see the ``json_helpers`` module.
        """
        self._columns = copy.deepcopy(self.base_columns)
        self._options = BaseGrid._default_options.copy()
        self._options.update(kwargs)
        register_grid(self.__class__)

    @classmethod
    def get_grid_id(cls):
        """
        Returns the grid's class ID.

        This is done by computing a CRC32 of the class's name. Using CRC32 is not a security risk - IDs are passed
        in the HTTP anyway, so they are no secret and being able to generate them is not going to help an attacker.
        """
        return '%X' % abs(crc32(cls.__name__))

    @property
    def columns(self):
        return self._columns

    def get_options(self, override = None):
        """
        Returns the grid's options - this options will be passed to the JavaScript ``jqGrid`` function

        Args:
            override: A dictionary that overrides the options provided when the grid was initialized.

        Returns:
            A dictionary with the grid's options.

        Some fields cannot be overridden:
        - ``colNames`` are created from the grid's ``Column`` fields
        - ``colModels`` are also created from the grid's ``Column`` fields.
        - ``url`` always points to the ``djqgrid.views.query`` view with the grid's ID.
        """
        options = self._options.copy()
        if override:
            options.update(override)

        options['colNames'] = [col.title for col in self.columns.values()]
        options['colModel'] = [col.model for col in self.columns.values()]
        options['url'] = reverse(views.query, kwargs = {'grid_id': self.get_grid_id()})

        return options

    def _model_to_dict(self, model):
        """
        Takes a model and converts it to a Python dictionary that will be sent to the jqGrid.

        This is done by going over all the columns, and rendering each of them to both text and HTML. The text
        is put in the result dictionary. The result dictionary also has an ``html`` dictionary, which contains the
        HTML rendering of each column.

        This is done to solve a bug with jqGrid's inline editing, that couldn't handle HTML values of cells properly.
        So instead we use a formatter, called ``customHtmlFormatter`` (in ``djqgrid_utils.js``) that can take the value
        from the html dictionary.

        Sometimes more information is required by the JavaScript code (for example, to choose row CSS styles). It
        is possible to add additional information. The method ``_get_additional_data`` returns this additional information,
        which is put in result JSON as well.

                So, for example, a Grid with two columns will have a JSON looking likes this::
        {col1: 'col1-text',
         col2: 'col2-text',
         html: {
            'col1': 'col1-html',
            'col2': 'col2-html'
         },
         additional: { ... }
        }
        """

        result = {}
        html = {}
        for column in self.columns.values():
            title = column.title.lower()
            result[title] = column.render_text(model)
            html[title] = column.render_html(model)
        result['html'] = html

        additional = self._get_additional_data(model)
        if additional:
            result['additional'] = additional
        return result

    def _get_additional_data(self, model):
        """
        Retrieves additional data to be sent back to the client.

        Args:
            model: The model of the currently rendered row
        Returns:
            A dictionary with more data that will be sent to the client, or ``None`` if there's no such data
        """

        return None

    def _apply_sort(self, queryset, querydict):
        """
        Applys sorting on the queryset.

        jqGrid supports sorting, by passing ``sidx`` and ``sord`` in the request's query string. ``_apply_sort``
        applies this sorting on a queryset.

        Args:
            queryset: A queryset for the objects of tje grid
            querydict: The request's querydict with sidx and sord
        Returns:
            An ordered queryset.
        """

        try:
            sidx = querydict['sidx']
            if not sidx:
                sidx = self.columns.values()[0].title
            sorder = '' if querydict['sord']=='asc' else '-'
        except KeyError:
            return queryset  # No sorting applied
        for column in self.columns.values():
            if sidx.lower()==column.title.lower():
                order = sorder + column.get_sort_name()
                return queryset.order_by(order)
        raise ValueError("Can't find index field '%s'" % sidx)

    def _apply_query(self, queryset, querydict):
        """
        This function lets a Grid instance change the default query, if it's ever necessary

        Args:
            queryset: The default query (``self.model.objects``)
            querydict: The request's query string
        Returns:
            The actual queryset to use

        Override this function if the default query is not enough
        """
        return queryset

    def _get_query_results(self, querydict):
        """
        Returns a queryset to populate the grid

        Args:
            querydict: The request's query dictionary
        Returns:
            The queryset that will be used to populate the grid. Paging will be applied by the caller.
        """
        queryset = self.model.objects
        queryset = self._apply_query(queryset, querydict)
        queryset = self._apply_sort(queryset, querydict)

        return queryset

    def get_json_data(self, querydict):
        """
        Returns a JSON string with the grid's contents

        Args:
            querydict: The request's query dictionary
        Returns:
            JSON string with the grid's contents

        *DO NOT* override this method unless absolutely necessary. ``_apply_query`` and ``_get_additional_data`` should
        be overridden instead.
        """
        queryset = self._get_query_results(querydict)

        page = int(querydict.get('page', '1'))
        rows = int(querydict.get('rows', self._options.get('rownum', 20)))
        queryset = self._apply_sort(queryset, querydict)

        total_pages = (len(queryset) + rows - 1) / rows
        paginator = Paginator(queryset, rows)
        response = {'page': page,
                    'total': total_pages,
                    'records': len(queryset),
                    'rows': [self._model_to_dict(m) for m in paginator.page(page)]}
        return response
    

class Grid(six.with_metaclass(DeclarativeColumnsMetaclass, BaseGrid)):
    """
    The Grid class everybody will use.

    We use BaseGrid, and add the fields metaclass magic, as is done in the Django forms
    """




