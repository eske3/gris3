#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2025/08/02 07:09 Eske Yoshinob[eske3g@gmail.com]
        update:2025/08/02 07:28 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2025 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import re
import inspect
from . import lib, verutil


HELP_DOCUMENT_STYLE = '''
<style type="text/css">
.syntax{
    color:#5096f0;
}
.var{
    color:#5096f0;
}
h3{
    color:#d09820;
    margin-bottom:0;
    font-weight:normal;
}
ul{
    margin-top:0;
    margin-bottom:0;
    margin-left:0;
}

div.separator{
    margin-bottom:2em;
}
</style>
'''


def parsePydoc(docstring):
    r"""
        与えられた文字列がgooglestyleで記述されていた場合に内容を解析する。
        
        Args:
            docstring (str):

        Returns:
            dict:
    """
    patterns = [
        ('parameters', re.compile('^Args:')), 
        ('return', re.compile('^Returns:')),
    ]
    results = {}
    ptn = patterns.pop(0)
    stacked = []
    category = 'brief'
    for line in [x.strip() for x in docstring.split('\n')]:
        if ptn[1].search(line):
            results[category] = stacked
            stacked = []
            category = ptn[0]
            if not patterns:
                continue
            ptn = patterns.pop(0)
            continue
        if not line:
            continue
        stacked.append(line)
    if stacked:
        results[category] = stacked
    return results


def parseStylizedPydoc(docstring):
    r"""
        与えられた文字列がドキュメント用記述されていた場合、内容を解析して
        リッチテキストに変換して返す。
        現在内部は専用の解析アルゴリズムになっているが、将来的には
        parsePydoc関数を用いる予定。

        Args:
            docstring (str):

        Returns:
            list:
    """
    def parseDoxygenStyle(docstring):
        r"""
            Args:
                docstring (str):
                
            Returns:
                list:
        """
        lines = []
        patterns = {
            'brief' : (re.compile('@brief\s(.*)'), []),
            'param' : (re.compile('@param\s(.*)'), []),
            'return' : (re.compile('@return\s(.*)'), []),
        }
        other = []
        for line in docstring.split('\n'):
            for ptn_name, data in patterns.items():
                r = data[0].search(line)
                if r:
                    data[1].append(r.group(1))
                    break
            else:
                other.append(line)
        # 概要部分の組み立て。=================================================
        for cat, label, fmt in (
            ('brief', 'Brief', '%s<br>'),
            ('param', 'Parameters', '<li>%s</li>'),
            ('return', 'Return', '%s')
        ):
            pre = '\n'.join([fmt % x for x in patterns[cat][1]])
            if not pre:
                continue
            lines.append('<h3>{}</h3><ul>{}</ul>'.format(label, pre))
        # =====================================================================
        # その他。=============================================================
        if other:
            lines.append('<ul>%s</ul>'%('<br>'.join(other)))
        # =====================================================================
        return lines

    def parseGoogleStyle(docstring):
        r"""
            Args:
                docstring (str):

            Returns:
                list:
        """
        patterns = [
            ('Parameters', re.compile('Args:'), '<li>%s</li>'), 
            ('Return', re.compile('Returns:'), '%s'),
        ]
        titleformat = '<h3>%s</h3>'
        lineformat =  '   %s<br>'

        ptn = patterns.pop(0)
        lines = [titleformat%('Brief')]
        stacked = []
        for line in [x.strip() for x in docstring.split('\n')]:
            if ptn[1].search(line):
                lines[-1] = lines[-1]+('<ul>%s</ul>'%('\n'.join(stacked)))
                lines.append(titleformat%(ptn[0]))
                stacked = []
                lineformat = ptn[2]
                if not patterns:
                    continue
                ptn = patterns.pop(0)
                continue
            if not line:
                continue
            stacked.append(lineformat%line)
        if stacked:
            lines[-1] = lines[-1]+('<ul>%s</ul>'%'\n'.join(stacked))
        return lines
    # /////////////////////////////////////////////////////////////////////////
    #                                                                        //
    # /////////////////////////////////////////////////////////////////////////

    if re.search('@brief', docstring):
        # Doxygenスタイルのドキュメントストリング
        return parseDoxygenStyle(docstring)
    return parseGoogleStyle(docstring)


def analyzeDocument(method, defaultStyle=HELP_DOCUMENT_STYLE):
    r"""
        規定のフォーマットで書かれたドキュメントをリッチテキストに変換して返す。
        
        Args:
            method (any):ドキュメントを表示するfunction、classなど
            defaultStyle (str):リッチテキスト書式に適用するスタイルシート
            
        Returns:
            str:
    """
    str_type = verutil.BaseString
    f_type =  type(lambda x:x)
    document = lib.encode(method.__doc__)
    try:
        spec = inspect.getargspec(method)
    except:
        header = defaultStyle
    else:
        header = '%s<span class="syntax">Syntax</span> : %s' % (
            defaultStyle,
            method.__name__
        )
        # 引数の組み立て。
        defaultlist = spec.defaults or []
        num = len(defaultlist)
        arglist = spec.args[:-num]
        for a, v in zip(spec.args[len(arglist):], defaultlist):
            if isinstance(v, str_type):
                v = "'%s'"%v
            elif isinstance(v, f_type):
                v = 'function'
            arglist.append('%s=%s'%(a, v))
        if spec.varargs:
            arglist.append('*%s'%spec.varargs)
        if spec.keywords:
            arglist.append('**%s'%spec.keywords)

        num = 4
        lines, mod = divmod(len(arglist), num)
        if lines < 1 or (lines==1 and mod==0):
            args = ', '.join(arglist)
        else:
            args = ''
            for i in range(lines):
                line = ', '.join(arglist[i:i+num+1])
                args += '<ul>%s,</ul>'%line
            if mod:
                line = ', '.join(arglist[len(arglist)-mod:])
                args += '<ul>%s</ul>'%line
        header += '(%s)'%args

    if not document:
        return header

    lines = [header]
    lines.extend(parseStylizedPydoc(document))
    return '\n'.join(lines)