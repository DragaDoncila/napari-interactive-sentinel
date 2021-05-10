import numpy as np
import dask.array as da
import warnings
import matplotlib.pyplot as plt

from matplotlib.backends.backend_qt5agg import FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QVBoxLayout, QWidget

from napari.qt import thread_worker


def get_ndvi_profile(NIR, red, y, x):
    """Get NDVI of a particular pixel"""
    nir_intensities = NIR[:, 0, y, x].astype(np.float32)
    red_intensities = red[:, 0, y, x].astype(np.float32)

    intensity_sum = nir_intensities + red_intensities
    intensity_diff = nir_intensities - red_intensities
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ndvi = da.divide(intensity_diff, intensity_sum)
        ndvi[da.isnan(ndvi)] = 0

    return ndvi


def compute_ndvi_layer(NIR, red):
    """Get multiscale NDVI layer for display"""
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        ndvi_levels = []
        for i in range(len(NIR)):
            current_nir = NIR[i].astype(np.float32)
            current_red = red[i].astype(np.float32)
            intensity_sum = current_nir + current_red
            intensity_diff = current_nir - current_red
            ndvi_layer = da.divide(intensity_diff, intensity_sum)
            ndvi_layer = da.nan_to_num(ndvi_layer)
            ndvi_levels.append(ndvi_layer)
    return ndvi_levels


def set_axes_lims(ndvi_axes, all_ys):
    all_ys = np.concatenate(all_ys).flatten()
    minval, maxval = np.min(all_ys), np.max(all_ys)
    range_ = maxval - minval
    centre = (maxval + minval) / 2
    min_y = centre - 1.05 * range_ / 2
    max_y = centre + 1.05 * range_ / 2
    ndvi_axes.set_ylim(min_y, max_y)


def create_plot_dock(viewer):
    # create the NDVI plot
    with plt.style.context("dark_background"):
        # cycler = plt.cycler("color", plt.cm.cool(np.linspace(0, 1, 5)))
        ndvi_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        ndvi_axes = ndvi_canvas.figure.subplots()
        # ndvi_axes.set_prop_cycle(cycler)

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
