#!/bin/sh

function help () {
echo "smooth_bathy.sh - A script that smooths the bathy areas of DEM (below 0) and merges back with original, unsmoothed topo."
	echo
	echo "Usage: $0 DEMs_list smooth_factor"
	echo
	echo "* DEMs_list: <file containing names of DEMs to do smoothing>"
	echo "* smooth_factor: <smooth_factor for Gaussian Blur, value of 10 provides reasonable results>"
}

#see if 2 parameters were provided
#show help if not
if [ ${#@} == 2 ]; 
then
	#User inputs    	
	tiles=$1
	smooth_factor=$2

	echo "list of DEMs is in" $tiles
	echo "smooth factor is" $smooth_factor
	# Get Tile Name
	IFS=,
	sed -n '/^ *[^#]/p' $tiles |
	while read -r line
	do
	name_full=$(echo $line | awk '{print $1}')
	name="${name_full:0:-4}"

	echo "Smoothing Bathy in " $name

	echo "Separating Bathy and Topo"
	gdal_calc.py -A $name_full --outfile=$name"_bathy_1_0.tif" --calc="0*(A>0)" --calc="1*(A<=0)"
	gdal_calc.py -A $name_full -B $name"_bathy_1_0.tif" --outfile=$name"_bathy.tif" --calc="A*B"
	gdal_calc.py -A $name_full --outfile=$name"_topo_tmp.tif" --calc="A*(A>0)"
	gdal_calc.py -A $name"_bathy_1_0.tif"  --outfile=$name"_bathy_999999.tif" --calc="A*999999"
	gdal_calc.py -A $name"_topo_tmp.tif" -B $name"_bathy_999999.tif" --outfile=$name"_topo.tif" --calc="A+B"

	echo "Smoothing Bathy in DEM"
	smooth_dem.py $name"_bathy.tif" $smooth_factor

	echo "Merging Smoothed Bathy back with Original Topo "
	gdal_merge.py -o $name"_b_smooth_"$smooth_factor".tif" $name"_bathy_smooth_"$smooth_factor".tif" $name"_topo.tif" -n 999999 -co "COMPRESS=DEFLATE" -co "PREDICTOR=3" -co "TILED=YES"

	rm $name"_bathy_1_0.tif"
	rm $name"_bathy.tif"
	rm $name"_topo_tmp.tif"
	rm $name"_bathy_999999.tif"
	rm $name"_topo.tif"
	rm $name"_bathy_smooth_"$smooth_factor".tif"

	done

else
	help

fi
