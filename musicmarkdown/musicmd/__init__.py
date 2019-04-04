import json
import re
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
from time import sleep
import os
from pkg_resources import resource_string
import logging

logger = logging.getLogger(__name__)
log = logger.warning

class Grid:
    """
    The markdown document object.
    It is the root of the abstrac syntax tree for the music grid.

    Its to_html() method allows to compile the tree in HTML format.
    """
    def __init__(self):
        self.tree = []
        self.gridRows = []
        self.debug = []

    @staticmethod
    def parse_section(text):
        sec = '<section class="tune-section">{t}</section>'
        return sec.format(t=text)

    html = {
        "title": "<h1>{t}</h1>",
        "subtitle": "<h2>{t}</h2>",
        "author": '<p class="author">{t}</p>',
        "copyright": '<div class="footer">®{t}</div>'
    }
    info = {
        "title": None,
        "subtitle": None,
        "author": None,
        "copyright": None
    }

    def to_html(self, live_server_addr=None):
        if live_server_addr is not None:
            # meta_refresh = '<meta http-equiv="refresh" content="1">'
            script_refresh = resource_string('musicmd', 'resources/musicgrid.js').decode()
            jscript = '<script type = "text/javascript" >\n' \
                           f'var server_address = "{live_server_addr}"\n' \
                           f'{script_refresh}\n</script>\n'
        else:
            jscript = ''


        css = resource_string('musicmd', 'resources/musicgrid.css').decode()

        self.html["head"] = '<!DOCTYPE html>\n'\
                            '<html lang="en" dir="ltr">\n'\
                            '<head>\n' \
                            '<meta charset="utf-8">' \
                            '<style>' \
                            f'{css}' \
                            '</style>' \
                            '</head>' \
                            '<body>' \
                            '<div class="page">'

        self.html["tail"] = f'</div>\n{jscript}\n</body>\n</html>'

        tag = self.html
        out_html = [tag["head"], '<div class="header">']
        # header
        for key, val in self.info.items():
            if (key != "copyright") and val:
                out_html.append(tag[key].format(t=val))
        out_html.append('</div>')

        # Elements
        for item in self.tree:
            out_html.append(item.to_html())

        # copyright
        if self.info["copyright"]:
            out_html.append(tag["copyright"].format(t=self.info["copyright"]))
        out_html.append(tag["tail"])

        return '\n'.join(out_html)

    def __repr__(self):
        d = str(self.info)
        d += '\n\n'
        d += ">>>CONTENT\n"
        d += '\n'.join([str(x) for x in self.tree])
        d += '\n\n'
        d += ">>>DEBUG\n"
        d += '\n'.join(self.debug)
        return d


class Element:
    """
    An leaf of the abstract syntax tree.
    """
    tag_start = ""
    rep_tag = 'Element'
    html_text = ''

    def to_html(self):
        if self.tag_start:
            tag_end = '</' + self.tag_start.split(' ')[0][1:] + '>'
        else:
            tag_end = ''
        return ''.join([self.tag_start, self.html_text, tag_end])
        # try:
        #     return ''.join([self.tag_start, self.html_text, tag_end])
        # except Exception():
        #     log("ERROR", self.tag_start, self.html_text)

    def __repr__(self):
        return f"{self.rep_tag}({self.html_text})"


class ElementGroup:
    """
    An node of the abstract syntax tree that can have children elements.
    """
    tag_start = ''
    rep_tag = "ElementGroup"

    def __init__(self):
        self.children = []
        self.html_text = ''

    def to_html(self):
        tag_end = '</' + self.tag_start.split(' ')[0][1:] + '>'
        out = []
        for child in self.children:
            if child is not None:
                out.append('\t' + child.to_html())

        self.html_text = '\n'.join(out)
        # try:
        #     #             assert(all([x is not None for x in out]))
        #     self.html_text = '\n'.join(out)
        # except:
        #     log("ERROR", type(self), out)
        #     raise
        return '\n'.join([self.tag_start, self.html_text, tag_end])

    def get_child(self, num):
        return self.children[num]

    def append(self, child):
        self.children.append(child)

    def __repr__(self):
        return str(self.rep_tag) + '(' + ', '.join([x.__repr__() for x in self.children]) + ')'


