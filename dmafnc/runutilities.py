from labjack import ljm
from datetime import datetime


def read_dma(
    handle,
    handle1,
    run_settings,
    electrometer_conv,
    dma_voltage,
    electrometer_voltage,
    electrometer_counts,
    electrometer_flow,
    sheath_flow_temp,
    sheath_flow_rh,
):
    dma_voltage.append(
        ljm.eReadName(handle, run_settings["dma_read"])
        * run_settings["voltage_factor_dma"]
    )
    electrospray_voltage = 0
    electrospray_current = 0
    # electrospray_voltage = (
    #     ljm.eReadName(handle, run_settings["electrospray_voltage_read"])
    #     * 5000
    #     / 5
    # )
    # electrospray_current = (
    #     ljm.eReadName(handle, run_settings["electrospray_current_read"])
    #     * 0.005
    #     / 5
    # )
    electrometer_voltage.append(
        ljm.eReadName(handle1, run_settings["electrometer_read"])
    )
    electrometer_counts.append(electrometer_voltage[-1] * electrometer_conv)
    electrometer_flow.append(
        ljm.eReadName(handle, run_settings["elec_flow_read"]) * 2196.9 + 184.31
    )
    # electrometer_conc.append(
    #     electrometer_voltage[-1] * electrometer_conv / run_settings["flow_rate"]
    # )
    sheath_flow_temp.append(
        ljm.eReadName(handle, run_settings["sheath_temp_read"])
        * run_settings["sheath_temp_factor"]
    )

    # elec_flow_vlt = ljm.eReadName(handle, "AIN4")
    # elec_flow = elec_flow_vlt * 2196.9 + 184.31
    # print(elec_flow)
    sheath_flow_rh.append(ljm.eReadName(handle, run_settings["sheath_rh_read"]))
    return electrospray_voltage, electrospray_current


def average_readings(value_list, dwell_steps):
    average_value = sum(value_list) / dwell_steps
    return average_value


def time_tracker(record_start, exact_time, time_list):
    current_time = datetime.now()
    exact_time.append(current_time)
    time_difference = current_time - record_start
    time_list.append(time_difference.total_seconds())


def update_graph(
    run_settings,
    time_from_start_avg,
    dma_voltage_avg,
    electrometer_conc_avg,
    figure1,
    plt,
):
    if (
        run_settings["dma_mode"] == "multi_voltage"
        or run_settings["dma_mode"] == "single_voltage"
    ):
        figure1.cla()
        figure1.plot(time_from_start_avg, electrometer_conc_avg, "b")
        plt.autoscale(True)

    if run_settings["dma_mode"] == "voltage_scan":
        if len(dma_voltage_avg) > 2:
            figure1.plot(dma_voltage_avg[-2:], electrometer_conc_avg[-2:], "b")
        else:
            figure1.plot(dma_voltage_avg, electrometer_conc_avg, "b")


def update_gui(
    gui_text_list,
    readings,
    # exact_time_avg,
    # dma_voltage_avg,
    # electrometer_conc_avg,
    electrospray_current,
    # current_voltage,
    # sheath_temp_avg,
    # sheath_rh_avg,
):
    gui_text_list["time"].delete("1.0", "1.end")
    gui_text_list["time"].insert("1.0", readings["exact time"].strftime("%X"))
    gui_text_list["set voltage"].delete("1.0", "1.end")
    gui_text_list["set voltage"].insert("1.0", "%.2f" % readings["set voltage"])
    gui_text_list["dma voltage"].delete("1.0", "1.end")
    gui_text_list["dma voltage"].insert("1.0", "%.2f" % readings["dma voltage"])
    gui_text_list["concentration"].delete("1.0", "1.end")
    gui_text_list["concentration"].insert(
        "1.0", "%.2f" % readings["electrometer conc"]
    )
    gui_text_list["electrospray"].delete("1.0", "1.end")
    gui_text_list["electrospray"].insert("1.0", "%.2f" % electrospray_current)
    gui_text_list["sheath temp"].delete("1.0", "1.end")
    gui_text_list["sheath temp"].insert(
        "1.0", "%.1f" % readings["sheath flow temp"]
    )
    gui_text_list["sheath rh"].delete("1.0", "1.end")
    gui_text_list["sheath rh"].insert(
        "1.0", "%.0f" % readings["sheath flow rh"]
    )
    gui_text_list["electrometer flow"].delete("1.0", "1.end")
    gui_text_list["electrometer flow"].insert(
        "1.0", "%.1f" % readings["electrometer flow"]
    )
