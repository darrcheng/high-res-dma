from labjack import ljm
from . import startutilities


def voltage_select(
    run_settings,
    previous_voltage,
    scan_finished,
    sample_index,
    gui_entry_list,
    config_file,
    single_voltage_update,
):
    # Multiple Voltages
    if run_settings["dma_mode"] == "multi_voltage":
        sample_number = int(sample_index / run_settings["num_measurements"])
        if sample_number > len(run_settings["voltage_list"]) - 1:
            scan_finished = True
            current_voltage = 0
        else:
            current_voltage = run_settings["voltage_list"][sample_number]
            sample_index += 1

    # Voltage Scan Setting
    if run_settings["dma_mode"] == "voltage_scan":
        if run_settings["scan_start"] <= run_settings["scan_end"]:
            if previous_voltage > run_settings["scan_end"]:
                scan_finished = True
            current_voltage = (
                run_settings["scan_start"]
                + run_settings["scan_step"] * sample_index
            )
        else:
            if previous_voltage < run_settings["scan_end"]:
                scan_finished = True
            current_voltage = (
                run_settings["scan_start"]
                + run_settings["scan_step"] * sample_index * -1
            )
        sample_index += 1

    # Single Voltage
    if run_settings["dma_mode"] == "single_voltage":
        current_voltage = run_settings["set_volt"]
        if single_voltage_update == True:
            run_settings = startutilities.create_run_settings(
                gui_entry_list, config_file, run_settings["filename_avg"]
            )
            single_voltage_update = False
    return (
        run_settings,
        scan_finished,
        current_voltage,
        sample_index,
        single_voltage_update,
    )


def ultravolt_voltage_set(voltage_set, lj_handle, neg_output, pos_output):
    """Sets the bipolar ultravolt voltage"""
    if voltage_set > 0:
        ljm.eWriteName(lj_handle, pos_output, voltage_set)
        ljm.eWriteName(lj_handle, neg_output, 0)
    elif voltage_set < 0:
        ljm.eWriteName(lj_handle, pos_output, 0)
        ljm.eWriteName(lj_handle, neg_output, voltage_set * -1)
    elif voltage_set == 0:
        ljm.eWriteName(lj_handle, pos_output, 0)
        ljm.eWriteName(lj_handle, neg_output, 0)
