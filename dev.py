#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
"""
def debugger(vars):
    """
    starts interactive Python terminal at location in script
    very handy for debugging
    call this function with

    debugger(globals().copy())

    anywhere in the body of the script, or

    debugger(locals().copy())

    within a script function
    """
    import readline # optional, will allow Up/Down/History in the console
    import code
    # vars = globals().copy() # in python "global" variables are actually module-level
    vars.update(locals())
    shell = code.InteractiveConsole(vars)
    shell.interact()
