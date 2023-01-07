from labjack import ljm
import struct
from datetime import datetime  # Pulls current time from system
from datetime import timedelta  # Calculates difference in time
import numpy as np

from tkinter import *
from tkinter import ttk

root = Tk()

# from random import random  # TEMP
import random

import threading
import time

import csv

import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Set Sampling Voltages
global sample_array
# sample_array = range(0,2551,150)
sample_array = [104, 136, 168, 200, 232, 264, 296, 328, 360, 480, 1000, 1960]
# sample_array = np.logspace(
#     np.log10(180), np.log10(2500), 15
# )  # convert to voltage before starting
# sample_array = np.logspace(
#     np.log10(148), np.log10(2992), 20
# )  # convert to voltage before starting
sample_array = np.insert(sample_array, 0, 0)
print(sample_array)

# Declare Streaming Interval, Set Default Value
streamingInterval = StringVar()
streamingInterval.set(1000)  # Default Value 1000ms
# Declare Voltage Start, Set Default Value
voltage_start = StringVar()
voltage_start.set(0)  # Default Value 0V


# TKINTER defining the callback function (observer)
def my_callback(var, index, mode):
    print("Streaming intverval: {}".format(streamingInterval.get()))
    print("Start Voltage: {}".format(voltage_start.get()))


def set_voltage(voltage, handle, name):
    signal_factor = 1 / 2000
    voltage_output = voltage * signal_factor
    # Labjack code here to set voltage


def read_voltage(instrument, handle, name="AIN2", scaling=1):
    # result = ljm.eReadName(handle, name)
    # instrument = instrument.append(result * scaling)
    instrument = instrument.append(random.random())


def start_run():
    BertanVoltSet.configure(text="Stop", command=stop_run)
    global interrupt
    interrupt = False
    global run_filename
    run_filename = create_filename()
    global run_filename_avg
    run_filename_avg = run_filename[:-4] + "_avg.csv"
    write_header()
    figure1.cla()
    run_program(
        record_start=datetime.now(),
        datetime_old=None,
        exact_time_avg=[],
        time_from_start_avg=[],
        electrometer_voltage_avg=[],
        electrometer_conc_avg=[],
    )


def stop_run():
    global interrupt
    interrupt = True
    BertanVoltSet.configure(text="Start", command=start_run)
    # Reset Voltage to 0 at the end of a run
    # ljm.eWriteName(handle, dma_write, 0)


def write_header():
    # Open Raw File
    with open(run_filename, "w", newline="") as csvfile:
        data_writer = csv.writer(csvfile, delimiter=",")
        # write header
        data_writer.writerow(
            [
                "Time",
                "Time Since Start",
                "DMA Voltage",
                "Electrometer Voltage",
                "Electrometer Concentration",
                "Electrospray Voltage",
                "Electrospray Current",
            ]
        )
    # Open Averaged File
    with open(run_filename_avg, "a", newline="") as csvfile_avg:
        data_writer_avg = csv.writer(csvfile_avg, delimiter=",")
        data_writer_avg.writerow(
            [
                "Time",
                "DMA Voltage",
                "Electrometer Concentration",
                "Time Since Start",
                "Electrometer Voltage",
                "DMA Set Voltage",
            ]
        )


def time_tracker(record_start, exact_time, time_list):
    current_time = datetime.now()
    exact_time.append(current_time)
    time_difference = current_time - record_start
    time_list.append(time_difference.total_seconds())


def create_filename():
    start_time = datetime.now()
    dt_string = start_time.strftime("%Y_%m_%d_%H_%M_%S")
    filename = "DMA_{datetime}.csv".format(datetime=dt_string)

    # Update GUI
    gui_filename.delete("1.0", "1.end")
    gui_filename.insert("1.0", filename)

    return filename


################################# GUI ########################################

# Create Window
root.title("Bertan Voltage Control")

# Create frame for graph
GraphFrame = ttk.Frame(root)
GraphFrame.grid(row=0, column=1, rowspan=5, padx=0)
fig = Figure(figsize=(5, 4), dpi=100)
canvas = FigureCanvasTkAgg(fig, master=GraphFrame)
canvas.draw()
canvas.get_tk_widget().pack()
figure1 = fig.add_subplot(111)


# #Create frame for graph buttons
# ButtonFrame = ttk.Frame(root)
# ButtonFrame.grid(row=4, column=0,rowspan=2,padx=0)

# Blower Control
blower_control_frame = ttk.Frame(root)
blower_control_frame.grid(row=0, column=0)
ttk.Label(
    blower_control_frame, text="Blower Control", font=("Helvetica", 12, "bold")
).grid(row=0, column=0, pady=(0, 5), columnspan=4)

