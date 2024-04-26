import csv
import tkinter as tk
from datetime import datetime


def create_run_settings(gui_entries, config_file, run_filename):
    run_settings = {
        "dma_mode": gui_entries["dma mode"].get(),
        "step_time": gui_entries["streaming interval"].get(),
        # "flow_rate": gui_entries["electrometer flow"].get(),
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
        "elec_flow_read": config_file["lj_inputs"]["elec_flow_read"],
        "filename_raw": run_filename,
        "filename_avg": run_filename[:-4] + "_avg.csv",
    }

    if gui_entries["dma mode"].get() == "multi_voltage":
        voltage_list = gui_entries["multi voltage list"].get(1.0, tk.END)

        run_settings.update(
            {
                "num_measurements": gui_entries["repeat measure"].get(),
                "voltage_list": list(map(int, voltage_list.split(","))),
            }
        )

    if gui_entries["dma mode"].get() == "voltage_scan":
        run_settings.update(
            {
                "scan_start": gui_entries["scan start volt"].get(),
                "scan_end": gui_entries["scan end volt"].get(),
                "scan_step": gui_entries["scan volt step"].get(),
            }
        )

    if gui_entries["dma mode"].get() == "single_voltage":
        run_settings.update(
            {"set_volt": gui_entries["single voltage value"].get()}
        )
    return run_settings


def create_filename(gui_filename):
    start_time = datetime.now()
    dt_string = start_time.strftime("%Y_%m_%d_%H_%M_%S")
    filename = "DMA_{datetime}.csv".format(datetime=dt_string)

    # Update GUI
    gui_filename.delete("1.0", "1.end")
    gui_filename.insert("1.0", filename)

    return filename


def write_header(run_filename, run_filename_avg):
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
