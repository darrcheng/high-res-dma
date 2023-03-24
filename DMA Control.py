from labjack import ljm
import struct
from datetime import datetime  # Pulls current time from system
from datetime import timedelta  # Calculates difference in time
import numpy as np
from tkinter import *
from tkinter import ttk
import random
import threading
import time
import csv
import matplotlib
import os

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import configparser

import pandas as pd
import altair as alt
import webbrowser
import os


root = Tk()

config_file = configparser.ConfigParser()
config_file.read(r"dma_config.ini")

# TKINTER defining the callback function (observer)
def my_callback(var, index, mode):
    print("Blower Speed: {}".format(blower_set.get()))


def set_voltage(voltage, handle, name):
    signal_factor = 1 / 2000
    voltage_output = voltage * signal_factor
    # Labjack code here to set voltage


def read_voltage(instrument, handle, name="AIN2", scaling=1):
    result = ljm.eReadName(handle, name)
    instrument = instrument.append(result * scaling)


def update_run_settings():
    global single_voltage_update
    single_voltage_update = True
    global run_settings
    run_settings = create_run_settings()


def start_run():
    BertanVoltSet.configure(text="Stop", command=stop_run)
    global interrupt
    interrupt = False

    data_directory = config_file["general"]["data_directory"]
    day = datetime.strftime(datetime.now(), "%Y-%m-%d")
    data_directory_date = os.path.join(data_directory, day)
    print(data_directory_date)
    os.makedirs(data_directory_date, exist_ok=True)
    os.chdir(data_directory_date)

    global run_filename
    run_filename = create_filename()
    global run_filename_avg
    run_filename_avg = run_filename[:-4] + "_avg.csv"
    write_header()

    figure1.cla()

    run_settings = create_run_settings()

    run_program(
        datetime.now(),
        run_settings,
        datetime_old=None,
        exact_time_avg=[],
        dma_voltage_avg=[],
        time_from_start_avg=[],
        electrometer_voltage_avg=[],
        electrometer_conc_avg=[],
    )


def create_run_settings():
    run_settings = {
        "dma_mode": dma_mode.get(),
        "step_time": streamingInterval.get(),
        "flow_rate": electrometer_flow.get(),
        "ms_between_nested": int(config_file["general"]["ms_between_nested"]),
        "voltage_factor_dma": int(config_file["general"]["voltage_factor_dma"]),
        "sheath_temp_factor": int(config_file["general"]["sheath_temp_factor"]),
        "electrometer_read": config_file["lj_inputs"]["electrometer_read"],
        "dma_read": config_file["lj_inputs"]["dma_read"],
        "electrospray_voltage_read": config_file["lj_inputs"][
            "electrospray_voltage_read"
        ],
        "electrospray_current_read": config_file["lj_inputs"][
            "electrospray_current_read"
        ],
        "dma_write_neg": config_file["lj_inputs"]["dma_write_neg"],
        "dma_write_pos": config_file["lj_inputs"]["dma_write_pos"],
        "sheath_temp_read": config_file["lj_inputs"]["sheath_temp_read"],
        "sheath_rh_read": config_file["lj_inputs"]["sheath_rh_read"],
    }

    if dma_mode.get() == "multi_voltage":
        voltage_list = multi_voltage_list.get(1.0, END)
        test1 = list(map(int, voltage_list.split(",")))

        run_settings.update(
            {
                "num_measurements": repeat_measure.get(),
                "voltage_list": list(map(int, voltage_list.split(","))),
            }
        )

    if dma_mode.get() == "voltage_scan":
        run_settings.update(
            {
                "scan_start": scan_start_volt.get(),
                "scan_end": scan_end_volt.get(),
                "scan_step": scan_volt_step.get(),
            }
        )

    if dma_mode.get() == "single_voltage":
        run_settings.update({"set_volt": single_voltage_value.get()})
    return run_settings


def stop_run():
    global interrupt
    interrupt = True
    BertanVoltSet.configure(text="Start", command=start_run)
    df = pd.read_csv(run_filename_avg)
    graph_dma_voltage(df)

    # Reset Voltage to 0 at the end of a run


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
                "Sheath Temperature",
                "Sheath RH",
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
electrometer_flow = IntVar()
electrometer_flow.set(config_file["general"]["electrometer_flow"])
ttk.Label(FreqFrame, text="Input Flow Rate: ").grid(row=1, column=0, sticky="W")
ElectrometerFlow = ttk.Entry(FreqFrame, textvariable=electrometer_flow, width=13).grid(
    row=1, column=1, sticky="W"
)
electrometer_flow.trace_add("write", my_callback)


