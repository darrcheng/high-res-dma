from labjack import ljm
from datetime import datetime  # Pulls current time from system
from datetime import timedelta  # Calculates difference in time
import time
import csv
import tkinter as tk
from tkinter import ttk
import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import configparser
import pandas as pd
import os

from dmafnc import *

# import yaml

root = tk.Tk()

config_file = configparser.ConfigParser()
config_file.read(r"test_config.ini")


# TKINTER defining the callback function (observer)
def my_callback(var, index, mode):
    print("Blower Speed: {}".format(blower_set.get()))


def start_run():
    # Manage start/stop button
    start_button.configure(text="Stop", command=lambda: stop_run(run_settings))
    global interrupt
    interrupt = False

    # Create and change date subfolder
    data_directory = config_file["general"]["data_directory"]
    day = datetime.strftime(datetime.now(), "%Y-%m-%d")
    data_directory_date = os.path.join(data_directory, day)
    print(data_directory_date)
    os.makedirs(data_directory_date, exist_ok=True)
    os.chdir(data_directory_date)

    # Create filename
    run_filename = startutilities.create_filename(
        gui_entry_list["output filename"]
    )
    run_filename_avg = run_filename[:-4] + "_avg.csv"
    startutilities.write_header(run_filename, run_filename_avg)

    # Clear graph
    figure1.cla()

    # Configure run settings
    run_settings = startutilities.create_run_settings(
        gui_entry_list, config_file, run_filename
    )

    run_program(
        datetime.now(),
        run_settings,
        datetime_old=None,
        dma_voltage_list=[],
        time_from_start_list=[],
        electrometer_conc_list=[],
    )


def stop_run(run_settings):
    global interrupt
    interrupt = True
    start_button.configure(text="Start", command=start_run)
    df = pd.read_csv(run_settings["filename_avg"])
    graphing.graph_dma_voltage(df, run_settings["filename_avg"])

    # Reset Voltage to 0 at the end of a run


def update_run_settings():
    global single_voltage_update
    single_voltage_update = True


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


# Blower Control
blower_control_frame = ttk.Frame(root)
blower_control_frame.grid(row=0, column=0)
ttk.Label(
    blower_control_frame, text="Blower Control", font=("Helvetica", 12, "bold")
).grid(row=0, column=0, pady=(0, 5), columnspan=4)

blower_set = tk.StringVar()
ttk.Label(blower_control_frame, text="Blower Set RPM: ").grid(row=1, column=0)
ttk.Entry(blower_control_frame, textvariable=blower_set, width=13).grid(
    row=1, column=1, padx=(0, 20)
)
blower_set.trace_add("write", my_callback)

ttk.Label(blower_control_frame, text="Blower RPM: ").grid(
    row=1, column=2, padx=(20, 0)
)
blower_actual = tk.Text(blower_control_frame, width=10, height=1)
blower_actual.grid(row=1, column=3, pady=2)

# Program Header
voltage_control_frame = ttk.Frame(root)
voltage_control_frame.grid(row=1, column=0)
ttk.Label(
    voltage_control_frame,
    text="DMA Voltage Control",
    font=("Helvetica", 12, "bold"),
).grid(row=0, column=0, pady=(0, 5))

# Frame for setting logging frequency
FreqFrame = ttk.Frame(voltage_control_frame)
FreqFrame.grid(row=1, column=0, padx=0)

# Insert Filename
ttk.Label(FreqFrame, text="Filename: ").grid(row=0, column=0, sticky="W")
gui_filename = tk.Text(FreqFrame, width=30, height=1)
gui_filename.grid(row=0, column=1, pady=2)
gui_filename.insert("1.0", "No Filename")

# Input Electrometer Flow Rate
electrometer_flow = tk.IntVar()
electrometer_flow.set(config_file["general"]["electrometer_flow"])
ttk.Label(FreqFrame, text="Input Flow Rate: ").grid(row=1, column=0, sticky="W")
ElectrometerFlow = ttk.Entry(
    FreqFrame, textvariable=electrometer_flow, width=13
).grid(row=1, column=1, sticky="W")
electrometer_flow.trace_add("write", my_callback)


# Data logging frequency entry box and labels
streamingInterval = tk.IntVar()
streamingInterval.set(config_file["general"]["data_frequency"])
ttk.Label(FreqFrame, text="Data frequency (ms): ").grid(
    row=2, column=0, sticky="W"
)
LoggingFreq = ttk.Entry(
    FreqFrame, textvariable=streamingInterval, width=13
).grid(row=2, column=1, sticky="w")
streamingInterval.trace_add("write", my_callback)

