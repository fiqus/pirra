from contextlib import contextmanager

from reportlab.pdfgen import canvas


class Base(object):
    @contextmanager
    def canvas_state(self):
        self.canvas.saveState()
        yield self.canvas
        self.canvas.restoreState()

    def _debug_rect(self, x1, y1, x2, y2):
        if self.debug:
            with self.canvas_state() as c:
                c.setStrokeColorRGB(0, 1, 0, .25)
                c.setFillColorRGB(1, 1, 0, .1)
                c.rect(x1, y1, x2 - x1, y2 - y1, stroke=1, fill=1)

    def __init__(self,
                 filename,
                 pagesize,
                 es_impresion,
                 margin_left=30,
                 margin_right=30,
                 margin_top=30,
                 margin_bottom=30,

                 debug=False):

        self.debug = debug
        self.canvas = canvas.Canvas(filename, pagesize)
        self.width, self.height = pagesize
        self.margin_left = margin_left
        self.margin_right = margin_right
        self.margin_top = margin_top
        self.margin_bottom = margin_bottom

        self.detail_item_padding = 6

        self.usable_width = self.width - self.margin_left - self.margin_right
        self.usable_height = self.height - self.margin_top - self.margin_bottom

        self.header_letter_items = self.gen_header_letter() if hasattr(self, "gen_header_letter") else []
        self.header_center_letter_size = max([i.width for i in self.header_letter_items])
        self.header_col_width = self.usable_width / 2 - self.header_center_letter_size / 2

        self.header1_items = self.gen_header1() if hasattr(self, "gen_header1") else []
        self.header2_items = self.gen_header2(1) if hasattr(self, "gen_header2") else []
        if self.cbte.empresa.imprimir_comp_triplicado and es_impresion:
            self.header2_items_2nd_copy = self.gen_header2(2) if hasattr(self, "gen_header2") else []
            self.header2_items_3rd_copy = self.gen_header2(3) if hasattr(self, "gen_header2") else []

        self.header_row2_items = self.gen_header_row2() if hasattr(self, "gen_header_row2") else []
        self.header_row3_items = self.gen_header_row3() if hasattr(self, "gen_header_row3") else []

        self.footer_legend_items = self.gen_footer_legend() if hasattr(self, "gen_footer_legend") else []
        self.footer_col1_items = self.gen_footer_col1() if hasattr(self, "gen_footer_col1") else []
        self.footer_col2_items = self.gen_footer_col2() if hasattr(self, "gen_footer_col2") else []

        self.footer_legend_last_page_items = self.gen_footer_legend_last_page() if hasattr(self,
                                                                                           "gen_footer_legend_last_page") else []
        self.footer_col1_last_page_items = self.gen_footer_col1_last_page() if hasattr(self,
                                                                                       "gen_footer_col1_last_page") else []
        self.footer_col2_last_page_items = self.gen_footer_col2_last_page() if hasattr(self,
                                                                                       "gen_footer_col2_last_page") else []
        self.footer_observaciones = self.gen_footer_observaciones() if hasattr(self, "gen_footer_observaciones") else []

        self.header_height = max(sum(i.height for i in self.header1_items),
                                 sum(i.height for i in self.header2_items)) + \
                             sum(i.height for i in self.header_row2_items) + \
                             sum(i.height for i in self.header_row3_items)

        self.footer_height = max(sum(i.height for i in self.footer_col1_items),
                                 sum(i.height for i in self.footer_col2_items)) + \
                             sum(i.height for i in self.footer_legend_items)

        self.footer_height_last_page = max(sum(i.height for i in self.footer_col1_last_page_items),
                                           sum(i.height for i in self.footer_col2_last_page_items)) + \
                                       sum(i.height for i in self.footer_legend_last_page_items) + \
                                       sum(i.height for i in self.footer_observaciones)

        self.detail_height = self.usable_height - self.footer_height - self.header_height
        self.detail_height_last_page = self.usable_height - self.footer_height_last_page - self.header_height

        self.detail_header_items = self.gen_detail_header() if hasattr(self, "gen_detail_header") else []
        self.detail_items = self.gen_detail_items() if hasattr(self, "gen_detail_items") else []

        self.paged_detail_items = self.split_detail_items()

    def draw_item(self, item, x, y):
        item.drawOn(self.canvas, x, y)
        if self.debug:
            self._debug_rect(x, y, x + item.width, y + item.height)

    def draw_header(self, copy_number):
        header_1_height = sum(i.height for i in self.header1_items)
        header_2_height = sum(i.height for i in self.header2_items)

        header_letter_height = sum(i.height for i in self.header_letter_items)

        self.rect(self.width / 2 - self.header_center_letter_size / 2,
                  self.height - self.margin_top - self.header_center_letter_size,
                  self.header_center_letter_size,
                  self.header_center_letter_size
                  )

        x = self.width / 2 - self.header_center_letter_size / 2
        y = self.height - self.margin_top - self.header_center_letter_size / 2 + header_letter_height / 2
        for item in self.header_letter_items:
            y -= item.height
            self.draw_item(item, x, y)

        x = self.margin_left
        y = self.height - self.margin_top
        if header_1_height < header_2_height: y -= (header_2_height - header_1_height)
        for item in self.header1_items:
            y -= item.height
            self.draw_item(item, x, y)

        x = self.usable_width - self.header_col_width + self.margin_left
        y = self.height - self.margin_top
        if header_2_height < header_1_height: y -= (header_1_height - header_2_height)
        if copy_number == 1:
            header = self.header2_items
        if copy_number == 2:
            header = self.header2_items_2nd_copy
        elif copy_number == 3:
            header = self.header2_items_3rd_copy

        for item in header:
            y -= item.height
            self.draw_item(item, x, y)

        x = self.margin_left
        y = self.height - self.margin_top - max(header_1_height, header_2_height)

        self.line(self.width / 2, self.height - self.margin_top - self.header_center_letter_size, self.width / 2, y)
        self.line(self.margin_left, y, self.width - self.margin_right, y)

        for item in self.header_row2_items:
            y -= item.height
            self.draw_item(item, x, y)

        self.line(self.margin_left, y, self.width - self.margin_right, y)

        for item in self.header_row3_items:
            y -= item.height
            self.draw_item(item, x, y)

        self.line(self.margin_left, y, self.width - self.margin_right, y)

    def draw_footer(self, last_page=False):

        x = self.margin_left
        y = self.margin_bottom

        col1_items = self.footer_col1_last_page_items if last_page else self.footer_col1_items
        col2_items = self.footer_col2_last_page_items if last_page else self.footer_col2_items
        legend_items = self.footer_legend_last_page_items if last_page else self.footer_legend_items

        footer1_height = sum(i.height for i in col1_items)
        footer2_height = sum(i.height for i in col2_items)

        for item in legend_items[::-1]:
            self.draw_item(item, x, y)
            y += item.height

        oldy = y

        if footer1_height < footer2_height:
            y += (footer2_height - footer2_height) / 2
        for item in col1_items[::-1]:
            self.draw_item(item, x, y)
            y += item.height

        y = oldy
        x = self.margin_left + self.usable_width / 2
        if footer2_height < footer1_height:
            y += (footer1_height - footer2_height) / 2

        for item in col2_items[::-1]:
            self.draw_item(item, x, y)
            y += item.height

        y = oldy + max(footer1_height, footer2_height)
        self.line(self.margin_left, y, self.width - self.margin_right, y)

        x = self.margin_left
        if last_page:
            for item in self.footer_observaciones[::-1]:
                self.draw_item(item, x, y)
                y += item.height

    def split_detail_items(self):
        avail_height = self.detail_height - max([i.height for i in self.detail_header_items]) - self.detail_item_padding
        avail_height_last_page = self.detail_height_last_page - max(
            [i.height for i in self.detail_header_items]) - self.detail_item_padding

        items = self.detail_items[::-1]
        page_avail_height = avail_height
        last_page_avail_height = avail_height_last_page
        pages = []
        curr_page = []

        while items:
            item = items.pop()
            item_height = max([i.height for i in item]) + self.detail_item_padding

            if item_height > last_page_avail_height:
                if sum([max([i.height for i in item]) + self.detail_item_padding for i in items]) < page_avail_height:
                    pages.append(curr_page)
                    curr_page = []
                    page_avail_height = avail_height
                    last_page_avail_height = avail_height_last_page

            if item_height > page_avail_height:
                pages.append(curr_page)
                curr_page = []
                page_avail_height = avail_height
                last_page_avail_height = avail_height_last_page

            curr_page.append(item)
            page_avail_height -= item_height
            last_page_avail_height -= item_height

        if curr_page:
            pages.append(curr_page)

        return pages

    def draw_detail(self, items):
        self._debug_rect(self.margin_left, self.height - self.margin_top - self.header_height,
                         self.width - self.margin_right, self.margin_bottom + self.footer_height)

        x = self.margin_left
        y = self.height - self.margin_top - self.header_height - self.detail_item_padding
        head_height = max([i.height for i in self.detail_header_items])
        y -= head_height
        self.bg_rect(x, y - self.detail_item_padding / 2, self.usable_width,
                     head_height + self.detail_item_padding * 1.5, True)

        for item in self.detail_header_items:
            self.draw_item(item, x, y)
            x += item.width

        for n, row in enumerate(items):
            max_y = max([i.height for i in row])
            y -= max_y + self.detail_item_padding
            x = self.margin_left
            if n % 2: self.bg_rect(x, y - self.detail_item_padding / 2, self.usable_width,
                                   max_y + self.detail_item_padding)
            for item in row:
                self.draw_item(item, x, y + max_y - item.height)
                x += item.width

    def gen_pdf(self, es_impresion):
        self.drawn_items = 0
        copies = 3 if self.cbte.empresa.imprimir_comp_triplicado and es_impresion else 1
        for i in range(copies):
            self.drawn_items = 0
            for n, items in enumerate(self.paged_detail_items):
                self.page_number = n + 1
                self.draw_detail(items)
                self.drawn_items += len(items)
                self.rect(self.margin_left, self.margin_bottom, self.usable_width, self.usable_height)
                self.draw_header(i+1)
                self.draw_footer(n == len(self.paged_detail_items) - 1)
                self.canvas.showPage()

        self.canvas.save()

    def rect(self, x1, y1, x2, y2):
        with self.canvas_state() as c:
            c.setStrokeColorRGB(0, 0, 0, 1)
            c.roundRect(x1, y1, x2, y2, 0, stroke=1, fill=0)

    def bg_rect(self, x, y, w, h, strong=False):
        with self.canvas_state() as c:
            if strong:
                c.setFillColorRGB(.85, .85, .85, 1)
            else:
                c.setFillColorRGB(.95, .95, .95, 1)
            c.rect(x, y, w, h, stroke=0, fill=1)

    def line(self, x1, y1, x2, y2):
        with self.canvas_state() as c:
            c.setStrokeColorRGB(0, 0, 0, 1)
            p = c.beginPath()
            p.moveTo(x1, y1)
            p.lineTo(x2, y2)
            c.drawPath(p)