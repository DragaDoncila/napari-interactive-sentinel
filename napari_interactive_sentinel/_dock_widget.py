"""
This module provides an interactive widget for computing NDVI profiles over time
of selected pixels
"""
from napari._qt.qthreading import thread_worker
from napari_plugin_engine import napari_hook_implementation
from magicgui import magic_factory
import toolz as tz

from napari.qt import progress
from ._utils import get_ndvi, set_axes_lims, create_plot_dock

LAST_MOVE_POINT = []

@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    return start_profiles

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
                all_ys += [new_ys]
                set_axes_lims(ndvi_axes, all_ys)
                ndvi_axes.plot(xs, new_ys)

                canvas_widg.draw_idle()
        pbar.close()

@tz.curry
def handle_data_add(
    e,
    *args,
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

def handle_points_move(e):
    LAST_MOVE_POINT.append((e.idx, e.coord))

def move_profile(move_info, red, nir, canvas_widget):
    pt_index, coord = move_info
    pt_index = pt_index[0]

    red = red.data[0]
    nir = nir.data[0]

    min_x, min_y = 0, 0
    max_x = red.shape[-1]
    max_y = red.shape[-2]

    if (min_x <= coord[0] <= max_x) and\
        (min_y <= coord[1] <= max_y):
        ndvi_axes = canvas_widget.figure.axes[0]
        current_lines = ndvi_axes.get_lines()   
        # find the line we need to move
        line_to_move = current_lines[pt_index]

        all_ys = [line.get_data()[1] for line in current_lines if line is not line_to_move] 
        new_ys = get_ndvi(nir, red, int(coord[0]), int(coord[1]))
        all_ys += [new_ys]
        set_axes_lims(ndvi_axes, all_ys)
        line_to_move.set_ydata(new_ys)
        
        canvas_widget.draw_idle()

@tz.curry
def move_release(
    pts,
    e,
    *args,
    red,
    nir,
    canvas_widget
):
    global LAST_MOVE_POINT
    moved = False
    # yield mouse press
    yield
    while e.type == 'mouse_move':
        moved = True
        yield
    # on release
    if pts.mode == 'select' and moved:
        move_profile(LAST_MOVE_POINT[-1], red, nir, canvas_widget)
        LAST_MOVE_POINT = []

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
        #TODO: make points big

        widget = create_plot_dock(viewer)
        callback = handle_data_add(
            widg=widget,
            red=red,
            nir=nir,
            pts=pts_layer
        )
        pts_layer.events.data.connect(callback)
        pts_layer.events.move.connect(handle_points_move)

        move_cbk = move_release(
            red=red,
            nir=nir,
            canvas_widget=widget
        )
        pts_layer.mouse_drag_callbacks.append(move_cbk)

        viewer.layers.selection.clear()
        viewer.layers.selection.add(pts_layer)

        pts_layer.mode = 'add'

        # TODO: close properly...
        start_profiles._pts_layer = pts_layer
        start_profiles._callback = callback

        # change the button/mode for next run
        start_profiles._call_button.text = 'Finish'
    else:  # we are in Finish mode
        close_profiles(start_profiles._pts_layer, start_profiles._callback)
        start_profiles._call_button.text = 'Start'




# from magicgui.widgets import FunctionGui

# class StartProfiles(FunctionGui):
#     def __init__(self):
#         super().__init__(start_profiles, call_button='Start', param_options={'viewer': {'visible': False, 'label': ' '}})

