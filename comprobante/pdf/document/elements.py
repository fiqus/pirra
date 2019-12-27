from reportlab.platypus.flowables import Image
from reportlab.platypus.paragraph import Paragraph
from reportlab.platypus.tables import Table


class CenterRestrictImage(Image):
    def __init__(self, filename, width, height, margin=0, kind='direct', mask="auto", lazy=1):
        Image.__init__(self, filename, width=None, height=None, kind=kind, mask=mask, lazy=lazy)
        self.r_width = width
        self.r_height = height
        self._restrictSize(self.r_width - margin * 2, self.r_height)

    @property
    def width(self):
        return self.r_width

    @property
    def height(self):
        return self.r_height

    def drawOn(self, canvas, x, y, _sW=0):
        x += self.r_width / 2 - self.drawWidth / 2
        y += self.r_height / 2 - self.drawHeight / 2
        Image.drawOn(self, canvas, x, y, _sW=_sW)


class RestrictParagraph(Paragraph):
    def __init__(self, text, width, height, style):
        Paragraph.__init__(self, text, style)
        self.wrap(width, height)


class PageCounterParagraph(RestrictParagraph):
    def __init__(self, sample_text, text_getter, width, height, style):
        self.text_getter = text_getter
        self.width = width
        self.height = height
        self.style = style
        RestrictParagraph.__init__(self, sample_text, width, height, style)

    def drawOn(self, *args, **kwargs):
        RestrictParagraph.__init__(self, self.text_getter(), self.width, self.height, self.style)
        RestrictParagraph.drawOn(self, *args, **kwargs)

class RestrictTable(Table):
    def __init__(self, data, width, height, cust_data_function=None, colWidths=None, rowHeights=None, style=None,
                 repeatRows=0, repeatCols=0, splitByRow=1, emptyTableAction=None, ident=None,
                 hAlign=None, vAlign=None, normalizedData=0, cellStyles=None, rowSplitRange=None,
                 spaceBefore=None, spaceAfter=None):

        self.cust_data_function = cust_data_function
        Table.__init__(self, data, colWidths, rowHeights, style,
                       repeatRows, repeatCols, splitByRow, emptyTableAction, ident,
                       hAlign, vAlign, normalizedData, cellStyles, rowSplitRange,
                       spaceBefore, spaceAfter)
        self.wrap(width, height)

    def drawOn(self, *args, **kwargs):
        if self.cust_data_function:
            self._cellvalues = self.cust_data_function()
        Table.drawOn(self, *args, **kwargs)

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height


class VSpace(object):
    def __init__(self, space=4):
        self.height = space
        self.width = 10

    def drawOn(self, *args, **kwargs):
        pass