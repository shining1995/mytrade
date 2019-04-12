# -*- coding: utf-8 -*-

import logging
import urllib2


def retrive_content(url):
    try:
        res = urllib2.urlopen(url)
    except Exception, e:
        content = 'NOT FOUND'
        logging.debug(e)
        logging.debug('failed to get content of %s' % url)
    else:
        content = res.read()
    return content
