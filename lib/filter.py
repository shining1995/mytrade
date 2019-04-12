# -*- coding: utf-8 -*-

def omit_long_filter(value):
    length = len(value)
    seg = length / 4
    if length > 30:
        return '%s...%s' % (value[:seg], value[-seg:])
    else:
        return value
