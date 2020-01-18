# -*- coding: utf-8 -*-
"""
Created on Fri Jan  3 11:20:58 2020

@author: ALU
"""
import numpy as np
from fbcca import fbcca_realtime
from fbcca import fbcca
SAMPLE_RATE = 500
t = np.linspace(0,1, num=SAMPLE_RATE)
s = np.sin(2*np.pi*8*t)
s = s[np.newaxis,:]
ss = np.repeat(s, 32, axis=0)
sss = ss[np.newaxis,:]
sss = np.repeat(sss, 6, axis=0)
list_freqs = np.arange(8.0,13.0+1,1)
fbcca_realtime(ss, list_freqs, SAMPLE_RATE, num_harms=3, num_fbs=5)
fbcca(sss, list_freqs, SAMPLE_RATE, num_harms=3, num_fbs=5)
