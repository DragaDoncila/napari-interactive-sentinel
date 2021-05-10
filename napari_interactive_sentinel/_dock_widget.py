"""
This module is an example of a barebones QWidget plugin for napari

It implements the ``napari_experimental_provide_dock_widget`` hook specification.
see: https://napari.org/docs/dev/plugins/hook_specifications.html

Replace code below according to your needs.
"""
from napari._qt.qthreading import thread_worker
from napari_plugin_engine import napari_hook_implementation
import numpy as np
from magicgui import magicgui, magic_factory
import dask.array as da
import toolz as tz

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from PyQt5.QtWidgets import QVBoxLayout, QWidget

from napari.qt import progress

@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    return start_profiles

def create_plot_dock(viewer):
        # create the NDVI plot
        with plt.style.context("dark_background"):
            ndvi_canvas = FigureCanvas(Figure(figsize=(5, 3)))
            ndvi_axes = ndvi_canvas.figure.subplots()
            
            ndvi_axes.set_ylim(-1, 1)
            ndvi_axes.set_xlabel("time")
            ndvi_axes.set_ylabel("NDVI")
            ndvi_axes.set_title("NDVI")
            ndvi_canvas.figure.tight_layout()

        # add matplotlib toolbar
        toolbar = NavigationToolbar2QT(ndvi_canvas, viewer.window._qt_window)
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        layout.addWidget(toolbar)
        layout.addWidget(ndvi_canvas)
        viewer.window.add_dock_widget(widget)

        return ndvi_canvas

def get_ndvi(NIR, red, y, x):
    """Get NDVI of a particular pixel"""
    nir_intensities = NIR[:, 0, y, x].astype(np.float32)
    red_intensities = red[:, 0, y, x].astype(np.float32)

    intensity_sum = (nir_intensities + red_intensities)
    intensity_diff = (nir_intensities - red_intensities)

    ndvi =  da.divide(intensity_diff,intensity_sum)
    ndvi[da.isnan(ndvi)] = 0

    return ndvi


@thread_worker
def add_profile(
    pt,
    canvas_widg,
    nir,
    red,
    pbar
):
    #TODO: if not multiscale
    red = red.data[0]
    nir = nir.data[0]

    min_x, min_y = 0, 0
    max_x = red.shape[-1]
    max_y = red.shape[-2]

    ndvi_axes = canvas_widg.figure.axes[0]
    current_lines = ndvi_axes.get_lines()
    if current_lines:
        xs, _ = current_lines[0].get_data()
        all_ys = [line.get_data()[1] for line in current_lines]
    else:
        xs = np.arange(red.shape[0])
        ndvi_axes.set_xlim(xs[0], xs[-1])
        all_ys = []

    if (min_x <= pt[0] <= max_x) and\
         (min_y <= pt[1] <= max_y):
            new_ys = get_ndvi(nir, red, int(pt[0]), int(pt[1]))
            # TODO: set y limits based on all profiles
            all_ys += [new_ys]
            all_ys = np.concatenate(all_ys).flatten()
            minval, maxval = np.min(new_ys), np.max(new_ys)
            range_ = maxval - minval
            centre = (maxval + minval) / 2
            min_y = centre - 1.05 * range_ / 2
            max_y = centre + 1.05 * range_ / 2
            ndvi_axes.set_ylim(min_y, max_y)
            ndvi_axes.plot(xs, new_ys)

    pbar.close()

@tz.curry
def handle_data_change(
    e,
    *args,
    viewer,
    widg,
    red,
    nir,
    pts
):
    if pts.mode == 'add':
        pbar = progress(total=0)
        pt = e.value[-1]
        pbar.set_description(f"NDVI @ ({int(pt[0])}, {int(pt[1])})")
        worker = add_profile(pt, widg, nir, red, pbar)
        worker.start()
        #TODO: elif selected figure out how to move points around
    
# make a bindable function to shut things down
@magicgui
def close_profiles(layer, callback):
    layer.events.data.disconnect(callback)
    layer.mode = 'pan_zoom'


@magic_factory(
        call_button='Start',
        layout='vertical',
        viewer={'visible': False, 'label': ' '},
        )
def start_profiles(
        red: 'napari.layers.Image',
        nir: 'napari.layers.Image',
        viewer : 'napari.viewer.Viewer',
        #TODO: Add picker for layer level
        ):
    mode = start_profiles._call_button.text  # can be "Start" or "Finish"

    if mode == 'Start':
        # make a points layer for image
        pts_layer = viewer.add_points(
                ndim=2,
                name='NDVI_pts',
        )

        widget = create_plot_dock(viewer)
        callback = handle_data_change(
            viewer=viewer,
            widg=widget,
            red=red,
            nir=nir,
            pts=pts_layer
        )
        pts_layer.events.data.connect(callback)

        viewer.layers.selection.clear()
        viewer.layers.selection.add(pts_layer)
        pts_layer.mode = 'add'

        # TODO: close properly...
        close_profiles.layer.bind(pts_layer)
        close_profiles.callback.bind(callback)

        # change the button/mode for next run
        start_profiles._call_button.text = 'Finish'
    else:  # we are in Finish mode
        close_profiles()
        start_profiles._call_button.text = 'Start'