blower_set = StringVar()
ttk.Label(blower_control_frame, text="Blower Set RPM: ").grid(row=1, column=0)
ttk.Entry(blower_control_frame, textvariable=blower_set, width=13).grid(
    row=1, column=1, padx=(0, 20)
)
blower_set.trace_add("write", my_callback)

ttk.Label(blower_control_frame, text="Blower RPM: ").grid(row=1, column=2, padx=(20, 0))
blower_actual = Text(blower_control_frame, width=10, height=1)
blower_actual.grid(row=1, column=3, pady=2)

# electrometer_flow = StringVar()
# electrometer_flow.set(322)
# ttk.Label(FreqFrame, text="Input Flow Rate: ").grid(row=1, column=0, sticky="W")
# ElectrometerFlow = ttk.Entry(FreqFrame, textvariable=electrometer_flow, width=13).grid(
#     row=1, column=1, sticky="W"
# )
# electrometer_flow.trace_add("write", my_callback)


# Program Header
voltage_control_frame = ttk.Frame(root)
voltage_control_frame.grid(row=1, column=0)
ttk.Label(
    voltage_control_frame, text="DMA Voltage Control", font=("Helvetica", 12, "bold")
).grid(row=0, column=0, pady=(0, 5))

# Frame for setting logging frequency
FreqFrame = ttk.Frame(voltage_control_frame)
FreqFrame.grid(row=1, column=0, padx=0)

# Insert Filename
ttk.Label(FreqFrame, text="Filename: ").grid(row=0, column=0, sticky="W")
gui_filename = Text(FreqFrame, width=30, height=1)
gui_filename.grid(row=0, column=1, pady=2)
gui_filename.insert("1.0", "No Filename")

# Input Electrometer Flow Rate
electrometer_flow = StringVar()
electrometer_flow.set(322)
ttk.Label(FreqFrame, text="Input Flow Rate: ").grid(row=1, column=0, sticky="W")
ElectrometerFlow = ttk.Entry(FreqFrame, textvariable=electrometer_flow, width=13).grid(
    row=1, column=1, sticky="W"
)
electrometer_flow.trace_add("write", my_callback)


# Data logging frequency entry box and labels
ttk.Label(FreqFrame, text="Data frequency (ms): ").grid(row=2, column=0, sticky="W")
LoggingFreq = ttk.Entry(FreqFrame, textvariable=streamingInterval, width=13).grid(
    row=2, column=1, sticky="w"
)  # Change from boo to LoggingFreq
streamingInterval.trace_add("write", my_callback)


# Frame for setting Bertan Voltages
BertanFrame = ttk.Frame(voltage_control_frame)
BertanFrame.grid(row=2, column=0, sticky="NW", pady=5)


# Radiobuttons for selecting mode
dma_mode = StringVar()
dma_mode.set("voltage_scan")

# DMA Scanning Options
scan_frame = ttk.Frame(BertanFrame)
scan_frame.grid(row=1, column=0, sticky="N", padx=5)
voltage_scan = ttk.Radiobutton(
    scan_frame, text="Voltage Scan", variable=dma_mode, value="voltage_scan"
).grid(row=0, column=0, columnspan=2, pady=(0, 5))
scan_start_volt = StringVar()
ttk.Label(scan_frame, text="Start Voltage: ").grid(row=1, column=0)
ttk.Entry(scan_frame, textvariable=scan_start_volt, width=13).grid(row=1, column=1)
scan_end_volt = StringVar()
ttk.Label(scan_frame, text="End Voltage: ").grid(row=2, column=0)
ttk.Entry(scan_frame, textvariable=scan_end_volt, width=13).grid(row=2, column=1)

# DMA Single Voltage Options
single_voltage_frame = ttk.Frame(BertanFrame)
single_voltage_frame.grid(row=1, column=1, sticky="N", padx=5)
single_voltage = ttk.Radiobutton(
    single_voltage_frame,
    text="Single Voltage",
    variable=dma_mode,
    value="single_voltage",
).grid(row=0, column=0, columnspan=2, pady=(0, 5))
single_voltage_value = StringVar()
ttk.Label(single_voltage_frame, text="Voltage: ").grid(row=1, column=0)
ttk.Entry(single_voltage_frame, textvariable=single_voltage_value, width=13).grid(
    row=1, column=1
)