# Data logging frequency entry box and labels
streamingInterval = IntVar()
streamingInterval.set(config_file["general"]["data_frequency"])
ttk.Label(FreqFrame, text="Data frequency (ms): ").grid(row=2, column=0, sticky="W")
LoggingFreq = ttk.Entry(FreqFrame, textvariable=streamingInterval, width=13).grid(
    row=2, column=1, sticky="w"
)
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
scan_start_volt = IntVar()
scan_start_volt.set(config_file["voltage_scan"]["start_voltage"])
ttk.Label(scan_frame, text="Start Voltage: ").grid(row=1, column=0)
ttk.Entry(scan_frame, textvariable=scan_start_volt, width=13).grid(row=1, column=1)
scan_end_volt = IntVar()
scan_end_volt.set(config_file["voltage_scan"]["end_voltage"])
ttk.Label(scan_frame, text="End Voltage: ").grid(row=2, column=0)
ttk.Entry(scan_frame, textvariable=scan_end_volt, width=13).grid(row=2, column=1)
scan_volt_step = IntVar()
scan_volt_step.set(config_file["voltage_scan"]["voltage_step"])
ttk.Label(scan_frame, text="Voltage Step: ").grid(row=3, column=0)
ttk.Entry(scan_frame, textvariable=scan_volt_step, width=13).grid(row=3, column=1)

# DMA Single Voltage Options
single_voltage_frame = ttk.Frame(BertanFrame)
single_voltage_frame.grid(row=1, column=1, sticky="N", padx=5)
single_voltage = ttk.Radiobutton(
    single_voltage_frame,
    text="Single Voltage",
    variable=dma_mode,
    value="single_voltage",
).grid(row=0, column=0, columnspan=2, pady=(0, 5))
single_voltage_value = IntVar()
single_voltage_value.set(config_file["single_voltage"]["voltage"])
ttk.Label(single_voltage_frame, text="Voltage: ").grid(row=1, column=0)
ttk.Entry(single_voltage_frame, textvariable=single_voltage_value, width=13).grid(
    row=1, column=1
)
single_voltage_update = ttk.Button(
    single_voltage_frame, text="Update", width=10, command=update_run_settings
)
single_voltage_update.grid(row=2, column=0, columnspan=2, pady=5, ipady=1)
single_voltage_update = False


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
multi_voltage_list = Text(multi_voltage_frame, width=10, height=3)
multi_voltage_list.insert(1.0, config_file["multiple_voltages"]["set_voltages"])
multi_voltage_list.grid(row=1, column=1, pady=2)
ys = ttk.Scrollbar(
    multi_voltage_frame, orient="vertical", command=multi_voltage_list.yview
)
multi_voltage_list["yscrollcommand"] = ys.set
ys.grid(column=2, row=1, sticky="ns")
repeat_measure = IntVar()
repeat_measure.set(config_file["multiple_voltages"]["repeat_samples"])
ttk.Label(multi_voltage_frame, text="# Measurements : ").grid(row=2, column=0)
ttk.Entry(multi_voltage_frame, textvariable=repeat_measure, width=13).grid(
    row=2, column=1
)

