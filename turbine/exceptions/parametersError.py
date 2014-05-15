"""
Created on Apr 2, 2014

@author: lesparre
"""

class ParametersError(Exception):
    """
    classdocs
    """

    def __init__(self, msg):
        """
        Constructor
        """
        Exception.__init(self, msg)
