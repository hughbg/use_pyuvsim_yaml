import numpy as np
from hera_sim import io
import yaml, csv
from astropy.time import Time
from astropy.coordinates import EarthLocation

from pyuvsim import AnalyticBeam
from vis_cpu import conversions

def load_config(fname, correct_radec = False):
    """
    Load config file for hera_sim.

    fname: yaml file name

    correct_radec: Correct source locations so that vis_cpu uses the right frame (default False)
    """

    with open(fname, "r") as conf:
        config = yaml.load(conf.read(), Loader=yaml.FullLoader)
        
    # Simple load of antennas which assumes CSV in the right format
    ants = {}
    ant_to_beam = []
    with open(config["telescope"]["array_layout"]) as fp:
        lines = fp.readlines()
    i = 0
    for line in lines:
        l = line.split()
        if len(l) > 0 and l[0] != "Name":
            ant_to_beam.append(int(l[2]))
            ants[i] = ( float(l[3]), float(l[4]), float(l[5]))
            i += 1

    # Observing parameters in a UVData object.
    uvdata = io.empty_uvdata(
        Nfreqs = config["freq"]["Nfreqs"],             
        start_freq = config["freq"]["start_freq"],
        channel_width = config["freq"]["channel_width"],
        start_time = config["time"]["start_time"],
        integration_time = config["time"]["integration_time"],
        Ntimes = config["time"]["Ntimes"],
        array_layout = ants,
        polarization_array = np.array([ "XX", "YY", "XY", "YX" ]),
        Npols = 4
    )
    
    # Simple load of sources which assumes CSV in the right format
          
    sources = np.genfromtxt(config["sources"]["catalog"], dtype=str, skip_header=1)
    if sources.ndim == 1: 
        sources = np.expand_dims(sources, 0)          # Make list of lists

    sources = sources[:, 1:].astype(float)            # Ignore source ids

    if sources.shape[1] == 4: 
        # There is no spectral index, add the column.
        print("No spectral index, setting to 0")
        sources = np.append(sources, np.zeros((sources.shape[0], 1)), axis=1)
    
    ra_dec = np.deg2rad(sources[:, :2])

    # calculate source fluxes 
    freqs = np.unique(uvdata.freq_array)
    flux = (freqs[:, np.newaxis]/sources[:,3])**sources[:,4].T*sources[:,2].T   

    with open(config["telescope"]["telescope_config_name"], "r") as conf:
        telescope = yaml.load(conf.read(), Loader=yaml.FullLoader)

    if correct_radec:
        loc = telescope["telescope_location"][1:-1].split(",")

        # Correct source locations so that vis_cpu uses the right frame
        obstime = Time(config["time"]["start_time"], format="jd", scale="utc")

        location = EarthLocation.from_geodetic(lat=float(loc[0]), lon=float(loc[1]), height=float(loc[2]))

        ra_new, dec_new = conversions.equatorial_to_eci_coords(
            ra_dec[:, 0], ra_dec[:, 1], obstime, location, unit="rad", frame="icrs")
        
        ra_dec = np.column_stack((ra_new, dec_new))


    # When this issue gets fixed this will need to change.
    defined_beams = {}
    for id in telescope["beam_paths"].keys():
        
        # The spec could be in a couple of different formats, one is a str
        # and the other is a dict with an option. Get the values.
        if isinstance(telescope["beam_paths"][id], str):
            beam_type = telescope["beam_paths"][id] 
            options = {}
        else:
            beam_type = telescope["beam_paths"][id]["type"]
            del telescope["beam_paths"][id]["type"]
            options = telescope["beam_paths"][id]
            
        defined_beams[id] = AnalyticBeam(beam_type, **options)
        
    # Now give each antenna the right beam
    beams = [ None for i in range(len(ant_to_beam)) ]
    for i in range(len(ant_to_beam)):
        beams[i] = defined_beams[ant_to_beam[i]]
    beam_ids = list(range(len(ant_to_beam)))
    

    # output file
    outfile = config["filing"]["outdir"] + "/" + config["filing"]["outfile_name"] + "_herasim." + config["filing"]["output_format"]
    
    return uvdata, beams, beam_ids, freqs, ra_dec, flux, outfile
