from napari.types import LayerDataTuple
from napari.layers import Image
from napari_plugin_engine import napari_hook_implementation
from ._utils import compute_ndvi_layer


@napari_hook_implementation
def napari_experimental_provide_function():
    return get_ndvi_layer


def get_ndvi_layer(red: Image, nir: Image) -> LayerDataTuple:
    ndvi_levels = compute_ndvi_layer(nir.data, red.data)
    return (
        ndvi_levels,
        {
            "name": "NDVI", 
            "colormap": "RdYlGn", 
            "contrast_limits": (0, 1),
            "scale": red.scale
        },
        "image",
    )
