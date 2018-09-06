# smooth_dem
Scripts to smooth DEM and reduce pimples/artifacts

Files Below:

smooth_dem.py: The main python script that smooths a DEM using a Gaussian Blur.

smooth_bathy.sh: A shell script that separates bathy (below zero) from topo and only smooths the bathy. Also allows for batch processing of multiple files by calling a file that has a list of the tifs.
