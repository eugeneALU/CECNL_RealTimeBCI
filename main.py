# -*- coding: utf-8 -*-
"""
Created on Wed Dec  4 10:22:24 2019

@author: ALU

All You need is here
@reference: https://github.com/labstreaminglayer/liblsl-Python/blob/1da8a50de68e2cfe5168d83712e20a5515c0705c/pylsl/pylsl.py
@https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.lfilter.html
@http://bigsec.net/b52/scipydoc/filters.html
@http://puremonkey2010.blogspot.com/2018/04/python-python-queue.html
# filtering reference
@https://scipy-cookbook.readthedocs.io/items/ApplyFIRFilter.html
@https://github.com/scipy/scipy/issues/5116
@https://www.mathworks.com/matlabcentral/answers/329357-initialize-filter-so-that-filtered-output-begins-with-initial-value-of-the-input
"""
import numpy as np
import matplotlib.pyplot as plt
from pylsl import StreamInfo, StreamOutlet, resolve_stream, StreamInlet
import threading 
from scipy.signal import iirnotch, filtfilt, cheb1ord, cheby1, lfilter, firwin,lfilter_zi,convolve
import scipy.signal as signal
import queue 
from Tello3 import TELLO 
from fbcca import fbcca_realtime
# pyqt for real time plot

#%% receive data function
def receive_data(q_data, q_time, inlet):
    # open stream for pull chunk
    inlet.open_stream()
    # get a chunk first, in case the stream just start and some error will happen in the first data fetch
    chunk_list, time_list = inlet.pull_chunk(timeout=0.6, max_samples=250)
    # count to drop the thread
    while True:
        # get a chunk a time 
        # time out should be slightly greater to let the program adapt to some delay
        chunk_list, time_list = inlet.pull_chunk(timeout=0.6, max_samples=250)
        try:
            if len(chunk_list) == 250:
                if q_time.full():
                    q_data.get()
                    q_time.get()
                q_data.put(np.array(chunk_list).T)
                q_time.put(np.array(time_list))
            else:
                print('Do not receive enough data')
        except:
            break
    # close stream for pull chunk
    inlet.close_stream()
    
def main():
    #%% Access stream
    
    # set stream info for Stream Outlet
    #         --name   --content_type --channel --sample_rate --channel_type --ID
    #info = StreamInfo("Test", "EEG", 8, 100, "float32", "myuid56872")
    Drone = TELLO()
    #List of stimulus frequencies
    list_freqs = np.arange(8.0,13.0+1,1)
    COMMAND = ['takeoff', 'land', 'forward 10',
               'back 10', 'left 10', 'right 10']

    BUFFER_SIZE = 1000
    MAX_SAMPLS = 250
    MULTIPLY = BUFFER_SIZE/MAX_SAMPLS
    
    streams = resolve_stream('type', 'EEG')
    
    inlet = StreamInlet(streams[0], max_buflen=1000)
    info = inlet.info()
    
    NAME = inlet.info().name()
    SAMPLE_RATE = int(info.nominal_srate())
    CHANNEL_COUNT = int(info.channel_count())
    print("Name: {:s}".format(NAME))
    print("Channel Count: {:d}".format(CHANNEL_COUNT))
    print("Sample Rate: {:d}".format(SAMPLE_RATE))
    
    timeout = MAX_SAMPLS/SAMPLE_RATE + 0.1
    q_data = queue.Queue(maxsize = 10) 
    q_time = queue.Queue(maxsize = 10) 
    
    #%% Filter design
    PASS_freq = 8  # Frequency to be removed from signal (Hz)
    STOP_freq = 6
    Nq = SAMPLE_RATE/2
    Wp = [PASS_freq/Nq, 90/Nq]
    Ws = [STOP_freq/Nq, 100/Nq]
    f0 = 60
    Q = 30.0
    # Design notch filter
    b, a = iirnotch(f0, Q, fs=SAMPLE_RATE)
    # Design band pass filter
    [N, Wn] = cheb1ord(Wp, Ws, 3, 40) # StopBand=[~Ws(1);Ws(2)~] PassBand=[Wp(1)~Wp(2)] gpass=3(dB) gstop=40(dB)
    [B, A] = cheby1(N, 0.5, Wn, 'bandpass')
