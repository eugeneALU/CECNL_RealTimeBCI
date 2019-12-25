# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 10:10:36 2019

@author: ALU
"""

import threading 
import pygame 
import time
from math import sin, pi

NUM_OF_THREAD = 6
b = threading.Barrier(NUM_OF_THREAD)

def blinking_block(points, frequency):
    COUNT = 1
    CLOCK = pygame.time.Clock()
    
    b.wait()    #Synchronize the start of each thread
    while True: #execution block
        CLOCK.tick(60)
        color = 127.5*(1+sin(2*pi*frequency*(COUNT/60))) 
        block = pygame.draw.polygon(win, (color, color, color), points, 0)
        pygame.display.update(block)  #can't update in main thread which will introduce delay in different block       
        COUNT += 1
        if COUNT == 61:
            COUNT = 1
#        print(CLOCK.get_time())
        
if __name__ == '__main__':
    pygame.init()
    pygame.TIMER_RESOLUTION = 1 #set time resolutions
    win = pygame.display.set_mode((1280,640))
    
    #background canvas
    bg = pygame.Surface(win.get_size())
    bg = bg.convert()
    bg.fill((0,0,0))           #  black background
    #display
    win.blit(bg, (0,0))
    pygame.display.update()
    pygame.display.set_caption("Blinking")
    
    
    frequency = [8,9,10,11,12,13] #frequency bank
    POINTS = [[(1175,0),(1070,210),(1280,210)],         #takeoff
              [(1175,640),(1070,430),(1280,430)],       #land
              [(425,0),(530,210),(320,210)],            #forward
              [(425,640),(530,430),(320,430)],          #backward
              [(0,320),(210,425),(210,215)],            #left
              [(850,320),(640,425),(640,215)]]          #right
    
    threads = []
    for i in range(6):
        threads.append(threading.Thread(target=blinking_block, args=(POINTS[i],frequency[i])))
        threads[i].setDaemon(True)
        threads[i].start()
     
    RUN = True    
    while RUN:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                RUN = False
        pygame.time.delay(100)
    
    pygame.quit()
    quit()
    
        
        
        