#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
"""
import os
from jinja2 import FileSystemLoader, Environment, select_autoescape
import ir
import pmkb

template_dir = os.path.join(os.path.dirname(__file__), "templates")
loader = FileSystemLoader(template_dir)
environment = Environment(
    loader = loader,
    autoescape = select_autoescape(['html'])
    )
template = environment.get_template('report.html')

def make_report(input, output):
    """
    """
    # initialize objects for parsing table and database
    IRtable = ir.IRTable(source = input)
    db = pmkb.PMKB()
    IRtable.lookup_all_interpretations(db = db)

    #  render output
    parsed = template.render(IRtable = IRtable)

    # write output
    with open(output, "w") as f:
        f.write(parsed)




if __name__ == '__main__':
    import ir
    import pmkb

    output_html = "output.html"
    IRtable = ir.demo()
    PMKB, _ = pmkb.demo()
    IRtable.lookup_all_interpretations(db = PMKB)
    # IRtable.records[1].interpretations

    parsed = template.render(IRtable = IRtable)

    with open(output_html, "w") as f:
        f.write(parsed)
    # from dev import debugger
    # debugger(globals().copy())
