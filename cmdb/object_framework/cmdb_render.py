"""OBJECT RENDER
"""
from cmdb.utils.error import CMDBError
from cmdb.object_framework import CmdbObject, CmdbType, CmdbFieldType
from cmdb.utils.logger import get_logger

LOGGER = get_logger()


class CmdbRender:

    VIEW_MODE = 0
    EDIT_MODE = 1
    DEFAULT_MODE = VIEW_MODE

    POSSIBLE_INPUT_FORM_TYPES = ['text', 'password', 'email', 'tel']
    POSSIBLE_RENDER_MODES = [VIEW_MODE, EDIT_MODE]

    def __init__(self, object_instance: CmdbObject, type_instance: CmdbType, mode: int=DEFAULT_MODE):
        self.object_instance = object_instance
        self.type_instance = type_instance
        if mode not in CmdbRender.POSSIBLE_RENDER_MODES:
            raise RenderModeError()
        self.mode = mode

    def get_mode(self):
        return self.mode

    @property
    def object_instance(self) -> CmdbObject:
        return self._object_instance

    @object_instance.setter
    def object_instance(self, object_instance: CmdbObject):
        if not isinstance(object_instance, CmdbObject):
            raise ObjectInstanceError()
        self._object_instance = object_instance

    @property
    def type_instance(self) -> CmdbType:
        return self._type_instance

    @type_instance.setter
    def type_instance(self, type_instance: CmdbType):
        if not isinstance(type_instance, CmdbType):
            raise ObjectInstanceError()
        self._type_instance = type_instance

    def get_field(self, name):
        try:
            field = self.type_instance.get_field(name)
            LOGGER.debug(field)
            object_value = self.object_instance.get_value(name)
            if object_value is not None or object_value != '':
                field.set_value(object_value)
        except CMDBError:
            # TODO: Error handling
            return None
        return field
    """
    def render_html_object(self, mode: int=VIEW_MODE):
        
        html_code = self.render_html_form()
        self.mode = CmdbRender.DEFAULT_MODE
        return html_code

    def render_html_form(self):
        type_sections = self.type_instance.get_sections()
        html_code = ""

        for section in type_sections:
            html_code += '<h2>{}</h2><hr />'.format(section['label'])
            for field_name in section['fields']:
                try:
                    field_typ = self.type_instance.get_field(name=field_name)
                    object_field_value = self.object_instance.get_value(field_typ.get_name())
                    # override default type values with database entries
                    if object_field_value is not None and object_field_value != "":
                        field_typ.set_value(object_field_value)
                    html_code += self._render_html_input(field_typ)
                except CMDBError as e:
                    LOGGER.info(e.message)
                    continue

        return html_code

    def _render_html_input(self, field_type: CmdbFieldType) -> str:
        html_type = field_type.get_sub_type()
        if html_type not in CmdbRender.POSSIBLE_INPUT_FORM_TYPES:
            raise InvalidHtmlInputType(html_type)

        render_output = '{{ input('+field_type.to_json()+')}}'
        LOGGER.debug(render_output)
        return render_output

    def _render_html_text(self, field_type: CmdbFieldType) -> str:

        render_text_output = ''
        render_text_output += '<div class="form-group">'
        render_text_output += '<label for="{0}">'.format(field_type.get_name())
        render_text_output += str(field_type.label)
        render_text_output += '</label>'
        render_text_output += '<input name="{0}" class="form-control" type="{1}" '.format(field_type.get_name(), field_type.get_sub_type())
        if field_type.get_value() is not None or field_type.get_value() != "":
            render_text_output += ' value="{0}" '.format(field_type.get_value())
        if self.mode == CmdbRender.VIEW_MODE:
            render_text_output += ' readonly '
        render_text_output += ' />'

        render_text_output += '</div>'
        return render_text_output
    """


class RenderModeError(CMDBError):
    def __init__(self):
        super(CMDBError, self)
        self.message = "No possible render mode"


class ObjectInstanceError(CMDBError):
    def __init__(self):
        super(CMDBError, self)
        self.message = "Wrong instance"


class InvalidHtmlInputType(CMDBError):
    def __init__(self, html_type):
        super(CMDBError, self)
        self.message = "Input type {} is not supported".format(html_type)