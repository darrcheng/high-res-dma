#import u3 #Imports Labjack U3 Class
from labjack import ljm
import struct
from datetime import datetime #Pulls current time from system
from datetime import timedelta #Calculates difference in time

from tkinter import *
from tkinter import ttk
root=Tk()

from random import random #TEMP

import threading
import time

import csv

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


#Declare Streaming Interval, Set Default Value
streamingInterval = StringVar()
streamingInterval.set(1000) #Default Value 1000ms 
#Declare Voltage Start, Set Default Value
voltage_start = StringVar()
voltage_start.set(0) #Default Value 0V 
#Declare Voltage Stop, Set Default Value
voltage_stop = StringVar()
voltage_stop.set(400) #Default Value 500V

#TKINTER defining the callback function (observer) 
def my_callback(var,index,mode): 
    print("Streaming intverval: {}".format(streamingInterval.get()))
    print("Start Voltage: {}".format(voltage_start.get()))
    print("Stop Voltage: {}".format(voltage_stop.get()))

def set_voltage(voltage, handle, name):
    signal_factor = 1/2000
    voltage_output = voltage * signal_factor
    #Labjack code here to set voltage
    
def read_voltage(instrument, handle, name = 'AIN0', scaling = 1):
     result = ljm.eReadName(handle, name)
     instrument = instrument.append(result * scaling) 

def start_run():
    return True

def time_tracker(exact_time, time_list):
    current_time = datetime.now()
    exact_time.append(current_time)
    if not time_list:
        time_list.append(0)
    else:
        time_difference = current_time - exact_time[0]
        time_list.append(time_difference.total_seconds())



################################# GUI ########################################

# Create Window
root.title("Bertan Voltage Control")

#Create frame for graph
GraphFrame = ttk.Frame(root)
GraphFrame.grid(row=2, column=0,rowspan=2,padx=0)
fig = Figure(figsize=(5, 4), dpi=100)
canvas = FigureCanvasTkAgg(fig, master=GraphFrame)
canvas.draw()
canvas.get_tk_widget().pack()
figure1 = fig.add_subplot(111)


# #Create frame for graph buttons
# ButtonFrame = ttk.Frame(root)
# ButtonFrame.grid(row=4, column=0,rowspan=2,padx=0)


#Frame for setting logging frequency
FreqFrame = ttk.Frame(root)
FreqFrame.grid(row=5, column=9,rowspan=2,padx=0)

#Data logging frequency entry box and labels
ttk.Label(FreqFrame, text="Data frequency",font=('Helvetica', 11))\
    .grid(row=0,column=0,sticky='W')
ttk.Label(FreqFrame, text="ms",font=('Helvetica', 11)).grid(row=0,column=2)
LoggingFreq = ttk.Entry(FreqFrame,textvariable = streamingInterval,width=10)\
    .grid(row=0,column=1,padx=5,sticky='w') #Change from boo to LoggingFreq
streamingInterval.trace_add('write',my_callback)

#Insert Filename
ttk.Label(FreqFrame, text="Filename", font =('Helvetica', 11)).grid(row=1, column = 0, sticky= 'W')
gui_filename = Text(FreqFrame, width=30, height=1)
gui_filename.grid(row=1, column=1, rowspan=2)
gui_filename.insert('1.0','No Filename')


#Frame for setting Bertan Voltages
BertanFrame = ttk.Frame(root)
BertanFrame.grid(row=0, column=0, pady=5)

#Bertan voltage entry boxes and labels
ttk.Label(BertanFrame, text="Bertan Voltage", font=('Helvetica', 12, 'bold'))\
    .grid(row=0, column=4)# sticky='E', pady=10) , bg='light blue'

ttk.Label(BertanFrame, text="Set START Voltage:").grid(row=2, column=4)
BertanStart = ttk.Entry(BertanFrame,textvariable = voltage_start,width=13)
BertanStart.grid(row=2,column=5, padx=10) #change e0 to BertanStart
ttk.Label(BertanFrame,text="Value from -5V to 5V").grid(row=2, column=6,padx=0)
voltage_start.trace_add('write',my_callback)

