"""
Created on Apr 2, 2014

@author: lesparre
"""

class GenerationError(Exception):
    """
    classdocs
    """

    def __init__(self, step, msg):
        """
        Constructor
        """
        self.step = step
        self.msg = msg
        
    def __str__(self):
        return "generation step : "+str(self.step)+" "+str(self.msg)