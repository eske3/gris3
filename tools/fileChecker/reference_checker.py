# !/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2021/06/08 15:21 shunsuke komori[eske3g@gmail.com]
        update:2021/07/20 19:07 shunsuke komori[eske3g@gmail.com]

    License:
        Copyright 2021 shunsuke komori[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import re
from . import core


class DataChecker(core.AbstractMayaDataChecker):
    def label(self):
        return 'External Reference'

    def check(self, header_lines):
        ref_ptn = re.compile('file\s\-rdi\s')
        end_ptn = re.compile('.* "(.+)";$')
        stacked = []
        references = []
        for line in header_lines:
            if stacked:
                stacked.append(line)
            else:
                if not ref_ptn.match(line):
                    continue
                stacked.append(line)
            end_line = end_ptn.search(line)
            if not end_line:
                continue
            references.append(end_line.groups())
            stacked = []
        num = len(references)
        if num < 1:
            return 1, ''
        con_text = 's are' if num > 2 else ' is'
        text = '\n'.join(
            ['    {}'.format(x[0]) for x in references]
        )
        return -1, '{} file{} referenced.\n{}'.format(num, con_text, text)