# Frame for setting Bertan Voltages
BertanFrame = ttk.Frame(voltage_control_frame)
BertanFrame.grid(row=2, column=0, sticky="NW", pady=5)

# Radiobuttons for selecting mode
dma_mode = tk.StringVar()
dma_mode.set("voltage_scan")


# DMA Scanning Options
scan_frame = ttk.Frame(BertanFrame)
scan_frame.grid(row=1, column=0, sticky="N", padx=5)
voltage_scan = ttk.Radiobutton(
    scan_frame, text="Voltage Scan", variable=dma_mode, value="voltage_scan"
).grid(row=0, column=0, columnspan=2, pady=(0, 5))
scan_start_volt = tk.IntVar()
scan_start_volt.set(config_file["voltage_scan"]["start_voltage"])
ttk.Label(scan_frame, text="Start Voltage: ").grid(row=1, column=0)
ttk.Entry(scan_frame, textvariable=scan_start_volt, width=13).grid(
    row=1, column=1
)
scan_end_volt = tk.IntVar()
scan_end_volt.set(config_file["voltage_scan"]["end_voltage"])
ttk.Label(scan_frame, text="End Voltage: ").grid(row=2, column=0)
ttk.Entry(scan_frame, textvariable=scan_end_volt, width=13).grid(
    row=2, column=1
)
scan_volt_step = tk.IntVar()
scan_volt_step.set(config_file["voltage_scan"]["voltage_step"])
ttk.Label(scan_frame, text="Voltage Step: ").grid(row=3, column=0)
ttk.Entry(scan_frame, textvariable=scan_volt_step, width=13).grid(
    row=3, column=1
)

# DMA Single Voltage Options
single_voltage_frame = ttk.Frame(BertanFrame)
single_voltage_frame.grid(row=1, column=1, sticky="N", padx=5)
single_voltage = ttk.Radiobutton(
    single_voltage_frame,
    text="Single Voltage",
    variable=dma_mode,
    value="single_voltage",
).grid(row=0, column=0, columnspan=2, pady=(0, 5))
single_voltage_value = tk.IntVar()
single_voltage_value.set(config_file["single_voltage"]["voltage"])
ttk.Label(single_voltage_frame, text="Voltage: ").grid(row=1, column=0)
ttk.Entry(
    single_voltage_frame, textvariable=single_voltage_value, width=13
).grid(row=1, column=1)
single_voltage_update_butt = ttk.Button(
    single_voltage_frame, text="Update", width=10, command=update_run_settings
)
single_voltage_update_butt.grid(row=2, column=0, columnspan=2, pady=5, ipady=1)
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
multi_voltage_list = tk.Text(multi_voltage_frame, width=10, height=3)
multi_voltage_list.insert(1.0, config_file["multiple_voltages"]["set_voltages"])
multi_voltage_list.grid(row=1, column=1, pady=2)
ys = ttk.Scrollbar(
    multi_voltage_frame, orient="vertical", command=multi_voltage_list.yview
)
multi_voltage_list["yscrollcommand"] = ys.set
ys.grid(column=2, row=1, sticky="ns")
repeat_measure = tk.IntVar()
repeat_measure.set(config_file["multiple_voltages"]["repeat_samples"])
ttk.Label(multi_voltage_frame, text="# Measurements : ").grid(row=2, column=0)
ttk.Entry(multi_voltage_frame, textvariable=repeat_measure, width=13).grid(
    row=2, column=1
)

