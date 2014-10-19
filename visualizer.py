import pyaudio
import numpy # for fft
import sys
import math
import struct
import time
import decimal
import curses



def analyze(data, width, sample_rate, bins):
    # Convert raw sound data to Numpy array
    fmt = "%dH"%(len(data)/2)
    data2 = struct.unpack(fmt, data)
    data2 = numpy.array(data2, dtype='h')
 
    # FFT black magic
    fourier = numpy.fft.fft(data2)
    ffty = numpy.abs(fourier[0:len(fourier)/2])/1000
    ffty1=ffty[:len(ffty)/2]
    ffty2=ffty[len(ffty)/2::]+2
    ffty2=ffty2[::-1]
    ffty=ffty1+ffty2
    ffty=numpy.log(ffty)-2
    
    fourier = list(ffty)[4:-4]
    fourier = fourier[:len(fourier)/2]
    
    size = len(fourier)
 
    # Split into desired number of frequency bins
    levels = [sum(fourier[i:(i+size/bins)]) for i in xrange(0, size, size/bins)][:bins]
    
    return levels



def main():
    chunk = 1024
    sample_rate= 48000
    device = 99
    bins = 50
    scale = .9

    p = pyaudio.PyAudio()
    
    print "Detecting audio cards"
    for i in range(0,p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if(dev['maxInputChannels']>0):
            print str(i) + ': '+dev['name']
            if dev['name']=='default':
                device = i
    
    print "Trying to connect the 'default' audio device..."
    if device==99:
        print "Couldnt find the default device"
        exit()

    print "Success!"

    stream = p.open(format = pyaudio.paInt16, 
                    channels = 1, 
                    rate = sample_rate,
                    input = True, 
                    frames_per_buffer = chunk, 
                    input_device_index = device)

    
    data = stream.read(chunk)

    minx=0
    maxx=-99

    screen = curses.initscr()
    (x,y) = screen.getmaxyx()

    pad = curses.newpad(x,y)
    x = x-1
    y = y-2

    bins = y/3

    curses.noecho()
    curses.curs_set(0)


    while True:
        try:
            pad.clear()
            levels = analyze(data, chunk, sample_rate, bins)

            #normalize levels
            if min(levels)<minx:
                minx=min(levels)
            if max(levels)>maxx:
                maxx=max(levels)
            normLevels = [x*round(((q-minx) / (maxx-minx)),2)**scale for q in levels]
           
            for l in range(0,len(normLevels)):
                for i in range(0,int(normLevels[l])):
                    pad.addch(x-i,l*3,'_')
                    pad.addch(x-i,l*3+1,'_')

            pad.refresh(0,0, 0,0, x,y)

            # get a new chunk of data
            try: 
                data = stream.read(chunk) 
            except IOError: 
                pass
                #print 'warning: dropped frame' # can replace with 'pass' if no message desired 
            time.sleep(0.01)
        except KeyboardInterrupt:
            stream.close()
            curses.endwin()
            exit()

if __name__ == '__main__':
    main()
