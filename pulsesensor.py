#!/usr/bin/env python

# Pulse sensor demo
# Author: Viktar Palstsiuk <vipals@gmail.com>

if False:
    import sip
    sip.settracemask(0x3f)

import random
import sys

import time

from PyQt4 import Qt
import PyQt4.Qwt5 as Qwt
from PyQt4.Qwt5.anynumpy import *

from numpy import fft
import numpy as np

# Data comes from here
import serial

class DataPlot(Qwt.QwtPlot):

    def __init__(self, *args):
        Qwt.QwtPlot.__init__(self, *args)

        self.setCanvasBackground(Qt.Qt.white)
        self.alignScales()

        # Initialize data
        period = 1/122.3 # 122.3 Sa/s ADC
        self.t = arange(0.0, 10.0, period) # 10 s
        self.x = zeros(len(self.t), Float)
        self.f = zeros(10, Float)

        self.setTitle("A Moving QwtPlot")
        self.insertLegend(Qwt.QwtLegend(), Qwt.QwtPlot.BottomLegend);

        self.curveX = Qwt.QwtPlotCurve("Data X")
        self.curveX.attach(self)

        self.curveF = Qwt.QwtPlotCurve("Data Y")
        self.curveF.attach(self)

        self.curveX.setPen(Qt.QPen(Qt.Qt.red))
        self.curveF.setPen(Qt.QPen(Qt.Qt.blue))

        mY = Qwt.QwtPlotMarker()
        mY.setLabelAlignment(Qt.Qt.AlignRight | Qt.Qt.AlignTop)
        mY.setLineStyle(Qwt.QwtPlotMarker.HLine)
        mY.setYValue(0.0)
        mY.attach(self)

        self.setAxisTitle(Qwt.QwtPlot.xBottom, "Time (seconds)")
        self.setAxisTitle(Qwt.QwtPlot.yLeft, "Values")

        # Open COM port
        self.datagen = serial.Serial('COM4', 28800, timeout = 10)
        self.n = 0
        self.ts = time.time()
        self.dt = period

        self.startTimer(1000) # 1 sec

    # __init__()

    def alignScales(self):
        self.canvas().setFrameStyle(Qt.QFrame.Box | Qt.QFrame.Plain)
        self.canvas().setLineWidth(1)
        for i in range(Qwt.QwtPlot.axisCnt):
            scaleWidget = self.axisWidget(i)
            if scaleWidget:
                scaleWidget.setMargin(0)
            scaleDraw = self.axisScaleDraw(i)
            if scaleDraw:
                scaleDraw.enableComponent(
                    Qwt.QwtAbstractScaleDraw.Backbone, False)

    # alignScales()
    
    def timerEvent(self, e):
        # x move from left to right:
        # Shift x arrays right and assign new value to x[0]
        while self.datagen.inWaiting() > 0:
            # Shift data buffer
            self.x = roll(self.x, 1)
            # Read ADC value from serial
            try:
                self.x[0] = float(self.datagen.readline())
                self.n = self.n + 1
                if self.n == 1000:
                    # Update Sa/s info
                    self.n = 0
                    ts = time.time()
                    self.dt = (ts-self.ts)/1000
                    print(str(1/self.dt)+' Sa/s, dt = '+str(self.dt)+' ms')
                    self.ts = ts
            except ValueError:
                print('Invalid value: flush Input', self.datagen.inWaiting())
                self.datagen.flushInput()

        # Plot ADC results
        self.curveX.setData(self.t, self.x)
                        
        n = len(self.x)
        m = np.mean(self.x)
        Fk = fft.fft(self.x - m)/n # Fourier coefficients (divided by n)
        nu = fft.fftfreq(n,self.dt) # Natural frequencies
        freqs = nu[:n/2+1]
        a = np.absolute(Fk[:n/2+1])*10
        # Plot spectrum magnitude
        #self.curveF.setData(freqs, a)
        # Find frequency of maximal power
        i = a.argmax(0)
        fmax = 60*freqs[i]
        amax = a[i]
        self.f = roll(self.f, 1)
        self.f[0] = fmax
        stdev = std(self.f[:])
        if stdev < 0.1 and fmax > 40 and fmax < 200 and amax > 1000:
            self.setTitle(str(fmax)+" BPM")
        print("F:",  '%.1f'%fmax, "BPM, D:", '%.1f'%stdev, "BPM, A:", '%.1f'%amax)
        self.replot()

    # timerEvent()

# class DataPlot

def make():
    demo = DataPlot()
    demo.resize(800, 600)
    demo.show()
    return demo

# make()

def main(args): 
    app = Qt.QApplication(args)
    demo = make()
    sys.exit(app.exec_())

# main()

# Admire
if __name__ == '__main__':
    main(sys.argv)

# Local Variables: ***
# mode: python ***
# End: ***