# Monitoring
monitor_frame = ttk.Frame(voltage_control_frame)
monitor_frame.grid(row=3, column=0)
ttk.Label(monitor_frame, text="Time: ").grid(row=0, column=0)
current_time = Text(monitor_frame, width=10, height=1)
current_time.grid(row=0, column=1, padx=10)  # change e0 to BertanStart
current_time.insert("1.0", "00:00:00")
ttk.Label(monitor_frame, text="Temperature (C): ").grid(row=1, column=0)
sheath_temp = Text(monitor_frame, width=10, height=1)
sheath_temp.grid(row=1, column=1, padx=10)  # change e0 to BertanStart
sheath_temp.insert("1.0", "0.00")
ttk.Label(monitor_frame, text="Relative Hum. (%): ").grid(row=2, column=0)
sheath_rh = Text(monitor_frame, width=10, height=1)
sheath_rh.grid(row=2, column=1, padx=10)  # change e0 to BertanStart
sheath_rh.insert("1.0", "0.00")
ttk.Label(monitor_frame, text="Set Voltage (V): ").grid(row=3, column=0)
BertanStart = Text(monitor_frame, width=10, height=1)
BertanStart.grid(row=3, column=1, padx=10)  # change e0 to BertanStart
BertanStart.insert("1.0", "0.00")
ttk.Label(monitor_frame, text="Actual Voltage (V): ").grid(row=4, column=0)
bertan_voltage = Text(monitor_frame, width=10, height=1)
bertan_voltage.grid(row=4, column=1)  # change t0 to BertanVoltage
bertan_voltage.insert("1.0", "0.00")
ttk.Label(monitor_frame, text="Electrospray Current: ").grid(row=5, column=0)
electrospray_output = Text(monitor_frame, width=10, height=1)
electrospray_output.grid(row=5, column=1)  # change t1 to ElectroVoltage
electrospray_output.insert("1.0", "0.00")
ttk.Label(monitor_frame, text="Electrometer Voltage (V): ").grid(row=6, column=0)
electrometer_output = Text(monitor_frame, width=10, height=1)
electrometer_output.grid(row=6, column=1)  # change t1 to ElectroVoltage
electrometer_output.insert("1.0", "0.00")

BertanVoltSet = ttk.Button(monitor_frame, text="Start", width=5, command=start_run)
BertanVoltSet.grid(row=7, column=0, columnspan=2, pady=10, ipady=1)


############ Open Labjack ##############################
handle = ljm.openS("T7", "ANY", "ANY")  # T7 device, Any connection, Any identifier
info = ljm.getHandleInfo(handle)
print(
    "Opened a LabJack with Device type: %i, Connection type: %i,\n"
    "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i"
    % (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5])
)

ljm.eWriteName(handle, "AIN2_RESOLUTION_INDEX", 8)
ljm.eWriteName(handle, "AIN2_RANGE", 1.0)


# Define Labjack Inputs
# global electrometer_read
# electrometer_read = "AIN2"
# global dma_read
# dma_read = "AIN1"
# global electrospray_voltage_read
# electrospray_voltage_read = "AIN5"
# # Set voltage
# global electrospray_current_read
# electrospray_current_read = "AIN4"
# global dma_write_neg
# dma_write_neg = "TDAC0"


########################### Main Program ###############################


