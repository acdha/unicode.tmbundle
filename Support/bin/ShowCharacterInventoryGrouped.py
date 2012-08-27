#!/usr/bin/python
# encoding: utf-8


import codecs
import itertools
import locale
import os
import sys
import unicodedata

from UniTools import *

sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
sys.stdin  = codecs.getreader('utf-8')(sys.stdin)

bundleLibPath = os.environ["TM_BUNDLE_SUPPORT"] + "/lib/"

locale.setlocale(locale.LC_ALL, locale.getdefaultlocale()[0])

class SeqDict(dict):
    """Dict that remembers the insertion order."""
    def __init__(self, *args):
        self._keys={}
        self._ids={}
        self._next_id=0
    def __setitem__(self, key, value):
        self._keys[key]=self._next_id
        self._ids[self._next_id]=key
        self._next_id+=1
        return dict.__setitem__(self, key, value)
    def keys(self):
        ids=list(self._ids.items())
        ids.sort()
        keys=[]
        for id, key in ids:
            keys.append(key)
        return keys



HEADER_HTML = """<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>Character Inventory</title>
<style type='text/css'>
    @import url(http://fonts.googleapis.com/css?family=Source+Sans+Pro:400,400italic,700|Droid+Sans+Mono&subset=latin,latin-ext);

    body {
        font-family: 'Source Sans Pro', sans-serif;
        font-size: 12pt;
    }

    pre, code, kbd, samp {
        font-family: "Droid Sans Mono", monospace;
        font-size: 14pt;
    }

    table {
        border-collapse: collapse;
        width: 100%;
    }

    th {
        font-size: larger;
        text-align: left;
        font-weight: 700;
        background-color: #333;
        color: #fff;
    }

    col {
        width: 15%;
    }

    col.name {
        width: 40%;
    }

    td {
        padding: 1px 3px;
    }

    tr {
        height: 2em;
    }

    tbody tr:nth-child(even) {
        background-color: #eee;
    }

    .a {
        text-align: center;
    }

    .c {
        font-family: "Droid Sans Mono", monospace;
        text-align: right;
        padding-right: 1em;
    }

    .tr1 {
        background-color: SandyBrown;
    }

    .tr2 {
        background-color: Cornsilk;
    }
    .b {
        text-align: center;
        cursor: pointer;
    }

    table#character-inventory {
        width: auto;
        margin: auto;
        text-align: center;
        vertical-align: middle;
    }

    table#character-inventory td {
        border: solid black 1px;
        width: 2em;
        height: 2em;
    }
</style>
</head>
<body>
"""


def main():
    print HEADER_HTML

    # dict of unique chars in doc and the number of its occurrence
    chKeys = {}
    for l in sys.stdin:
        for c in codepoints(l):
            try:
                chKeys[c] += 1
            except KeyError:
                chKeys[c] = 1

    chKeys.pop(10) # Avoid displaying newlines

    keys = chKeys.keys()
    keys.sort()

    relDataFile = file(bundleLibPath + "relatedChars.txt", 'r')
    relData = relDataFile.read().decode("UTF-8").splitlines()
    relDataFile.close()
    groups = SeqDict()    # groups of related chars
    unrel  = []    # list of chars which are not in groups

    for ch in keys:
        wch = wunichr(ch)
        for index, group in enumerate(relData):
            if wch in group:
                try:
                    groups[index].append(ch)
                except KeyError:
                    groups[index] = []
                    groups[index].append(ch)
                break
        else:
            unrel.append(ch)

    print "<table>"
    print """<colgroup><col class="character"/><col class="count"/><col class="codepoint"/><col class="block"/><col class="name"/></colgroup>"""
    print "<thead><tr><th>Character</th><th>Occurrences</th><th>UCS</th><th>Unicode Block</th><th>Unicode Name</th></tr></thead>"
    print "<tbody>"

    total = distinct = 0

    # get Unicode names of all chars in doc; if not in Unicodedata, get them from UnicodeData.txt.zip
    regExp = {}
    data = {}
    for ch in keys:
        try:
            data["%04X" % int(ch)] = unicodedata.name(wunichr(ch), "<")
        except ValueError:
            regExp["%04X" % int(ch)] = 1
        except TypeError:
            regExp["%04X" % int(ch)] = 1

    # FIXME: make this a simple file scan rather than an unbounded regexp
    if regExp:
        print >>sys.stderr, "Unmatched characters:"
        print >>sys.stderr, regExp.keys()
        UnicodeData = os.popen("zgrep -E '^(" + "|".join(regExp.keys()) + ");' '" + \
                        bundleLibPath + "UnicodeData.txt.zip'").read().decode("UTF-8")
        for c in UnicodeData.splitlines():
            uniData = c.strip().split(';')
            if len(uniData) > 1:
                data[uniData[0]] = uniData[1]

    # FIXME: merge the two duplicate HTML output blocks and properly escape entities

    bgclasses = ['tr2', 'tr1']

    for (clsstr, gr) in itertools.izip(itertools.cycle(bgclasses), groups.keys()):
        for c in groups[gr]:
            total += chKeys[c]
            distinct += 1
            t = wunichr(c)
            name = data.get("%04X" % int(c), getNameForRange(c) + "-%04X" % int(c))
            # I have no idea why name can be 1 ??
            if name == 1 or name[0] == '<': name = getNameForRange(c) + "-%04X" % int(c)
            if "COMBINING" in name: t = u"◌" + t
            # if groups[gr] has only one element shows up it as not grouped; otherwise bgcolor alternates
            if len(groups[gr]) == 1: clsstr = ''
            print "<tr class='" + clsstr + "'><td class='a'>", \
                    t, "</td><td class='c'>", locale.format("%d", chKeys[c], grouping=True), "</td><td class='c'>", \
                    "U+%04X" % (int(c)), "</td><td>", getBlockName(c), "</td><td>", name, "</tr>"

    for c in unrel:
        total += chKeys[c]
        distinct += 1
        t = wunichr(c)
        name = data.get("%04X" % int(c), getNameForRange(c) + "-%04X" % int(c))
        if name == 1 or name[0] == '<': name = getNameForRange(c) + "-%04X" % int(c)
        if "COMBINING" in name: t = u"◌" + t
        print "<tr><td class='a'>", t, "</td><td class='c'>", locale.format("%d", chKeys[c], grouping=True), \
                "</td><td class='c'>", "U+%04X" % (int(c)), "</td><td>", \
                getBlockName(c), "</td><td>", name, "</tr>"

    print "</tbody></table>"

    if total < 2:
        pl = ""
    else:
        pl = "s"

    print '<h2><a name="inventory">Character Inventory</a></h2>'
    print "<p><i>%s character%s total, %s distinct</i></p>" % (locale.format("%d", total, grouping=True),
                                                               pl,
                                                               locale.format("%d", distinct, grouping=True))

    print '<table id="character-inventory">'
    print '<tr>'
    for i, c in enumerate(sorted((unichr(i) for i in chKeys.keys()), key=ord)):
        if i > 0 and i % 25 == 0:
            print '</tr><tr>'
        print '<td>', c, '</td>',
    print '</tr>'
    print "</table>"

    print "</body></html>"


if __name__ == "__main__":
    main()