#    B = firwin(21, 0.024, pass_zero='highpass', fs=SAMPLE_RATE)
    
    zi_highpass = np.repeat(lfilter_zi(B, A)[np.newaxis,:], CHANNEL_COUNT, axis=0)
    zi_notch = np.repeat(lfilter_zi(b, a)[np.newaxis,:], CHANNEL_COUNT, axis=0)
    
    #%% start a thread 
    recvThread = threading.Thread(target=receive_data, args=(q_data, q_time, inlet))
    recvThread.setDaemon(True)
    recvThread.start()
    
    #%% main thread
    BUFFER = np.zeros((CHANNEL_COUNT, BUFFER_SIZE), dtype=np.float32)
    TIME_BUFFER = np.zeros((BUFFER_SIZE), dtype=np.float32)
    INDEX = 0
    #%% plot the filtered signal
#    fig1 = plt.figure(figsize=(10,6))
#    ax1 = fig1.add_subplot(111)
#    line1, = ax1.plot(BUFFER[0,:])
#    line2 = ax1.axvline(x=INDEX, color = 'r')
#    timeticks = ax1.set_xticklabels(TIME_BUFFER)
#    ax.set_ylim(bottom=-10, top=10) # renew the data limits
    
    #%% plot the resulting comment
    output_command = np.zeros(len(list_freqs))
    
    fig2 = plt.figure(figsize=(10,6))
    ax2 = fig2.add_subplot(111)
    ax2.set_ylim(bottom=0, top=10)
    bar1 = ax2.bar(list_freqs,output_command, tick_label = COMMAND)
   
    # parameters and buffer
    FirstRound = 0
    Threshold = 10
    
    RESULT_NOTCH = np.zeros((CHANNEL_COUNT, BUFFER_SIZE), dtype=np.float32)
    RESULT = np.zeros((CHANNEL_COUNT, BUFFER_SIZE), dtype=np.float32)
    #%% starting
    while True:
        try:
            BUFFER[:,INDEX:INDEX+250] = q_data.get()
            TIME_BUFFER[INDEX:INDEX+250] = q_time.get()
            
            q_data.task_done()
            q_time.task_done()
    
            if INDEX == 0:
                idx_highpass = np.concatenate((np.arange(1000-len(B)+1,1000),np.arange(0,INDEX+250)),axis=0)
                idx_notch = np.concatenate((np.arange(1000-len(b)+1,1000),np.arange(0,INDEX+250)),axis=0)
                START = 1000-len(b)+1
            else:
                idx_highpass = np.arange(INDEX-len(B)+1,INDEX+250)
                idx_notch = np.arange(INDEX-len(b)+1,INDEX+250)
                START = INDEX-len(b)+1
            
            # bypass first few round 
            if FirstRound<10:
                FirstRound += 1
                continue 
                
    #        y, zi_highpass = lfilter(B, A, BUFFER[:, idx_highpass], zi=zi_highpass)
            RESULT_NOTCH[:,INDEX:INDEX+250] = filtfilt(b, a, BUFFER[:, idx_notch])[:, len(b) - 1:]
    #        RESULT_NOTCH[:,INDEX:INDEX+250] = convolve(BUFFER[:, idx_highpass], B[np.newaxis, :], mode='valid')
    #        RESULT[0,INDEX:INDEX+250] = lfilter(B, A, BUFFER[0, idx_notch])[len(b) - 1:]
            RESULT[:,INDEX:INDEX+250] = filtfilt(B, A, RESULT_NOTCH[:,INDEX:INDEX+250])#[:, len(B) - 1:]
            
            INDEX += 250
            if INDEX == 1000:
                INDEX = 0
            #%% FBCCA
            result = fbcca_realtime(RESULT[:,INDEX:INDEX+250], list_freqs, SAMPLE_RATE, num_harms=3, num_fbs=5)
            if result==999:
                print('No command match')
            else:
                
                #%% output threshold 
                output_command[result] += 1
                
                # send out command that is the greatest count during this interval
                if output_command.max() == Threshold:
                    output = np.argmax(output_command)
                    #%% Send commnad to TELLO
                    Drone.send(COMMAND[output])
                    # reset to zeros
                    output = 0
                    output_command = np.zeros(len(list_freqs))
#                    print(COMMAND[result])
        
#                line1.set_ydata(RESULT[0,:])
#                line2.set_xdata(INDEX+250)
#                ax1.set_xticklabels(TIME_BUFFER)
#                ax1.relim()
#                ax1.autoscale_view(True, True, True) # rescale plot view
                bar1[result].set_height(output_command[result])
                plt.pause(0.01)
        except Exception as e: 
            print(e)
            Drone.send('end')
            del Drone
            
            
#w, h = signal.freqz(b,a)
#plt.plot(w/3.14, 20 * np.log10(abs(h)), 'b')
#plt.ylabel('Amplitude [dB]', color='b')
#plt.xlabel('Frequency [rad/sample]')            