class BarBlock(ElementGroup):
    rep_tag = "BarBlock"

    def __init__(self, size=''):
        self.size = size
        self.case = None
        self.bar = Bar()

    @property
    def tag_start(self):
        return f'<div class="bar-block {self.size}">'

    @property
    def children(self):
        return [self.case, self.bar]


class Bar(ElementGroup):
    tag_start = '<div class="bar">'
    rep_tag = "Bar"

    def __init__(self):
        super().__init__()
        self.chordBlock = None

    def append(self, child):
        if isinstance(child, Chord):
            if self.chordBlock is None:
                self.chordBlock = ChordBlock()
                self.children.append(self.chordBlock)
            self.chordBlock.append(child)
        else:
            super().append(child)


class ChordBlock(ElementGroup):
    tag_start = '<div class="chords">'
    rep_tag = "ChordBlock"


class Chord(Element):
    tag_start = '<div class="chord">'
    rep_tag = "Chord"

    def __init__(self, text):
        super().__init__()
        self.html_text = text


class EmptyChord(Chord):
    tag_start = '<div class="chord">'
    rep_tag = "Chord"

    def __init__(self):
        super().__init__('')


class Case(Element):
    rep_tag = "Case"

    def __init__(self, text):
        super().__init__()
        if re.match(r'[12]\.*', text):
            self.tag_start = '<div class="case case-start">'
        else:
            self.tag_start = '<div class="case">'
        self.html_text = text


class Barline(Element):
    rep_tag = "Barline"

    def __init__(self, kind=''):
        self.tag_start = f'<div class="barline {kind}">'


class Pause(Element):
    rep_tag = "Pause"
    tag_start = '<div class="pause">'

    def __init__(self, n):
        self.html_text = f'<div class="pause-line"></div><div class="pause-number"> {n} </div><div ' \
                         f'class="pause-line"></div> '


class Pentagram(Element):
    rep_tag = "Pentagram"
    tag_start = '<div class="pentagram">'

    def __init__(self):
        self.html_text = ''.join(['<div class="pentagram-line"></div>'] * 5)


class Time(Element):
    rep_tag = "Time"
    tag_start = '<div class="time">'

    def __init__(self, divisions, value):
        self.html_text = f'<span>{divisions}</span><span>{value}</span>'


class Repeat(Element):
    rep_tag = "Repeat"
    tag_start = '<div class="repeat">'

    def __init__(self):
        self.html_text = ':'


class SameMeasure(Chord):
    rep_tag = "%"
    tag_start = '<div class="chord same-bar">'

    def __init__(self):
        self.html_text = '%'

class GridRow(ElementGroup):
    # A row consists of may bars
    tag_start = '<div class="grid-row">'
    rep_tag = "Row"

    def __init__(self):
        super(GridRow, self).__init__()

class Vspace(Element):
    def __init__(self, kind=''):
        if kind:
            self.tag_start = f'<div class="vspace-{kind}">'
        else:
            self.tag_start = f'<div class="vspace">'
        self.html_text = ''


class SectionName(Element):
    tag_start = '<p class="name">'
    rep_tag = "Name"

    def __init__(self, name):
        self.html_text = name


class SectionRepetitions(Element):
    tag_start = '<p class="repeats">'
    rep_tag = "Rep"

    def __init__(self, num):
        self.html_text = "x" + str(num)


class Rarrow(Element):
    tag_start = '<p class="debug arrow">'
    rep_tag = "->"

    def __init__(self):
        self.html_text = "&rarr;" # "&#8680;"


class SectionComment(Element):
    tag_start = '<span class="note">'
    rep_tag = "Comment"

    def __init__(self, text):
        self.html_text = text


class NotRecognized(Element):
    tag_start = '<span class="error">'
    rep_tag = "Error"

    def __init__(self, text):
        self.html_text = f'SyntaxError: "{text}"'


class Section(ElementGroup):
    rep_tag = "Section"
    tag_start = '<section class="tune-section">'


class BarlineSimple(Element):
    tag_start = '<section class="tune-section">'


