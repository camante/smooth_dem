#!/usr/bin/env python
import os
import sys
import numpy as np
from scipy.signal import fftconvolve
from gdalconst import *
from osgeo import osr
from osgeo import gdal

_version = "0.0.2"

_license = """
version %s
    """ %(_version)

_usage = """
smooth_dem_bathy.py: A script that smooths the bathy areas of DEM (below 0) and merges back with original, unsmoothed topo.

usage: smooth_dem_bathy.py input-dem [-smooth value]

Options:
  input-dem\tThe input DEM file-name
  -smooth\tValue for the smooth factor; default is 10

  -help\t\tPrint the usage text
  -version\tPrint the version information

Example:
smooth_dem_bathy.py input.tif -smooth 12

smooth_dem_bathy.py v.%s 
""" %(_version)

def gaussian_blur(in_array, size):
    # expand in_array to fit edge of kernel
    padded_array = np.pad(in_array, size, 'symmetric')
    # build kernel
    x, y = np.mgrid[-size:size + 1, -size:size + 1]
    g = np.exp(-(x**2 / float(size) + y**2 / float(size)))
    g = (g / g.sum()).astype(in_array.dtype)
    # do the Gaussian blur
    return fftconvolve(padded_array, g, mode='valid')

# Function to read the original file's projection:
def GetGeoInfo(FileName):
    SourceDS = gdal.Open(FileName, GA_ReadOnly)
    NDV = SourceDS.GetRasterBand(1).GetNoDataValue()
    xsize = SourceDS.RasterXSize
    ysize = SourceDS.RasterYSize
    GeoT = SourceDS.GetGeoTransform()
    Projection = osr.SpatialReference()
    Projection.ImportFromWkt(SourceDS.GetProjectionRef())
    DataType = SourceDS.GetRasterBand(1).DataType
    DataType = gdal.GetDataTypeName(DataType)
    return xsize, ysize, GeoT, Projection, DataType, NDV

# Function to write a new file.
def CreateGeoTiff(Name, Array, driver,
                  xsize, ysize, GeoT, Projection, DataType):
    if DataType == 'Float32':
        DataType = gdal.GDT_Float32
    NewFileName = Name+'.tif'
    # Set nans to the original No Data Value
    #Array[np.isnan(Array)] = NDV
    # Set up the dataset
    DataSet = driver.Create( NewFileName, xsize, ysize, 1, DataType )
    # the '1' is for band 1.
    DataSet.SetGeoTransform(GeoT)
    
    wkt_proj = Projection.ExportToWkt()
    if wkt_proj.startswith("LOCAL_CS"):
        wkt_proj = wkt_proj[len("LOCAL_CS"):]
        wkt_proj = "PROJCS"+wkt_proj
    DataSet.SetProjection(wkt_proj)
    #DataSet.SetProjection( Projection.ExportToWkt() )
    
    # Write the array
    DataSet.GetRasterBand(1).WriteArray( Array )
    #DataSet.GetRasterBand(1).SetNoDataValue(NDV)
    return NewFileName

if __name__ == '__main__':
    
    elev = None
    smooth_factor = 10

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]

        if arg == '-s' or arg == '-smooth' or arg == '--smooth':
            smooth_factor = sys.argv[i+1]
            i = i + 1

        elif arg == '-help' or arg == '--help' or arg == '-h':
            print(_usage)
            sys.exit(1)

        elif arg == '-version' or arg == '--version':
            print('smooth_dem_bathy.py v.%s' %(_version))
            print(_license)
            sys.exit(1)

        elif elev is None:
            elev = arg

        else:
            print(_usage)
            sys.exit(1)

        i = i + 1

    if elev is None:
        print(_usage)
        sys.exit(1)

    if not os.path.exists(elev):
        print("Error: %s is not a valid file" %(elev))
        print(_usage)
        sys.exit(1)
    
    try: smooth_factor = int(smooth_factor)
    except:
        print("Error: %s is not a valid smooth-factor" %(smooth_factor))
        print(_usage)
        sys.exit(1)

    #Create Array
    output_name=elev[:-4]+"_smooth_"+str(smooth_factor)
    xsize, ysize, GeoT, Projection, DataType, NDV = GetGeoInfo(elev)

    print "elev is", elev
    print "smooth factor is", smooth_factor
    print "output_name is", output_name

    elev_g = gdal.Open(elev) #
    elev_array = elev_g.GetRasterBand(1).ReadAsArray(0,0,xsize,ysize) 
    #Set topo values to zero
    elev_array[elev_array > 0] = 0
    print "loaded input dem"

    #Perform smoothing
    smooth_elev=gaussian_blur(elev_array, smooth_factor)
    print "smoothed array"
    
    #Reload original array and merge the topo with the smoothed bathy
    elev_array = elev_g.GetRasterBand(1).ReadAsArray(0,0,xsize,ysize)
    elev_array[elev_array < 0] = 0
    smoothed_array = smooth_elev + elev_array
    elev_g = elev_array = smooth_elev = None
    #Export Tif
    driver = gdal.GetDriverByName('GTiff')
    CreateGeoTiff(output_name, smoothed_array, driver, xsize, ysize, GeoT, Projection, DataType)
    smoothed_array = None
    print "created Smoothed Geotiff"