# Monitoring
monitor_frame = ttk.Frame(voltage_control_frame)
monitor_frame.grid(row=3, column=0)
ttk.Label(monitor_frame, text="Time: ").grid(row=0, column=0)
current_time_gui = tk.Text(monitor_frame, width=10, height=1)
current_time_gui.grid(row=0, column=1, padx=10)  # change e0 to BertanStart
current_time_gui.insert("1.0", "00:00:00")
ttk.Label(monitor_frame, text="Temperature (C): ").grid(row=1, column=0)
sheath_temp_gui = tk.Text(monitor_frame, width=10, height=1)
sheath_temp_gui.grid(row=1, column=1, padx=10)  # change e0 to BertanStart
sheath_temp_gui.insert("1.0", "0.00")
ttk.Label(monitor_frame, text="Relative Hum. (%): ").grid(row=2, column=0)
sheath_rh_gui = tk.Text(monitor_frame, width=10, height=1)
sheath_rh_gui.grid(row=2, column=1, padx=10)  # change e0 to BertanStart
sheath_rh_gui.insert("1.0", "0.00")
ttk.Label(monitor_frame, text="Set Voltage (V): ").grid(row=3, column=0)
set_voltage_gui = tk.Text(monitor_frame, width=10, height=1)
set_voltage_gui.grid(row=3, column=1, padx=10)  # change e0 to BertanStart
set_voltage_gui.insert("1.0", "0.00")
ttk.Label(monitor_frame, text="Actual Voltage (V): ").grid(row=4, column=0)
dma_voltage_gui = tk.Text(monitor_frame, width=10, height=1)
dma_voltage_gui.grid(row=4, column=1)  # change t0 to BertanVoltage
dma_voltage_gui.insert("1.0", "0.00")
ttk.Label(monitor_frame, text="Electrospray Current: ").grid(row=5, column=0)
electrospray_output = tk.Text(monitor_frame, width=10, height=1)
electrospray_output.grid(row=5, column=1)  # change t1 to ElectroVoltage
electrospray_output.insert("1.0", "0.00")
ttk.Label(monitor_frame, text="Electrometer Voltage (V): ").grid(
    row=6, column=0
)
electrometer_conc_gui = tk.Text(monitor_frame, width=10, height=1)
electrometer_conc_gui.grid(row=6, column=1)  # change t1 to ElectroVoltage
electrometer_conc_gui.insert("1.0", "0.00")

start_button = ttk.Button(
    monitor_frame, text="Start", width=5, command=start_run
)
start_button.grid(row=7, column=0, columnspan=2, pady=10, ipady=1)

gui_entry_list = {
    "dma mode": dma_mode,
    "streaming interval": streamingInterval,
    "electrometer flow": electrometer_flow,
    "multi voltage list": multi_voltage_list,
    "repeat measure": repeat_measure,
    "scan start volt": scan_start_volt,
    "scan end volt": scan_end_volt,
    "scan volt step": scan_volt_step,
    "single voltage value": single_voltage_value,
    "output filename": gui_filename,
}

gui_text_list = {
    "time": current_time_gui,
    "sheath temp": sheath_temp_gui,
    "sheath rh": sheath_rh_gui,
    "set voltage": set_voltage_gui,
    "dma voltage": dma_voltage_gui,
    "electrospray": electrospray_output,
    "concentration": electrometer_conc_gui,
}

############ Open Labjack ##############################
handle = ljm.openS(
    "T7", "ANY", "ANY"
)  # T7 device, Any connection, Any identifier
info = ljm.getHandleInfo(handle)
print(
    "Opened a LabJack with Device type: %i, Connection type: %i,\n"
    "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i"
    % (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5])
)

ljm.eWriteName(handle, "AIN2_RESOLUTION_INDEX", 8)
ljm.eWriteName(handle, "AIN2_RANGE", 1.0)


########################### Main Program ###############################


