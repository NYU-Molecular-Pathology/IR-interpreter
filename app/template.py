#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
"""
import os
from jinja2 import FileSystemLoader, Environment, select_autoescape
from dev import debugger
import IR

template_dir = os.path.join(os.path.dirname(__file__), "templates")
loader = FileSystemLoader(template_dir)
environment = Environment(
    loader = loader,
    autoescape = select_autoescape(['html'])
    )
template = environment.get_template('report.html')

if __name__ == '__main__':
    output_html = "output.html"
    IRtable = IR.demo()
    # IRtable.records[1].interpretations

    parsed = template.render(IRtable = IRtable)

    with open(output_html, "w") as f:
        f.write(parsed)
    # debugger(globals().copy())
