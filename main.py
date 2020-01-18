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
import time

#%% receive data function
def receive_data(q_data, q_time, inlet):
    #parameters
    L = 500 # Length of the sample we receive a time
    # open stream for pull chunk
    inlet.open_stream()
    # get a chunk first, in case the stream just start and some error will happen in the first data fetch
    chunk_list, time_list = inlet.pull_chunk(timeout=1.1, max_samples=L)

    while True:
        # get a chunk a time 
        # time out should be slightly greater to let the program adapt to some delay
        chunk_list, time_list = inlet.pull_chunk(timeout=1.1, max_samples=L)
        try:
            if len(chunk_list) == L:
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

# import scipy.stats will cause "forrtl: error (200): program aborting due to control-C event" when trying to end the program
# so add a manual function to handle it
# Still cause error but at least the program can catch the control-C event
# https://stackoverflow.com/questions/15457786/ctrl-c-crashes-python-after-importing-scipy-stats
import win32api
def doSaneThing(sig, func=None):
    print("END")
    Drone.send('end')
    raise KeyboardInterrupt
    
if __name__ == "__main__":
    #%% catching the control-C event
    win32api.SetConsoleCtrlHandler(doSaneThing, 1)

    #%% Access stream
    streams = resolve_stream('type', 'EEG')
    inlet = StreamInlet(streams[0], max_buflen=1000)
    info = inlet.info()
    NAME = inlet.info().name()
    SAMPLE_RATE = int(info.nominal_srate())
    CHANNEL_COUNT = int(info.channel_count())
    print("Name: {:s}".format(NAME))
    print("Channel Count: {:d}".format(CHANNEL_COUNT))
    print("Sample Rate: {:d}".format(SAMPLE_RATE))

    #%% Initialize of the Drone interface
    Drone = TELLO()

    #List of stimulus frequencies
    list_freqs = np.arange(8.0,13.0+1,1)
    COMMAND = ['takeoff', 'land', 'forward 10',
               'back 10', 'left 10', 'right 10']
    
    #%% Filter design
    ''' Filter '''
    # Design notch filter
    ''' power_line_frequency '''
    power_line_frequency = 60  # Target of the notch filter which is the power line frequency
    Q = 30.0 # Quality factors
    b, a = iirnotch(power_line_frequency, Q, fs=SAMPLE_RATE)
    # Design band pass filter
    ## cheb1ord
    # PASS_freq = 6 # Frequency to be removed from signal (Hz)
    # STOP_freq = 4
    # Nq = SAMPLE_RATE/2
    # Wp = [PASS_freq/Nq, 90/Nq]
    # Ws = [STOP_freq/Nq, 100/Nq]
    # [N, Wn] = cheb1ord(Wp, Ws, 3, 40) # StopBand=[~Ws(1);Ws(2)~] PassBand=[Wp(1)~Wp(2)] gpass=3(dB) gstop=40(dB)
    # [B, A] = cheby1(N, 0.5, Wn, 'bandpass')
    ## FIR
    # B = firwin(21, 0.024, pass_zero='highpass', fs=SAMPLE_RATE)
    # A = np.array([1])
    ## DC block 
    B = np.array([1,-1])
    A = np.array([1, 0.95])
    
    # initial condition of the filter
    zi_highpass = np.repeat(lfilter_zi(B, A)[np.newaxis,:], CHANNEL_COUNT, axis=0)
    zi_notch = np.repeat(lfilter_zi(b, a)[np.newaxis,:], CHANNEL_COUNT, axis=0)
    
    #%% start a thread to receive data
    q_data = queue.Queue(maxsize = 10) 
    q_time = queue.Queue(maxsize = 10) 
    recvThread = threading.Thread(target=receive_data, args=(q_data, q_time, inlet))
    recvThread.setDaemon(True)
    recvThread.start()
    
    #%% main thread
    ''' BUFFER_SIZE '''
    BUFFER_SIZE = 500
    BUFFER = np.zeros((CHANNEL_COUNT, BUFFER_SIZE), dtype=np.float32)
    TIME_BUFFER = np.zeros((BUFFER_SIZE), dtype=np.float32)
    # INDEX = 0 # using to calculate the right index of the buffer[used only when the buffer is longer than the length of the data that we receive a time]

    #%% plot the filtered signal
    # fig1 = plt.figure(figsize=(10,6))
    # ax1 = fig1.add_subplot(111)
    # line1, = ax1.plot(BUFFER[0,:])
    # line2 = ax1.axvline(x=INDEX, color = 'r')
    
    output_command = np.zeros(len(list_freqs)) # store the ouput command
    #%% plot the resulting command
    # fig2 = plt.figure(figsize=(10,6))
    # ax2 = fig2.add_subplot(111)
    # ax2.set_ylim(bottom=0, top=10)
    # bar1 = ax2.bar(list_freqs,output_command, tick_label = COMMAND)
   
    # parameters and buffer
    FirstRound = 0
    ''' Threshold '''
    Threshold = 3 # send out a command only when the times it appears over this threshold in order to reduce the noise
    RESULT_NOTCH = np.zeros((CHANNEL_COUNT, BUFFER_SIZE), dtype=np.float32)
    RESULT = np.zeros((CHANNEL_COUNT, BUFFER_SIZE), dtype=np.float32)

    #%% starting
    while True:
        try:
            # start = time.time() # check the execution time per round

            #%% [used only when the buffer is longer than the length of the data that we receive a time]
            # BUFFER[:,INDEX:INDEX+250] = q_data.get()
            # TIME_BUFFER[INDEX:INDEX+250] = q_time.get()
            BUFFER = q_data.get()
            TIME_BUFFER = q_time.get()
            
            q_data.task_done()
            q_time.task_done()
    
            #%% calculate the correct entry of the buffer[used only when the buffer is longer than the length of the data that we receive a time]
            # if INDEX == 0:
            #     idx_highpass = np.concatenate((np.arange(1000-len(B)+1,1000),np.arange(0,INDEX+250)),axis=0)
            #     idx_notch = np.concatenate((np.arange(1000-len(b)+1,1000),np.arange(0,INDEX+250)),axis=0)
            #     START = 1000-len(b)+1
            # else:
            #     idx_highpass = np.arange(INDEX-len(B)+1,INDEX+250)
            #     idx_notch = np.arange(INDEX-len(b)+1,INDEX+250)
            #     START = INDEX-len(b)+1
            
            #%% bypass first few round
            if FirstRound<5:
                FirstRound += 1
                continue 
            
            #%% Filtering
            y, zi_notch = lfilter(b, a, BUFFER, zi=zi_notch)  # notch filtering
            RESULT, zi_highpass = lfilter(B, A, y, zi=zi_highpass) # DC blocking

            #%% [used only when the buffer is longer than the length of the data that we receive a time]
            # INDEX += 250
            # if INDEX == 1000:
            #     INDEX = 0

            #%% FBCCA
            result = fbcca_realtime(RESULT, list_freqs, SAMPLE_RATE, num_harms=3, num_fbs=5) #how long should be the input 1 or 0.5 or more second?
            if result==999:
                print('No command match')
            else:
                #%% Command matched
                print(COMMAND[result])
                output_command[result] += 1
                
                # send out command that hit the threshold
                if output_command.max() == Threshold:
                    output = np.argmax(output_command)
                    #%% Send command to TELLO
                    Drone.send(COMMAND[result])
                    # reset the counter to zero
                    output = 0
                    output_command = np.zeros(len(list_freqs))
                    print(COMMAND[output]) # print the command
                    #%% plot the command accumulation window
                    # ax2.bar(list_freqs,output_command, tick_label = COMMAND)
                    # plt.pause(0.01)

            #%% plost the time domain result
            # line1.set_ydata(RESULT[0,:])
            # line2.set_xdata(INDEX)
            # ax1.set_xticklabels(TIME_BUFFER)
            # ax1.relim()
            # ax1.autoscale_view(True, True, True) # re-scale plot view
            # plt.pause(0.01)
                    
            # end = time.time()        
            # print("Cost {}(s)".format(end-start))

        except Exception as e: 
            print(e)
            Drone.send('end')  #End the Drone, force it to la
            del Drone          