def run_program(
    record_start,
    run_settings,
    datetime_old=None,
    exact_time_avg=[],
    time_from_start_avg=[],
    dma_voltage_avg=[],
    electrometer_voltage_avg=[],
    electrometer_conc_avg=[],
    previous_voltage=0,
):
    # Pull operating parameters from GUI
    # step_time = streamingInterval.get()
    # flow_rate = electrometer_flow.get()

    # Enable Ultravolt
    ljm.eWriteName(handle, "DAC0", 3)

    # Other Constants
    voltage_factor_DMA = 5000 / 10
    electrometer_conv = 6.242e6 * 60

    # Define Lists
    exact_time = []
    time_from_start = []
    dma_voltage = []
    electrospray_voltage = []
    electrospray_current = []
    electrometer_voltage = []
    electrometer_conc = []
    sheath_flow_temp = []
    sheath_flow_rh = []

    # Datetime
    if datetime_old == None:
        datetime_old = datetime.now()
        global sample_index
        sample_index = 0
    elapsed_milliseconds = 0
    while elapsed_milliseconds < run_settings["step_time"]:
        datetime_new = datetime.now()
        elapsed_milliseconds = int((datetime_new - datetime_old).total_seconds() * 1000)

    datetime_old = datetime_old + timedelta(seconds=run_settings["step_time"] / 1000)

    # Stop run if stop button pressed
    if interrupt:
        ultravolt_voltage_set(
            0,
            handle,
            run_settings["dma_write_neg"],
            run_settings["dma_write_pos"],
        )
        ljm.eWriteName(handle, "DAC0", 0)
        return

    # Determine what voltage to set
    if run_settings["dma_mode"] == "multi_voltage":
        sample_number = int(sample_index / run_settings["num_measurements"])
        if sample_number > len(run_settings["voltage_list"]) - 1:
            stop_run()
            ultravolt_voltage_set(
                0,
                handle,
                run_settings["dma_write_neg"],
                run_settings["dma_write_pos"],
            )
            ljm.eWriteName(handle, "DAC0", 0)
            return
        current_voltage = run_settings["voltage_list"][sample_number]
        sample_index += 1

    if run_settings["dma_mode"] == "voltage_scan":
        if run_settings["scan_start"] <= run_settings["scan_end"]:
            step_pos = True
        else:
            step_pos = False
        current_voltage = run_settings["scan_start"] + run_settings[
            "scan_step"
        ] * sample_index * (-1 + 2 * step_pos)
        sample_index += 1
        if step_pos == True:
            if current_voltage > run_settings["scan_end"]:
                stop_run()
                ultravolt_voltage_set(
                    0,
                    handle,
                    run_settings["dma_write_neg"],
                    run_settings["dma_write_pos"],
                )
                ljm.eWriteName(handle, "DAC0", 0)
                return
        else:
            if current_voltage < run_settings["scan_end"]:
                stop_run()
                ultravolt_voltage_set(
                    0,
                    handle,
                    run_settings["dma_write_neg"],
                    run_settings["dma_write_pos"],
                )
                ljm.eWriteName(handle, "DAC0", 0)
                return

    if run_settings["dma_mode"] == "single_voltage":
        current_voltage = run_settings["set_volt"]
        global single_voltage_update
        if single_voltage_update == True:
            run_settings = create_run_settings()
            single_voltage_update = False

    # Set new voltage
    if current_voltage != previous_voltage:
        ultravolt_voltage_set(
            current_voltage / run_settings["voltage_factor_dma"],
            handle,
            run_settings["dma_write_neg"],
            run_settings["dma_write_pos"],
        )
        previous_voltage = current_voltage

    repeat_readings = 0
    dwell_steps = int(run_settings["step_time"] / run_settings["ms_between_nested"])
    while repeat_readings < dwell_steps:

        # open file
        with open(run_filename, "a", newline="") as csvfile:
            data_writer = csv.writer(csvfile, delimiter=",")

            # Take Readings
            time_tracker(record_start, exact_time, time_from_start)
            dma_voltage.append(
                ljm.eReadName(handle, run_settings["dma_read"])
                * run_settings["voltage_factor_dma"]
            )
            electrospray_voltage = (
                ljm.eReadName(handle, run_settings["electrospray_voltage_read"])
                * 5000
                / 5
            )
            electrospray_current = (
                ljm.eReadName(handle, run_settings["electrospray_current_read"])
                * 0.005
                / 5
            )
            read_voltage(
                electrometer_voltage, handle, run_settings["electrometer_read"]
            )
            electrometer_conc.append(
                electrometer_voltage[-1] * electrometer_conv / run_settings["flow_rate"]
            )

            sheath_flow_temp.append(
                ljm.eReadName(handle, run_settings["sheath_temp_read"])
                * run_settings["sheath_temp_factor"]
            )
            sheath_flow_rh.append(ljm.eReadName(handle, run_settings["sheath_rh_read"]))

            # Write unaveraged data to file
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

            # Pause until end of time increment
            repeat_reading_pause_time = int(
                repeat_readings * run_settings["ms_between_nested"]
                - (datetime.now() - datetime_old).total_seconds() * 1000
            )
            if repeat_reading_pause_time > 0:
                root.after(repeat_reading_pause_time)

        # Update GUI and increment
        # root.update()
        repeat_readings += 1

    sheath_flow_temp_avg = 0
    sheath_flow_rh_avg = 0

    # Average Readings for graphing and Summary CSV
    sheath_flow_temp_avg, sheath_flow_rh_avg = average_readings(
        exact_time_avg,
        time_from_start_avg,
        dma_voltage_avg,
        electrometer_voltage_avg,
        electrometer_conc_avg,
        sheath_flow_temp_avg,
        sheath_flow_rh_avg,
        exact_time,
        time_from_start,
        dma_voltage,
        electrometer_voltage,
        electrometer_conc,
        sheath_flow_temp,
        sheath_flow_rh,
        dwell_steps,
    )

    # Correct RH
    v_supply = 5
    sheath_flow_rh_avg = (sheath_flow_rh_avg / v_supply - 0.16) / 0.0062
    sheath_flow_rh_avg = sheath_flow_rh_avg / (1.0546 - 0.00216 * sheath_flow_temp_avg)

    # Write Averaged Data to CSV
    with open(run_filename_avg, "a", newline="") as csvfile_avg:
        data_writer_avg = csv.writer(csvfile_avg, delimiter=",")
        data_writer_avg.writerow(
            [
                exact_time_avg[-1],
                dma_voltage_avg[-1],
                electrometer_conc_avg[-1],
                time_from_start_avg[-1],
                electrometer_voltage_avg[-1],
                current_voltage,
                sheath_flow_temp_avg,
                sheath_flow_rh_avg,
            ]
        )

    # Update GUI
    update_gui(
        exact_time_avg,
        dma_voltage_avg,
        electrometer_conc_avg,
        electrospray_current,
        current_voltage,
        sheath_flow_temp_avg,
        sheath_flow_rh_avg,
    )

    # Update Graph
    update_graph(
        run_settings,
        exact_time_avg,
        time_from_start_avg,
        dma_voltage_avg,
        electrometer_voltage_avg,
        electrometer_conc_avg,
    )

    canvas.draw()

    root.update()
    root.after(
        1,
        lambda: run_program(
            record_start,
            run_settings,
            datetime_old=datetime_old,
            exact_time_avg=exact_time_avg,
            time_from_start_avg=time_from_start_avg,
            dma_voltage_avg=dma_voltage_avg,
            electrometer_voltage_avg=electrometer_voltage_avg,
            electrometer_conc_avg=electrometer_conc_avg,
            previous_voltage=previous_voltage,
        ),
    )