class GridProcessor:
    """
    The Music Grid Markdown parser.

    Parse a music grid markdown script and return a Grid object
    """
    re = {
        "title": re.compile(r"^#([^#]+)$"),
        "subtitle": re.compile(r"^#{2}([^#]+)$"),
        "author": re.compile(r"^(?i:author:)(.+)$"),
        "copyright": re.compile(r"^(?i:copyright:)(.+)$"),
        "vspace": re.compile(r"^%vspace-?(.*)%$"),
        "tag": re.compile(r"^(<.*>)$"),
        "comment": re.compile(r"^(.*)(?=(//))(.*)$"),
        "sections-line": re.compile(r"^\s*-(.*)$"),
        "grid-row": re.compile(r"^(?:(?P<num>\d)/(?P<den>\d))?\s*([|\[\]].*[|\[\]])$"),
        "section": {
            "name": re.compile(r"\[(?P<name>.*?)\](?:\s*x(?P<rep>\d+))?"),
            "rarrow": re.compile(r"->"),
        }
    }

    @staticmethod
    def parse_row(text):
        measures = re.findall(r"(?:\d/\d\s+)?[|\[\]][^|\[\]]*", text)
        measures[-2] += measures[-1]
        measures.pop(-1)
        out = []
        for measure in measures:
            re_case = re.compile(r'(\(.*?\))')  # split case test in brackets, where spaces should be keept
            temp = re.split(re_case, measure)
            tokens = []
            bb = BarBlock()
            for s in temp:
                s = s.strip()
                if re_case.match(s) is None:
                    tokens += re.split('\s+', s)  # split by spaces
                else:
                    tokens.append(s)
            #             tokens = [x for x in tokens if x]
            for tk in tokens:
                if tk == '':
                    continue
                m_time = re.match(r"(\d)/(\d)", tk)
                m_case = re_case.match(tk)
                m_pause = re.match(r'-(\d+)-', tk)
                m_penta = re.match(r'==+', tk)
                m_same = re.match(r'%', tk)
                m_size = re.match(r'\.(i?[ls])', tk)
                m_emptychord = re.match(r'-', tk)
                m_barline = re.match(r"(?P<rep1>[:])?(?P<kind>[|\[\]])(?P<rep2>[:])?", tk)
                if tk == ":":
                    bb.bar.append(Repeat())
                elif m_barline:
                    if m_barline.group("rep1"):
                        bb.bar.append(Repeat())

                    if m_barline.group("kind") == '|':
                        bb.bar.append(Barline())
                    elif m_barline.group("kind") == '[':
                        bb.bar.append(Barline("double-start"))
                    elif m_barline.group("kind") == ']':
                        bb.bar.append(Barline("double-end"))

                    if m_barline.group("rep2"):
                        bb.bar.append(Repeat())
                elif m_time is not None:
                    bb.bar.append(Time(m_time.group(1), m_time.group(2)))
                elif m_case is not None:
                    bb.case = Case(m_case.groups()[0][1:-1])
                elif m_pause is not None:
                    bb.bar.append(Pause(m_pause.groups()[0]))
                    bb.size = "short"  # make the measure smaller
                elif m_penta is not None:
                    bb.bar.append(Pentagram())
                    bb.bar.append(EmptyChord())
                elif m_emptychord is not None:
                    bb.bar.append(EmptyChord())
                elif m_same is not None:
                    bb.bar.append(SameMeasure())
                elif m_size is not None:
                    if m_size.group(1).lower() == 'l':
                        bb.size = "long"  # make the measure smaller
                    elif m_size.group(1).lower() == 's':
                        bb.size = "short"  # make the measure smaller

                else:
                    bb.bar.append(Chord(tk))
            out.append(bb)
        return out

    def parse_section(self, text):
        section = Section()
        atoms = re.split('\s+', text)
        comment = []
        for atom in atoms:
            m_name = self.re["section"]["name"].match(atom)
            m_rarrow = self.re["section"]["rarrow"].match(atom)

            if len(comment) > 0 and (m_name or m_rarrow):
                section.children.append(SectionComment(' '.join(comment)))
                comment = []
            if m_name:
                name = SectionName(m_name.group("name"))
                section.children.append(name)
                if m_name.group("rep"):
                    rep = SectionRepetitions(m_name.group("rep"))
                    section.children.append(rep)
            elif m_rarrow:
                section.children.append(Rarrow())
            else:
                comment.append(atom)

        if len(comment) > 0:
            section.children.append(SectionComment(' '.join(comment)))
        return section

    def run(self, lines):
        g = Grid()

        for line in lines:

            # remove comments
            m_comment = self.re["comment"].match(line)
            if m_comment:
                line = m_comment.group(1)

            line = line.strip()
            if not line:
                continue  # skip empty lines

            m_title = self.re["title"].match(line)
            m_subtl = self.re["subtitle"].match(line)
            m_author = self.re["author"].match(line)
            m_copyright = self.re["copyright"].match(line)
            m_vspace = self.re["vspace"].match(line)
            m_sectn = self.re["sections-line"].match(line)
            m_grrow = self.re["grid-row"].match(line)
            m_tag= self.re["tag"].match(line)

            if m_title:
                g.info['title'] = m_title.group(1).strip()
            elif m_subtl:
                g.info['subtitle'] = m_subtl.group(1).strip()
            elif m_author:
                g.info['author'] = m_author.group(1).strip()
            elif m_copyright:
                g.info['copyright'] = m_copyright.group(1).strip()
            elif m_vspace:
                vspace = Vspace(m_vspace.group(1).strip().lower())
                g.tree.append(vspace)
            elif m_sectn:
                text = m_sectn.group(1).strip()
                g.tree.append(self.parse_section(text))
            elif m_grrow:
                gridRow = GridRow()
                gridRow.children = self.parse_row(m_grrow.group(0))
                g.tree.append(gridRow)
            elif m_tag:
                e = Element()
                e.html_text=m_tag.group(0)
                g.tree.append(e)
            else:
                g.tree.append(NotRecognized(line))

        return g


