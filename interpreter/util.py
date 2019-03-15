#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Utility functions to use in the app
"""
def capitalize(x):
    """
    Capitalize the first letter of every word in a string,
    unless the string consists entirely of all capital letters

    Parameters
    ----------
    x: str
        character string

    Returns
    -------
    str
        capitalized string

    Examples
    --------
        >>> capitalize("The rain in spain")
        'The Rain In Spain'
        >>> capitalize("EGFR")
        'EGFR'
        >>> capitalize("lower case words")
        'lower case words'
        >>> capitalize("foo")
        'foo'
    """
    if x.isupper():
        return(x)
    else:
        return(x.title())

def sanitize_tumor_tissue(label):
    """
    Cleans up tumor and tissue type labels for consistency
    """
    # remove trailing whitespace
    label = label.strip()
    # fix case
    label = capitalize(label)
    # replace empty string with 'Any'
    if label == '':
        label = "Any"
    # replace 'All' with 'Any'
    if label == 'All':
        label = "Any"
    return(label)

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
    import os
    import sys
    import django
    import readline # optional, will allow Up/Down/History in the console
    import code
    # import app from top level directory
    parentdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(0, parentdir)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webapp.settings")
    django.setup()
    from interpreter.models import PMKBVariant, TissueType, TumorType, NYUTier
    from interpreter.ir import IRTable
    from interpreter.util import capitalize, debugger
    # vars = globals().copy() # in python "global" variables are actually module-level
    vars.update(locals())
    shell = code.InteractiveConsole(vars)
    shell.interact()
