# -*- coding: utf-8 -*-
"""
Created on Wed Oct 30 09:32:31 2019

@author: ALU
"""
from fbcca import fbcca
from itr import itr
from scipy.io import loadmat
import numpy as np
import scipy.stats

'''
functon to calculate confidence interval (CI)
return:
    Estimate of mean
    Estimate of standard deviation
    Confidence interval for mean (2x1)
    Confidence interval for standard deviation (2x1)
Test: input [1,3,5,5,6]
Matalb : mean = 4  +/-CI = [1.5167, 6.4833]
         sigma = 2 +/-CI = [1.1983, 5.7471]
Python : mean = 4  +/-CI = [1.5167, 6.4833]
         sigma = 2 +/-CI = [1.1983, 5.7471]
'''
def normfit(data, confidence=0.95):
    n = len(data)
    m, se = np.mean(data), scipy.stats.sem(data)  #mean, standard error = (std/sqrt(n))
    #for small sample populations (N < 100 or so),
    #it is better to look up z in Student t's distribution instead of in the normal distribution
    # 2-side,and two tails are equal (like normal distribution)
    h = se * scipy.stats.t.ppf((1 + confidence) / 2.0, n-1)
    
    var = np.var(data, ddof=1) #ddof needs to be 1 to match matlab implementaton
    # two-side CI -> from alpha=(1-confidence)/2 ~ 1-alpha, here is 0.025~0.975
    # two tails are not equal   
    varCI_upper = var * (n - 1) / (scipy.stats.chi2.ppf((1-confidence) / 2, n - 1)) 
    varCI_lower = var * (n - 1) / (scipy.stats.chi2.ppf(1-(1-confidence) / 2, n - 1))
    sigma = np.sqrt(var)
    sigmaCI_lower = np.sqrt(varCI_lower)
    sigmaCI_upper = np.sqrt(varCI_upper)
    return m, sigma, [m - h, m + h], [sigmaCI_lower, sigmaCI_upper]

# load data
D = loadmat("sample")
eeg = D['eeg'] # ndarray

'''
parameters
'''
#Data length for target identification [s]
len_gaze_s = 0.5 
#Visual latency being considered in the analysis [s]
len_delay_s = 0.13                 
#The number of sub-bands in filter bank analysis
num_fbs = 5
#The number of harmonics in the canonical correlation analysis 
num_harms = 5
#100*(1-alpha_ci): confidence intervals
alpha_ci = 0.05
#Sampling rate [Hz]
fs = 250                 
#Duration for gaze shifting [s]
len_shift_s = 0.5             
#List of stimulus frequencies
BASE = np.arange(8.0,15.0+1,1)
list_freqs = [BASE, BASE+0.2, BASE+0.4, BASE+0.6, BASE+0.8]
list_freqs = np.stack(list_freqs, axis=0).ravel()
#The number of stimuli
num_targs = len(list_freqs)  
#Labels of data
labels = np.arange(0,num_targs,1)

'''
useful variable
'''
#Data length [samples]
len_gaze_smpl = round(len_gaze_s*fs)       
#Visual latency [samples], round have some problem here since it encouters 0.5
# to match matlab's result using ceiling here
len_delay_smpl = int(np.ceil(len_delay_s*fs))      
#Selection time [s]
len_sel_s = len_gaze_s + len_shift_s
#Confidence interval
ci = 100*(1-alpha_ci)  

'''
preparing data
'''
# cut into event-defined pieces 
[_, num_chans, _, num_blocks] = eeg.shape #[frequency(40) , channel(9), time(125), after BP(6)]
eeg = eeg[:, :, (len_delay_smpl):(len_delay_smpl+len_gaze_smpl), :] # 加上delay, then往後125sample

'''
Estimate classification performance
'''
accs = np.zeros(num_blocks)
itrs = np.zeros(num_blocks)
for block_i in range(num_blocks):  #choose one block
    
    #Test 
    testdata = np.squeeze(eeg[:, :, :, block_i])
    estimated = fbcca(testdata, list_freqs, fs, num_harms, num_fbs)
    
    #Evaluation 
    is_correct = (estimated==labels)
    accs[block_i] = np.mean(is_correct)*100;
    itrs[block_i] = itr(num_targs, np.mean(is_correct), len_sel_s)
    print('Trial {:d}: Accuracy = {:2.2f}%, ITR ={:2.2f} bpm\n'.format(
        block_i, accs[block_i], itrs[block_i]))
'''   
Summarize
'''
[mu, _, muci, _] = normfit(accs, (1-alpha_ci))
print("Mean accuracy = {:2.2f}% ({:2.0f}% CI: {:2.2f} - {:2.2f} %)\n".format(
        mu, ci, muci[0], muci[1]))

[mu, _, muci, _] = normfit(itrs, (1-alpha_ci))
print('Mean ITR = {:2.2f}  bpm ({:2.0f}% CI: {:2.2f} - {:2.2f} bpm)\n\n'.format(
    mu, ci, muci[0], muci[1]))

























