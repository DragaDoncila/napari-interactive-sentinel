
# Pixel Driller

The goal of pixel driller is to provide a variety of analysis functions
on satellite images stacked across time. In particular, pixel driller
allows you to select a pixel on your `(t, y, x)` satellite image layer
and compute the analysis profile of that pixel over time.

Currently, only NDVI is provided as an analysis function, but more
will be added over time!

# Overview

Each widget assumes the different bands of your satellite image cube
have been loaded as separate layers into napari. 

This means the file format of your images is not relevant. The only
restriction on these images is that the entire cube is loaded into 
napari in `(t, y, x)` axis order.

![Image cube axis order](https://i.imgur.com/fgqXvSU.png)

# get_ndvi_layer

The first widget provided by this plugin allows you to select the 
relevant bands for your analysis function (red and NIR for NDVI) and 
click Run.

Once processing is complete, a new layer will be added to the viewer
showing you the NDVI overlay of your images. If you have a particularly
high resolution image with multiple timepoints, consider using 
[Dask arrays](https://docs.dask.org/en/latest/array.html)
to enable lazy computation.

https://user-images.githubusercontent.com/17995243/125924612-67797625-5cf3-463d-81df-121be00bca5d.mp4


# NDVI_profiles

This widget again allows you to select the relevant bands from your
layer list for analysis.

Once you click Start, a new napari Points layer is added to the viewer,
as well as a dock widget displaying a blank matplotlib canvas.

![Points layer and plotting canvas added](https://i.imgur.com/ECck01w.png)

You can click anywhere on the Points layer to add a point to the canvas.
Once a point is added, napari will compute the NDVI profile of that pixel
over time, based on the layers previously selected. 

Once computation is complete, the profile will be added to the matplotlib
canvas. You can move the point around and the profile will be recomputed
based on the new location (once mouse drag is complete).

Alternatively, you can add more points, and their profiles will be 
added to the plotting canvas for inspection.

https://user-images.githubusercontent.com/17995243/125924762-e3cf036e-675c-45b1-9671-0ae9f55b8765.mp4

Note that the matplotlib canvas also has the matplotlib toolbar loaded.
This means you can navigate around, and save the profiles, as you would
expect of a standard matplotlib plot.