# DMA Multiple Voltage Options
multi_voltage_frame = ttk.Frame(BertanFrame)
multi_voltage_frame.grid(row=1, column=2, sticky="N", padx=5)
multi_voltage = ttk.Radiobutton(
    multi_voltage_frame,
    text="Multiple Voltages",
    variable=dma_mode,
    value="multi_voltage",
).grid(row=0, column=0, columnspan=2, pady=(0, 5))
ttk.Label(multi_voltage_frame, text="Voltages: ").grid(row=1, column=0)
multi_voltage_list = Text(multi_voltage_frame, width=13, height=3)
multi_voltage_list.grid(row=1, column=1, pady=2)
ys = ttk.Scrollbar(
    multi_voltage_frame, orient="vertical", command=multi_voltage_list.yview
)
multi_voltage_list["yscrollcommand"] = ys.set
ys.grid(column=2, row=1, sticky="ns")
repeat_measure = StringVar()
ttk.Label(multi_voltage_frame, text="# Measurements : ").grid(row=2, column=0)
ttk.Entry(multi_voltage_frame, textvariable=repeat_measure, width=13).grid(
    row=2, column=1
)


# Monitoring
monitor_frame = ttk.Frame(voltage_control_frame)
monitor_frame.grid(row=3, column=0)


ttk.Label(monitor_frame, text="Set Voltage (V): ").grid(row=0, column=0)
BertanStart = Text(monitor_frame, width=10, height=1)
BertanStart.grid(row=0, column=1, padx=10)  # change e0 to BertanStart
BertanStart.insert("1.0", "0.00")


ttk.Label(monitor_frame, text="Actual Voltage (V): ").grid(row=1, column=0)
bertan_voltage = Text(monitor_frame, width=10, height=1)
bertan_voltage.grid(row=1, column=1)  # change t0 to BertanVoltage
bertan_voltage.insert("1.0", "0.00")

ttk.Label(monitor_frame, text="Electrospray Current: ").grid(row=2, column=0)
electrospray_output = Text(monitor_frame, width=10, height=1)
electrospray_output.grid(row=2, column=1)  # change t1 to ElectroVoltage
electrospray_output.insert("1.0", "0.00")

ttk.Label(monitor_frame, text="Electrometer Voltage (V): ").grid(row=3, column=0)
electrometer_output = Text(monitor_frame, width=10, height=1)
electrometer_output.grid(row=3, column=1)  # change t1 to ElectroVoltage
electrometer_output.insert("1.0", "0.00")

# ############ Open Labjack ##############################
# handle = ljm.openS("T7", "ANY", "ANY")  # T7 device, Any connection, Any identifier
# info = ljm.getHandleInfo(handle)
# print(
#     "Opened a LabJack with Device type: %i, Connection type: %i,\n"
#     "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i"
#     % (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5])
# )

# ljm.eWriteName(handle, "AIN2_RESOLUTION_INDEX", 8)
# ljm.eWriteName(handle, "AIN2_RANGE", 1.0)


# Define Labjack Inputs
global electrometer_read
electrometer_read = "AIN2"
global dma_read
dma_read = "AIN1"
global electrospray_voltage_read
electrospray_voltage_read = "AIN5"
# Set voltage
global electrospray_current_read
electrospray_current_read = "AIN4"
global dma_write
dma_write = "TDAC0"


########################### Main Program ###############################