ttk.Label(BertanFrame, text="Set STOP Voltage:").grid(row=3, column=4)
BertanStop=ttk.Entry(BertanFrame,textvariable = voltage_stop,width=13).grid(row=3,column=5, padx=10) #change e1 to BertanStop
voltage_stop.trace_add('write',my_callback)

ttk.Label(BertanFrame, text="Actual Voltage:").grid(row=4,column=4)
bertan_voltage = Text(BertanFrame,width=10, height=1)
bertan_voltage.grid(row=4, column=5) #change t0 to BertanVoltage
bertan_voltage.insert('1.0', '0.00')
ttk.Label(BertanFrame, text="Volts").grid(row=4, column=6, padx=0)

ttk.Label(BertanFrame, text="Electrometer Voltage:").grid(row=5,column=4)
electrometer_output = Text(BertanFrame,width=10, height=1)
electrometer_output.grid(row=5, column=5) #change t1 to ElectroVoltage
electrometer_output.insert('1.0', '0.00')
ttk.Label(BertanFrame, text="Volts").grid(row=5, column=6, padx=0)

#Open Labjack
handle = ljm.openS("T7", "ANY", "ANY")  # T7 device, Any connection, Any identifier
info = ljm.getHandleInfo(handle)
print("Opened a LabJack with Device type: %i, Connection type: %i,\n"
    "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i" %
    (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5]))


def run_program():

    #Initalize Lists
    exact_time = []
    time_from_start = []
    dma_voltage = []
    electrometer_voltage = []    



    #Define Labjack Inputs
    electrometer_read = 'AIN0'
    dma_read = 'AIN1'
    dma_write = 'TDAC0'
    # fig = Figure(figsize=(5, 4), dpi=100)
    # #fig.add_subplot(111).plot(dma_voltage, electrometer_voltage)

    # canvas = FigureCanvasTkAgg(fig, master=GraphFrame)

    #Pull operating parameters from GUI
    current_voltage = int(voltage_start.get())
    voltage_end = int(voltage_stop.get())
    step_time = int(streamingInterval.get())

    #Create Filename
    start_time = datetime.now()
    dt_string = start_time.strftime('%Y_%m_%d_%H_%M_%S')
    filename = 'DMA_{datetime}.csv'.format(datetime = dt_string)
    gui_filename.delete('1.0','1.end')
    gui_filename.insert('1.0', filename)

    event=threading.Event()

    #Clear Figure
#    figure1.cla()

    #open file
    with open(filename, 'w', newline='') as csvfile:
        data_writer = csv.writer(csvfile, delimiter=',')
        
        #write header
        data_writer.writerow(['Time', 'Time Since Start', 'DMA Voltage', 'Electrometer Voltage'])
        

        while (current_voltage <= voltage_end):

            #Take Readings
            time_tracker(exact_time, time_from_start)
            read_voltage(dma_voltage, handle, dma_read, 200)
            read_voltage(electrometer_voltage, handle, electrometer_read)

            #Update GUI
            bertan_voltage.delete('1.0', '1.end')
            bertan_voltage.insert('1.0',"%.2f" % dma_voltage[-1])
            electrometer_output.delete('1.0', '1.end')
            electrometer_output.insert('1.0',"%.2f" % electrometer_voltage[-1])

            #Write line to file
            data_writer.writerow([exact_time[-1], time_from_start[-1], dma_voltage[-1], electrometer_voltage[-1]])

            root.after(int(step_time*50/52.458))
            # time.sleep(1)
            root.update()

            #Set voltage
            ljm.eWriteName(handle, dma_write, current_voltage/200)

            #Update graphs
            #fig = Figure(figsize=(5, 4), dpi=100)
            figure1.plot(dma_voltage, electrometer_voltage)

            #canvas = FigureCanvasTkAgg(fig, master=GraphFrame)  # A tk.DrawingArea.
            canvas.draw()
            canvas.get_tk_widget().pack()

            #Increment Current Voltage
            current_voltage += 1
        
        #Reset Voltage to 0
        ljm.eWriteName(handle, dma_write, 0)




#Read Set Voltages
BertanVoltSet = Button(BertanFrame,text="Start", width=5, bg='springgreen', command = run_program)\
    .grid(row=2, column=7, padx=10, ipady=1) 


root.mainloop()