def update_graph(
    run_settings,
    exact_time_avg,
    time_from_start_avg,
    dma_voltage_avg,
    electrometer_voltage_avg,
    electrometer_conc_avg,
):
    if (
        run_settings["dma_mode"] == "multi_voltage"
        or run_settings["dma_mode"] == "single_voltage"
    ):
        if len(time_from_start_avg) > 100:
            time_from_start_avg.pop(0)
            dma_voltage_avg.pop(0)
            electrometer_voltage_avg.pop(0)
            electrometer_conc_avg.pop(0)
            exact_time_avg.pop(0)
            figure1.cla()
            figure1.plot(time_from_start_avg, electrometer_conc_avg, "b")
            plt.autoscale(True)
        else:
            figure1.plot(time_from_start_avg, electrometer_conc_avg, "b")

    if run_settings["dma_mode"] == "voltage_scan":
        if len(dma_voltage_avg) > 2:
            figure1.plot(dma_voltage_avg[-2:], electrometer_conc_avg[-2:], "b")
        else:
            figure1.plot(dma_voltage_avg, electrometer_conc_avg, "b")


def update_gui(
    exact_time_avg,
    dma_voltage_avg,
    electrometer_conc_avg,
    electrospray_current,
    current_voltage,
    sheath_temp_avg,
    sheath_rh_avg,
):
    current_time.delete("1.0", "1.end")
    current_time.insert("1.0", exact_time_avg[-1].strftime("%X"))
    BertanStart.delete("1.0", "1.end")
    BertanStart.insert("1.0", "%.2f" % current_voltage)
    bertan_voltage.delete("1.0", "1.end")
    bertan_voltage.insert("1.0", "%.2f" % dma_voltage_avg[-1])
    electrometer_output.delete("1.0", "1.end")
    electrometer_output.insert("1.0", "%.2f" % electrometer_conc_avg[-1])
    electrospray_output.delete("1.0", "1.end")
    electrospray_output.insert("1.0", "%.2f" % electrospray_current)
    sheath_temp.delete("1.0", "1.end")
    sheath_temp.insert("1.0", "%.1f" % sheath_temp_avg)
    sheath_rh.delete("1.0", "1.end")
    sheath_rh.insert("1.0", "%.0f" % sheath_rh_avg)


def average_readings(
    exact_time_avg,
    time_from_start_avg,
    dma_voltage_avg,
    electrometer_voltage_avg,
    electrometer_conc_avg,
    sheath_flow_temp_avg,
    sheath_flow_rh_avg,
    exact_time,
    time_from_start,
    dma_voltage,
    electrometer_voltage,
    electrometer_conc,
    sheath_flow_temp,
    sheath_flow_rh,
    dwell_steps,
):
    exact_time_avg.append(exact_time[0])
    time_from_start_avg.append(sum(time_from_start) / dwell_steps)
    dma_voltage_avg.append(sum(dma_voltage) / dwell_steps)
    electrometer_voltage_avg.append(sum(electrometer_voltage) / dwell_steps)
    electrometer_conc_avg.append(sum(electrometer_conc) / dwell_steps)
    sheath_flow_temp_avg = sum(sheath_flow_temp) / dwell_steps
    sheath_flow_rh_avg = sum(sheath_flow_rh) / dwell_steps
    return sheath_flow_temp_avg, sheath_flow_rh_avg


