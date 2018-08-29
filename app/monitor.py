#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for monitoring a directory and running the program based on discovered inputs
"""
import os
import template

def find_input_IR_tsvs(inputDir):
    """
    """
    for root, dirs, files in os.walk(inputDir):
        for item in files:
            if item.endswith('.tsv'):
                yield(os.path.join(root, item))

if __name__ == '__main__':
    import sys
    inputDir = sys.argv[1]
    # print("inputDir is {0}".format(inputDir))

    for input in find_input_IR_tsvs(inputDir):
        output = os.path.splitext(input)[0] + ".html"
        if not os.path.exists(output):
            print("Making output: {0}".format(output))
            template.make_report(input = input, output = output)
