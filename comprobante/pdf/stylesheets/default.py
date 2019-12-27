from reportlab.lib.colors import Color
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.fonts import tt2ps
from reportlab.lib.styles import StyleSheet1, ParagraphStyle

_baseFontName = "Helvetica"
_baseFontNameB = tt2ps(_baseFontName, 1, 0)
_baseFontNameI = tt2ps(_baseFontName, 0, 1)
_baseFontNameBI = tt2ps(_baseFontName, 1, 1)


def get_default_stylesheet():
    """Returns a stylesheet object"""
    stylesheet = StyleSheet1()

    stylesheet.add(ParagraphStyle(name='Normal',
                                  fontSize=10,
                                  leading=12,
                                  letterSpacing='normal',
                                  textColor=Color(0,0,0))
                   )

    stylesheet.add(ParagraphStyle(name='BodyText',
                                  parent=stylesheet['Normal'],
                                  spaceBefore=6)
                   )
    stylesheet.add(ParagraphStyle(name='Italic',
                                  parent=stylesheet['BodyText'],
                                  fontName=_baseFontNameI)
                   )

    stylesheet.add(ParagraphStyle(name='Heading1',
                                  parent=stylesheet['Normal'],
                                  fontName=_baseFontNameB,
                                  fontSize=18,
                                  leading=22,
                                  spaceAfter=6),
                   alias='h1')

    ##
    stylesheet.add(ParagraphStyle(name='Title',
                                  parent=stylesheet['Normal'],
                                  fontName=_baseFontNameB,
                                  fontSize=18,
                                  leading=22,
                                  alignment=TA_CENTER,
                                  spaceAfter=6),
                   alias='title')

    stylesheet.add(ParagraphStyle(name='Heading2',
                                  parent=stylesheet['Normal'],
                                  fontName=_baseFontNameB,
                                  fontSize=14,
                                  leading=18,
                                  spaceBefore=12,
                                  spaceAfter=6),
                   alias='h2')

    stylesheet.add(ParagraphStyle(name='Heading3',
                                  parent=stylesheet['Normal'],
                                  fontName=_baseFontNameBI,
                                  fontSize=12,
                                  leading=14,
                                  spaceBefore=12,
                                  spaceAfter=6),
                   alias='h3')

    stylesheet.add(ParagraphStyle(name='Heading4',
                                  parent=stylesheet['Normal'],
                                  fontName=_baseFontNameBI,
                                  fontSize=10,
                                  leading=12,
                                  spaceBefore=10,
                                  spaceAfter=4),
                   alias='h4')

    stylesheet.add(ParagraphStyle(name='Heading5',
                                  parent=stylesheet['Normal'],
                                  fontName=_baseFontNameB,
                                  fontSize=9,
                                  leading=10.8,
                                  spaceBefore=8,
                                  spaceAfter=4),
                   alias='h5')

    stylesheet.add(ParagraphStyle(name='Heading6',
                                  parent=stylesheet['Normal'],
                                  fontName=_baseFontNameB,
                                  fontSize=7,
                                  leading=8.4,
                                  spaceBefore=6,
                                  spaceAfter=2),
                   alias='h6')

    stylesheet.add(ParagraphStyle(name='Bullet',
                                  parent=stylesheet['Normal'],
                                  firstLineIndent=0,
                                  spaceBefore=3),
                   alias='bu')

    stylesheet.add(ParagraphStyle(name='Definition',
                                  parent=stylesheet['Normal'],
                                  firstLineIndent=0,
                                  leftIndent=36,
                                  bulletIndent=0,
                                  spaceBefore=6,
                                  bulletFontName=_baseFontNameBI),
                   alias='df')

    ##
    stylesheet.add(ParagraphStyle(name='header_normal',
                                  parent=stylesheet['Normal'],
                                  alignment=TA_LEFT,
                                  fontSize=9,
                                  leftIndent=10,
                                  rightIndent=10))

    ##
    stylesheet.add(ParagraphStyle(name='header_company_name',
                                  parent=stylesheet['header_normal'],
                                  alignment=TA_CENTER,
                                  fontName=_baseFontNameB,
                                  fontSize=8))

    stylesheet.add(ParagraphStyle(name='header_company_name_large',
                                  parent=stylesheet['header_normal'],
                                  alignment=TA_CENTER,
                                  fontName=_baseFontNameB,
                                  fontSize=16,
                                  leading=18))
    ##
    stylesheet.add(ParagraphStyle(name='header_big',
                                  parent=stylesheet['header_normal'],
                                  fontSize=16,
                                  leading=18,
                                  fontName=_baseFontNameB))
    ##
    stylesheet.add(ParagraphStyle(name='header_medium',
                                  parent=stylesheet['header_normal'],
                                  fontSize=10,
                                  fontName=_baseFontNameB))

    stylesheet.add(ParagraphStyle(name='header_small',
                                  parent=stylesheet['header_normal'],
                                  fontSize=8, leading=10))

    stylesheet.add(ParagraphStyle(name='header_letter',
                                  parent=stylesheet['header_normal'],
                                  alignment=TA_CENTER,
                                  fontSize=16,
                                  leading=20,
                                  fontName=_baseFontNameB,
                                  borderColor='#000',
                                  spaceBefore=0,
                                  spaceAfter=0))

    stylesheet.add(ParagraphStyle(name='header_letter_xxs',
                                  parent=stylesheet['header_letter'],
                                  fontSize=4,
                                  leading=8,
                                  alignment=TA_CENTER, ))

    stylesheet.add(ParagraphStyle(name='header_letter_xs',
                                  parent=stylesheet['header_letter'],
                                  fontSize=7,
                                  leading=10,
                                  alignment=TA_CENTER, ))

    stylesheet.add(ParagraphStyle(name='header_small_center',
                                  parent=stylesheet['header_small'],
                                  alignment=TA_CENTER, ))

    stylesheet.add(ParagraphStyle(name='legend_xs',
                                  parent=stylesheet['header_small'],
                                  alignment=TA_CENTER,
                                  fontSize=6))

    stylesheet.add(ParagraphStyle(name='detail_left',
                                  parent=stylesheet['header_small'],
                                  alignment=TA_LEFT,
                                  leftIndent=0,
                                  fontSize=7,
                                  rightIndent=4))

    stylesheet.add(ParagraphStyle(name='detail_right',
                              parent=stylesheet['detail_left'],
                              alignment=TA_RIGHT, ))

    stylesheet.add(ParagraphStyle(name='detail_header_left',
                                  parent=stylesheet['detail_left'],
                                  fontName=_baseFontNameB,
                                  alignment=TA_LEFT))

    stylesheet.add(ParagraphStyle(name='detail_header_right',
                                  parent=stylesheet['detail_header_left'],
                                  alignment=TA_RIGHT, ))

    return stylesheet