def ultravolt_voltage_set(voltage_set, lj_handle, neg_output, pos_output):
    if voltage_set > 0:
        ljm.eWriteName(lj_handle, pos_output, voltage_set)
        ljm.eWriteName(lj_handle, neg_output, 0)
    if voltage_set < 0:
        ljm.eWriteName(lj_handle, pos_output, 0)
        ljm.eWriteName(lj_handle, neg_output, voltage_set * -1)
    if voltage_set == 0:
        ljm.eWriteName(lj_handle, pos_output, 0)
        ljm.eWriteName(lj_handle, neg_output, 0)


def graph_dma_voltage(df):
    # Create a selection that chooses the nearest point & selects based on x-value
    nearest = alt.selection(
        type="single",
        nearest=True,
        on="mouseover",
        fields=["DMA Voltage"],
        empty="none",
    )

    line = (
        alt.Chart(df)
        .mark_line()
        .encode(
            x="DMA Voltage:Q",
            y="Electrometer Concentration:Q",
        )
    )

    # Transparent selectors across the chart. This is what tells us
    # the x-value of the cursor
    selectors = (
        alt.Chart(df)
        .mark_point()
        .encode(
            x="DMA Voltage:Q",
            tooltip=["DMA Voltage:Q", "Electrometer Concentration"],
            opacity=alt.value(0),
        )
        .add_selection(nearest)
    )

    # Draw points on the line, and highlight based on selection
    points = line.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )

    # # Draw text labels near the points, and highlight based on selection
    # text = line.mark_text(align='left', dx=5, dy=-5).encode(
    #     text=alt.condition(nearest, 'DMA Voltage:Q', alt.value(' '))
    # )

    # Draw a rule at the location of the selection
    rules = (
        alt.Chart(df)
        .mark_rule(color="gray")
        .encode(
            x="DMA Voltage:Q",
        )
        .transform_filter(nearest)
    )

    # Put the five layers into a chart and bind the data
    dma_voltage = alt.layer(
        line,
        selectors,
        points,
        rules,  # text
    ).properties(width=600, height=300)
    ##########################

    # Create a selection that chooses the nearest point & selects based on x-value
    nearest = alt.selection(
        type="single",
        nearest=True,
        on="mouseover",
        fields=["Time Since Start"],
        empty="none",
    )

    line = (
        alt.Chart(df)
        .mark_line()
        .encode(
            x="Time Since Start:Q",
            y="Electrometer Concentration:Q",
        )
    )

    # Transparent selectors across the chart. This is what tells us
    # the x-value of the cursor
    selectors = (
        alt.Chart(df)
        .mark_point()
        .encode(
            x="Time Since Start:Q",
            tooltip=["Time Since Start:Q", "Electrometer Concentration"],
            opacity=alt.value(0),
        )
        .add_selection(nearest)
    )

    # Draw points on the line, and highlight based on selection
    points = line.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )

    # # Draw text labels near the points, and highlight based on selection
    # text = line.mark_text(align='left', dx=5, dy=-5).encode(
    #     text=alt.condition(nearest, 'DMA Voltage:Q', alt.value(' '))
    # )

    # Draw a rule at the location of the selection
    rules = (
        alt.Chart(df)
        .mark_rule(color="gray")
        .encode(
            x="Time Since Start:Q",
        )
        .transform_filter(nearest)
    )

    # Put the five layers into a chart and bind the data
    time_basis = alt.layer(
        line,
        selectors,
        points,
        rules,  # text
    ).properties(width=600, height=300)
    graphs = alt.vconcat(dma_voltage, time_basis)

    graphs.save(run_filename_avg[:-4] + ".html")
    webbrowser.open_new_tab(
        "file://" + os.path.realpath(run_filename_avg[:-4] + ".html")
    )


root.mainloop()
