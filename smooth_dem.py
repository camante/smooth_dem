#!/usr/bin/env python
import numpy as np
from scipy.signal import fftconvolve
import gdal
from gdalconst import *
from osgeo import osr
import sys

print "loaded modules"

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
    #NDV = SourceDS.GetRasterBand(1).GetNoDataValue()
    xsize = SourceDS.RasterXSize
    ysize = SourceDS.RasterYSize
    GeoT = SourceDS.GetGeoTransform()
    Projection = osr.SpatialReference()
    Projection.ImportFromWkt(SourceDS.GetProjectionRef())
    DataType = SourceDS.GetRasterBand(1).DataType
    DataType = gdal.GetDataTypeName(DataType)
    return xsize, ysize, GeoT, Projection, DataType

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

#Create Array
#input from shell script
elev=str(sys.argv[1])
smooth_factor=int(sys.argv[2])
output_name=elev[:-4]+"_smooth_"+str(smooth_factor)

print "elev is", elev
print "smooth factor is", smooth_factor
print "output_name is", output_name

elev_g = gdal.Open(elev) #
elev_cols = elev_g.RasterXSize
elev_rows = elev_g.RasterYSize
elev_array = elev_g.GetRasterBand(1).ReadAsArray(0,0,elev_cols,elev_rows) 
cols = elev_g.RasterXSize
rows = elev_g.RasterYSize

#Load from saved
orig_elev_array = elev_g.GetRasterBand(1).ReadAsArray(0,0,elev_cols,elev_rows) 
print "loaded array"

#Perform smoothing
smooth_elev=gaussian_blur(orig_elev_array, smooth_factor)
print "smoothed array"

#Export Tif
xsize, ysize, GeoT, Projection, DataType = GetGeoInfo(elev) 
driver = gdal.GetDriverByName('GTiff')

CreateGeoTiff(output_name, smooth_elev, driver, xsize, ysize, GeoT, Projection, DataType)
print "Created Smoothed Geotiff"
