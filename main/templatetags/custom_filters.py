import re
from django.conf import settings
from decimal import Decimal
from django.utils.encoding import force_text
from django.utils.formats import number_format
from django.template.defaultfilters import register


def money(value, use_l10n=True):
    """
    Separator '.'
    Converts an integer to a string containing commas every three digits.
    For example, 3000 becomes '3.000' and 45000 becomes '45.000'.
    """
    if settings.USE_L10N and use_l10n:
        try:
            if not isinstance(value, (float, Decimal)):
                value = int(value)
        except (TypeError, ValueError):
            return money(value, False)
        else:
            return number_format(value, force_grouping=True)
    orig = force_text(value)
    new = re.sub("^(-?\d+)(\d{3})", '\g<1>.\g<2>', orig)
    if orig == new:
        return new
    else:
        return money(new, use_l10n)

register.filter('money', money)