def run_program(
    record_start,
    run_settings,
    datetime_old=None,
    time_from_start_list=[],
    dma_voltage_list=[],
    electrometer_conc_list=[],
    previous_voltage=0,
    sample_index=0,
):
    runtime_start = datetime.now()
    # Enable Ultravolt
    ljm.eWriteName(handle, "DAC0", 3)

    # Other Constants
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
    else:
        next_start = datetime_old + timedelta(
            seconds=run_settings["step_time"] / 1000
        )
        # print(datetime_old)
        # print(next_start)
        # print(datetime.now())
        datetime_old = next_start
        sleep_time = (next_start - datetime.now()).total_seconds()
        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            print(f"Slow! {datetime.now()}")
    # elapsed_milliseconds = 0
    # while elapsed_milliseconds < run_settings["step_time"]:
    #     datetime_new = datetime.now()
    #     elapsed_milliseconds = int(
    #         (datetime_new - datetime_old).total_seconds() * 1000
    #     )
    # datetime_old = datetime_old + timedelta(
    #     seconds=run_settings["step_time"] / 1000
    # )

    # Stop run if stop button pressed
    if interrupt:
        runvoltage.ultravolt_voltage_set(
            0,
            handle,
            run_settings["dma_write_neg"],
            run_settings["dma_write_pos"],
        )
        ljm.eWriteName(handle, "DAC0", 0)
        return

    # Determine what voltage to set
    scan_finished = False

    global single_voltage_update
    # Multiple Set Voltages
    (
        run_settings,
        scan_finished,
        current_voltage,
        sample_index,
        single_voltage_update,
    ) = runvoltage.voltage_select(
        run_settings,
        previous_voltage,
        scan_finished,
        sample_index,
        gui_entry_list,
        config_file,
        single_voltage_update,
    )

    # Stop run if scan is finished
    if scan_finished:
        stop_run(run_settings)
        runvoltage.ultravolt_voltage_set(
            0,
            handle,
            run_settings["dma_write_neg"],
            run_settings["dma_write_pos"],
        )
        ljm.eWriteName(handle, "DAC0", 0)
        return

    # Set new voltage
    if current_voltage != previous_voltage:
        runvoltage.ultravolt_voltage_set(
            current_voltage / run_settings["voltage_factor_dma"],
            handle,
            run_settings["dma_write_neg"],
            run_settings["dma_write_pos"],
        )
        previous_voltage = current_voltage

    repeat_readings = 0
    dwell_steps = (
        int(run_settings["step_time"] / run_settings["ms_between_nested"]) * 0.9
    )
    while repeat_readings < dwell_steps:
        # open file
        with open(run_settings["filename_raw"], "a", newline="") as csvfile:
            data_writer = csv.writer(csvfile, delimiter=",")

            # Take Readings
            runutilities.time_tracker(record_start, exact_time, time_from_start)
            electrospray_voltage, electrospray_current = runutilities.read_dma(
                handle,
                run_settings,
                electrometer_conv,
                dma_voltage,
                electrometer_voltage,
                electrometer_conc,
                sheath_flow_temp,
                sheath_flow_rh,
            )

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
            # print(repeat_reading_pause_time)
            if repeat_reading_pause_time > 0:
                root.after(repeat_reading_pause_time)
                # print("pause")

        # Update GUI and increment
        repeat_readings += 1

    # Average Readings for graphing and Summary CSV
    readings = {}
    readings["exact time"] = exact_time[0]
    readings["set voltage"] = current_voltage
    readings["time from start"] = runutilities.average_readings(
        time_from_start, dwell_steps
    )
    readings["dma voltage"] = runutilities.average_readings(
        dma_voltage, dwell_steps
    )
    readings["electrometer volt"] = runutilities.average_readings(
        electrometer_voltage, dwell_steps
    )
    readings["electrometer conc"] = runutilities.average_readings(
        electrometer_conc, dwell_steps
    )

    # Correct RH
    sheath_flow_temp_avg = runutilities.average_readings(
        sheath_flow_temp, dwell_steps
    )
    sheath_flow_rh_avg = runutilities.average_readings(
        sheath_flow_rh, dwell_steps
    )
    v_supply = 5
    sheath_flow_rh_avg = (sheath_flow_rh_avg / v_supply - 0.16) / 0.0062
    sheath_flow_rh_avg = sheath_flow_rh_avg / (
        1.0546 - 0.00216 * sheath_flow_temp_avg
    )
    readings["sheath flow temp"] = sheath_flow_temp_avg
    readings["sheath flow rh"] = sheath_flow_rh_avg
    # print(f"Readings Runtime: {datetime.now() - runtime_start}")

    # Write Averaged Data to CSV
    with open(run_settings["filename_avg"], "a", newline="") as csvfile_avg:
        fieldnames = [
            "exact time",
            "dma voltage",
            "electrometer conc",
            "time from start",
            "electrometer volt",
            "set voltage",
            "sheath flow temp",
            "sheath flow rh",
        ]
        data_writer_avg = csv.DictWriter(
            csvfile_avg, fieldnames=fieldnames, delimiter=","
        )
        data_writer_avg.writerow(readings)

    # Update GUI
    runutilities.update_gui(
        gui_text_list,
        readings,
        electrospray_current,
    )

    # Update lists for graphing
    time_from_start_list.append(readings["time from start"])
    dma_voltage_list.append(readings["dma voltage"])
    electrometer_conc_list.append(readings["electrometer conc"])
    if len(time_from_start_list) > 100:
        time_from_start_list.pop(0)
        dma_voltage_list.pop(0)
        electrometer_conc_list.pop(0)

    # Update Graph
    runutilities.update_graph(
        run_settings,
        time_from_start_list,
        dma_voltage_list,
        electrometer_conc_list,
        figure1,
        plt,
    )

    canvas.draw()

    root.update()
    # print(f"Loop Runtime: {datetime.now() - runtime_start}")

    root.after(
        1,
        lambda: run_program(
            record_start,
            run_settings,
            datetime_old=datetime_old,
            time_from_start_list=time_from_start_list,
            dma_voltage_list=dma_voltage_list,
            electrometer_conc_list=electrometer_conc_list,
            previous_voltage=previous_voltage,
            sample_index=sample_index,
        ),
    )


root.mainloop()