class CustomHandler(SimpleHTTPRequestHandler):
    # disable logging
    # override the logging method of the handler

    watcher = None

    def log_message(self, format, *args):
        return

    def do_GET(self):
        if self.path == "/is_changed/":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'is_changed': self.watcher.is_changed}).encode())

            self.watcher.is_changed = False
            return
        else:
            super(CustomHandler, self).do_GET()


class ThreadedServer(threading.Thread):
    def __init__(self, watcher, port=8000):
        self.httpd = None
        self.port = port
        CustomHandler.watcher = watcher
        self.handler = CustomHandler

        while self.httpd is None:
            try:
                self.httpd = HTTPServer(('localhost', self.port), self.handler)
                super().__init__()
            except OSError:
                self.port += 1

    def run(self):
        log("Server running.\n" \
            f"Open this address (http://localhost:{self.port}) in a web browser to see your grid")
        self.httpd.serve_forever()
        self.handler
        log("Server terminated")

    def stop_server(self):
        self.httpd.shutdown()
        self.httpd.socket.close()


def compile_mmd(filename, out_filename="index.html", live_server_addr=None):
    # open mmd script
    with open(filename, "r", encoding='utf-8') as f:
        mmd = f.readlines()

    # read it
    gp = GridProcessor()
    g = gp.run(mmd)

    # write html
    with open(out_filename, 'w', encoding='utf-8') as f:
        f.write(g.to_html(live_server_addr=live_server_addr))


class Watcher(threading.Thread):
    # check if a file has changed and recompile it
    def __init__(self, filename):
        self.is_changed = False
        self.filename = filename
        self.stop = False
        self.live_server_addr = None
        super(Watcher, self).__init__()

    def run(self, live_server_addr=None):
        compile_mmd(self.filename, live_server_addr=self.live_server_addr)
        mtime = os.stat(self.filename).st_mtime
        while True:
            if self.stop: break
            if os.stat(self.filename).st_mtime != mtime:
                mtime = os.stat(self.filename).st_mtime
                compile_mmd(self.filename, live_server_addr=self.live_server_addr)
                self.is_changed = True
            sleep(0.2)

