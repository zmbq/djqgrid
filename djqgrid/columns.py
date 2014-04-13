import string
from django.template import Context, Template
from django.template.loader import get_template
from json_helpers import function

__author__ = 'zmbq'

class Column(object):
    _creation_count = 0

    def __init__(self, title, model_path, **kwargs):
        self._title = title
        self._colModel = dict(kwargs)
        self._colModel['name'] = title.lower()
        if not 'formatter' in kwargs:
            self._colModel['formatter'] = function('customHtmlFormatter')
        self._count = Column._creation_count
        Column._creation_count += 1
        self._model_path = model_path

    def get_model_attr(self, attr, model):
        return reduce(getattr, attr.split('.'), model)

    def get_model_value(self, model):
        return self.get_model_attr(self._model_path, model)

    def render_text(self, model):
        return str(self.get_model_value(model))

    def render_html(self, model):
        return self.render_text(model)

    @property
    def title(self):
        """ Returns the name that goes in the colName JSON """
        return self._title

    @property
    def model(self):
        return self._colModel

    def get_sort_name(self):
        return self._model_path.replace('.', '__')

class TextColumn(Column):
    def __init__(self, title, model_path, **kwargs):
        super(TextColumn, self).__init__(title, model_path, **kwargs)
        self._model_path = model_path
        del self._colModel['formatter'] # Use the default formatter

class ClientOnlyColumn(Column):
    """ A column that is filled by the client, the server just returns it with a blank value """
    def __init__(self, title, **kwargs):
        super(ClientOnlyColumn, self).__init__(title, None, **kwargs)
        if not 'formatter' in kwargs:
            del self._colModel['formatter']

    def get_model_value(self, model):
        return ''

class TemplateColumn(Column):
    def __init__(self, title, model_path, template = None, template_name = None,**kwargs):
        super(TemplateColumn, self).__init__(title, model_path, **kwargs)
        if template:
            self._template = Template(template.strip())
        elif template_name:
            self._template = get_template(template_name)
        else:
            self._template = None # set_template may be called later

    def set_template(self, template):
        self._template = Template(template.strip())

    def fill_context(self, context, model):
        return context

    def render_html(self, model):
        if not self._template:
            raise ValueError("Template has not been set in %s" % self)
        context = Context({'model': model})
        self.fill_context(context, model)
        html = self._template.render(context = context)

        lines = html.split('\n')
        lines = [line.strip() for line in lines]
        html = string.join(lines)

        return html

class LinkColumn(TemplateColumn):
    template = """
    <a href="{{ url }}">{{ name }}</a>
    """

    def __init__(self, title, model_path, url_builder, **kwargs):
        super(LinkColumn, self).__init__(title, model_path, template=LinkColumn.template, **kwargs)
        self._url_builder = url_builder

    def fill_context(self, context, model):
        url = self._url_builder(model)
        context['url'] = url
        context['name'] = self.get_model_attr(self._model_path, model)

class CheckboxColumn(Column):
    def __init__(self, title, model_path, **kwargs):
        kwargs['formatter'] = 'checkbox'
        if 'editable' in kwargs and not 'edittype' in kwargs:
            kwargs['formatoptions'] = {'disabled': False}
            kwargs['edittype'] = 'checkbox'
            kwargs['editoptions'] = {'value': 'true:false'}
        super(CheckboxColumn, self).__init__(title, model_path, **kwargs)

    def render_text(self, model):
        text = super(CheckboxColumn, self).render_text(model)
        return text=='True'    # Turn the field into a boolean, for JavaScript

class KeyColumn(Column):
    def __init__(self, model_path, **kwargs):
        kwargs['key'] = True
        kwargs['hidden'] = True
        super(KeyColumn, self).__init__("Key", model_path, **kwargs)
