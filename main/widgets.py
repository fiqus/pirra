from django.forms import widgets, Select
from django.forms.utils import flatatt
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.utils.safestring import mark_safe


class TextInputWithButton(widgets.TextInput):
    PLACEMENT_APPEND = 'append'
    PLACEMENT_PREPEND = 'prepend'

    btn_label = 'Go!'
    btn_type = 'submit'
    btn_placement = 'append'
    btn_attrs = None

    def __init__(self, attrs=None, btn_attrs=None):
        if btn_attrs is not None:
            self.btn_label = btn_attrs.pop('label', self.btn_label)
            self.btn_type = btn_attrs.pop('type', self.btn_type)
            self.btn_placement = btn_attrs.pop('placement', self.btn_placement)
            if self.btn_placement not in [self.PLACEMENT_APPEND, self.PLACEMENT_PREPEND]:
                self.btn_placement = self.PLACEMENT_APPEND

            self.btn_attrs = btn_attrs.copy()
        else:
            self.btn_attrs = {}

        super(TextInputWithButton, self).__init__(attrs)

    def build_btn_attrs(self, extra_attrs=None, **kwargs):
        attrs = dict(self.btn_attrs, **kwargs)
        if extra_attrs:
            attrs.update(extra_attrs)
        return attrs

    def render(self, name, value, attrs=None, btn_attrs=None, **kwargs):
        final_btn_attrs = self.build_btn_attrs(btn_attrs, type=self.btn_type)
        if 'class' not in final_btn_attrs:
            final_btn_attrs['class'] = 'btn btn-default'

        if self.btn_placement == self.PLACEMENT_APPEND:
            template = """
            <div class="input-group">
                {0}
                <span class="input-group-btn">
                    <button{1}>{2}</button>
                </span>
            </div>
            """
        else:
            template = """
            <div class="input-group">
                <span class="input-group-btn">
                    <button{1}>{2}</button>
                </span>
                {0}
            </div>
            """

        return format_html(template,
                           super(TextInputWithButton, self).render(name, value, attrs),
                           flatatt(final_btn_attrs),
                           self.btn_label,
                           )


class SelectAlicuotaIva(Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        ret = super(SelectAlicuotaIva, self).create_option(name, value, label, selected, index, subindex, attrs)
        ret["attrs"]["data-tipo_cbte"] = ",".join([str(i.tipo_comp.id) for i in
                                          self.choices.queryset.get(id=value).tipocomprobantealicuotaiva_set.all()])
        ret["attrs"]["data-porc"] = str(self.choices.queryset.get(id=value).porc) if value else ""
        return ret
