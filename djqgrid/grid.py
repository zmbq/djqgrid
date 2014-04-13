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
def get_declared_columns(bases, attrs, with_base_columns=True):
    """
    Create a list of form column instances from the passed in 'attrs', plus any
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
    'base_fields', taking into account parent class 'base_fields' as well.
    """
    def __new__(cls, name, bases, attrs):
        attrs['base_columns'] = get_declared_columns(bases, attrs)
        new_class = super(DeclarativeColumnsMetaclass,
                     cls).__new__(cls, name, bases, attrs)
        return new_class

class BaseGrid(object):
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
        self._columns = copy.deepcopy(self.base_columns)
        self._options = BaseGrid._default_options.copy()
        self._options.update(kwargs)
        register_grid(self.__class__)

    @classmethod
    def get_grid_id(cls):
        return '%X' % abs(crc32(cls.__name__))

    @property
    def columns(self):
        return self._columns

    def get_options(self, override = None):
        options = self._options.copy()
        if override:
            options.update(override)

        options['colNames'] = [col.title for col in self.columns.values()]
        options['colModel'] = [col.model for col in self.columns.values()]
        options['url'] = reverse(views.query, kwargs = {'grid_id': self.get_grid_id()})

        return options

    def model_to_dict(self, model):
        result = {}
        html = {}
        for column in self.columns.values():
            title = column.title.lower()
            result[title] = column.render_text(model)
            html[title] = column.render_html(model)
        result['html'] = html

        additional = self.get_additional_data(model)
        if additional:
            result['additional'] = additional
        return result

    def get_additional_data(self, model):
        return None

    def apply_sort(self, queryset, querydict):
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

    def apply_query(self, queryset, querydict):
        return queryset

    def get_query_results(self, querydict):
        queryset = self.model.objects
        queryset = self.apply_query(queryset, querydict)
        queryset = self.apply_sort(queryset, querydict)

        return queryset

    def get_json_data(self, querydict):
        queryset = self.get_query_results(querydict)

        page = int(querydict.get('page', '1'))
        rows = int(querydict.get('rows', self._options.get('rownum', 20)))
        queryset = self.apply_sort(queryset, querydict)

        total_pages = (len(queryset) + rows - 1) / rows
        paginator = Paginator(queryset, rows)
        response = {'page': page,
                    'total': total_pages,
                    'records': len(queryset),
                    'rows': [self.model_to_dict(m) for m in paginator.page(page)]}
        return response
    

class Grid(six.with_metaclass(DeclarativeColumnsMetaclass, BaseGrid)):
    """ Adds the fields metaclass magic, as is done in the Django forms """