def run_program(
    record_start,
    datetime_old=None,
    exact_time_avg=[],
    time_from_start_avg=[],
    electrometer_voltage_avg=[],
    electrometer_conc_avg=[],
    previous_voltage=0,
):

    # Pull operating parameters from GUI
    step_time = int(streamingInterval.get())
    flow_rate = int(electrometer_flow.get())

    # Other Constants
    voltage_factor_DMA = 10000 / 5
    repeat_samples = 150
    time_between_nested = 10
    electrometer_conv = 6.242e6 * 60

    # Define Lists
    exact_time = []
    time_from_start = []
    dma_voltage = []
    electrospray_voltage = []
    electrospray_current = []
    electrometer_voltage = []
    electrometer_conc = []

    # Datetime
    if datetime_old == None:
        datetime_old = datetime.now()
        global sample_index
        sample_index = 0
    elapsed_milliseconds = 0
    while elapsed_milliseconds < step_time:
        datetime_new = datetime.now()
        elapsed_milliseconds = int((datetime_new - datetime_old).total_seconds() * 1000)

    datetime_old = datetime_old + timedelta(seconds=1)
    sample_number = int(sample_index / repeat_samples)
    if sample_number > len(sample_array) - 1:
        stop_run()

    if interrupt:
        return

    # Determine what voltage to set
    if dma_mode.get() == "multi_voltage":
        # previous_voltage = -1
        current_voltage = sample_array[sample_number]
        sample_index += 1

    if dma_mode.get() == "voltage_scan":
        print(scan_start_volt.get())

    # if dma_mode.get() == "dma_scan":

    # previous_voltage = -1
    # current_voltage = sample_array[sample_number]
    # sample_index += 1

    repeat_readings = 0
    dwell_steps = int(step_time / time_between_nested)
    while repeat_readings < dwell_steps:
        nested_milliseconds = 0
        # while nested_milliseconds < 20:
        #     nested_milliseconds = int((datetime.now()- datetime_old).total_seconds()*1000 - time_between_nested*repeat_readings)

        # open file
        with open(run_filename, "a", newline="") as csvfile:
            data_writer = csv.writer(csvfile, delimiter=",")

            # Take Readings
            time_tracker(record_start, exact_time, time_from_start)
            # dma_voltage.append(ljm.eReadName(handle, dma_read) * voltage_factor_DMA)
            dma_voltage.append(random.random())
            # electrospray_voltage = (
            #     ljm.eReadName(handle, electrospray_voltage_read) * 5000 / 5
            # )
            electrospray_voltage = random.random()
            # electrospray_current = (
            #     ljm.eReadName(handle, electrospray_current_read) * 0.005 / 5
            # )
            electrospray_current = random.random()
            handle = 0
            read_voltage(electrometer_voltage, handle, electrometer_read)
            electrometer_conc.append(
                electrometer_voltage[-1] * electrometer_conv / flow_rate
            )

            # Write line to file
            data_writer.writerow(
                [
                    exact_time[-1],
                    time_from_start[-1],
                    dma_voltage[-1],
                    electrometer_voltage[-1],
                    electrometer_conc[-1],
                    electrospray_voltage,
                    electrospray_current,
                ]
            )

        # Update GUI and increment
        # root.update()
        repeat_readings += 1

    # Set new voltage
    if current_voltage != previous_voltage:
        # ljm.eWriteName(handle, dma_write, current_voltage / voltage_factor_DMA)
        previous_voltage = current_voltage

    # Average Readings for graphing and Summary CSV
    exact_time_avg.append(exact_time[0])
    time_from_start_avg.append(sum(time_from_start) / dwell_steps)
    dma_voltage_avg = sum(dma_voltage) / dwell_steps
    electrometer_voltage_avg.append(sum(electrometer_voltage) / dwell_steps)
    electrometer_conc_avg.append(sum(electrometer_conc) / dwell_steps)

    # open file
    with open(run_filename_avg, "a", newline="") as csvfile_avg:
        data_writer_avg = csv.writer(csvfile_avg, delimiter=",")
        data_writer_avg.writerow(
            [
                exact_time_avg[-1],
                dma_voltage_avg,
                electrometer_conc_avg[-1],
                time_from_start_avg[-1],
                electrometer_voltage_avg[-1],
                current_voltage,
                previous_voltage,
            ]
        )

    # Update GUI
    BertanStart.delete("1.0", "1.end")
    BertanStart.insert("1.0", "%.2f" % current_voltage)
    bertan_voltage.delete("1.0", "1.end")
    bertan_voltage.insert("1.0", "%.2f" % dma_voltage_avg)
    electrometer_output.delete("1.0", "1.end")
    electrometer_output.insert("1.0", "%.2f" % electrometer_conc_avg[-1])
    electrospray_output.delete("1.0", "1.end")
    electrospray_output.insert("1.0", "%.2f" % electrospray_current)

    if len(time_from_start_avg) > 100:
        time_from_start_avg.pop(0)
        electrometer_voltage_avg.pop(0)
        electrometer_conc_avg.pop(0)
        exact_time_avg.pop(0)
        figure1.cla()
        figure1.plot(time_from_start_avg, electrometer_conc_avg, "b")
        plt.autoscale(True)
    else:
        figure1.plot(time_from_start_avg, electrometer_conc_avg, "b")

    canvas.draw()

    root.after(
        1,
        lambda: run_program(
            record_start=record_start,
            datetime_old=datetime_old,
            exact_time_avg=exact_time_avg,
            time_from_start_avg=time_from_start_avg,
            electrometer_voltage_avg=electrometer_voltage_avg,
            electrometer_conc_avg=electrometer_conc_avg,
        ),
    )


# Read Set Voltages
BertanVoltSet = ttk.Button(monitor_frame, text="Start", width=5, command=start_run)
BertanVoltSet.grid(row=4, column=0, columnspan=2, pady=10, ipady=1)


root.mainloop()
