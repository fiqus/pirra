from django_tables2 import LinkColumn, Column

class EditColumn(LinkColumn):
    def __init__(self, *args, **kwargs):
        if kwargs.get('attrs', None) is None:
            kwargs['attrs'] = {
                "a": {
                    "class": "btn btn-secondary btn-sm"
                }
            }
        super(EditColumn, self).__init__(*args, **kwargs)
        
    def render(self, record, value):
        return super(EditColumn, self).render(record, "Editar")


class DeleteColumn(LinkColumn):
    def __init__(self, *args, **kwargs):
        if kwargs.get('attrs', None) is None:
            kwargs['attrs'] = {
                "a": {
                    "class": "btn btn-outline btn-danger btn-sm"
                }
            }
        super(DeleteColumn, self).__init__(*args, **kwargs)

    def render(self, record, value):
        return super(DeleteColumn, self).render(record, "Eliminar")


class MoneyColumn(Column):
    def render(self, value):
        return "${0:,.2f}".format(value)
