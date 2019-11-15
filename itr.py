# -*- coding: utf-8 -*-
"""
Created on Wed Oct 30 10:21:23 2019

@author: ALU
"""

'''
Calculate information transfer rate (ITR) for brain-computer interface
 
Input:
    n   : # of targets
    p   : Target identification accuracy (0 <= p <= 1) 
    t   : Averaged time for a selection [s]
Output:
    itr : Information transfer rate [bits/min] 

Reference:
  [1] M. Cheng, X. Gao, S. Gao, and D. Xu,
      "Design and Implementation of a Brain-Computer Interface With High 
       Transfer Rates",
      IEEE Trans. Biomed. Eng. 49, 1181-1186, 2002.
'''
from math import log2
import warnings

def itr(n, p, t):
#    if (nargin < 3):
#        print('stats:itr:LackOfInput', 'Not enough input arguments.')

    if (p < 0 or 1 < p):
        raise ValueError('stats:itr:BadInputValue '\
                         +'Accuracy need to be between 0 and 1.')
    elif (p < 1/n):
        warnings.warn('stats:itr:BadInputValue '\
                      +'The ITR might be incorrect because the accuracy < chance level.')
        itr = 0
    elif (p == 1):
        itr = log2(n)*60/t
    else:
        itr = (log2(n) + p*log2(p) + (1-p)*log2((1-p)/(n-1)))*60/t
        
    return itr

if __name__ == '__main__':
    print(itr(10,0.95,1)) #matlab result = 172.6221
    print(itr(10,0.05,1)) #matlab result = 0
    print(itr(10,1,1))    #matlab result = 199.3157
    print(itr(10,1.5,1)) 
















