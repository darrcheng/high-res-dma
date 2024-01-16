import altair as alt
import webbrowser
import os


def graph_dma_voltage(df, run_filename_avg):
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
    points = line.mark_point().encode(opacity=alt.condition(nearest, alt.value(1), alt.value(0)))

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
    points = line.mark_point().encode(opacity=alt.condition(nearest, alt.value(1), alt.value(0)))

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
    webbrowser.open_new_tab("file://" + os.path.realpath(run_filename_avg[:-4] + ".html"))
