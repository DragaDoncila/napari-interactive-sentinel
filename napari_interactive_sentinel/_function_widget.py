import warnings
from napari.types import ImageData, LayerDataTuple
from napari_plugin_engine import napari_hook_implementation
from ._utils import compute_ndvi_layer


@napari_hook_implementation
def napari_experimental_provide_function():
    return get_ndvi_layer

def get_ndvi_layer(red : ImageData, nir: ImageData) -> LayerDataTuple:
    ndvi_levels = compute_ndvi_layer(nir, red)
    return (ndvi_levels, {'name':'NDVI', 'colormap':'summer'}, 'image')