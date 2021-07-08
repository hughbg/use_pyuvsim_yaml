import numpy as np
from hera_sim import io
import yaml, csv
from astropy.time import Time
from astropy.coordinates import EarthLocation

from pyuvsim import AnalyticBeam
from vis_cpu import conversions

correct_radec = True

def load_config(fname, correct_radec = False):
    """
    Load config file for hera_sim.

    fname: yaml file name
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
    
        # Simple load of antennas which assumes CSV in the right format
    sources = []
    with open(config["sources"]["catalog"]) as fp:
        lines = fp.readlines()
    i = 0
    for line in lines:
        l = line.split()
        if len(l) > 0 and l[0] != "SOURCE_ID":
            # ra, dec, flux, ref freq, spectral index
            sources.append([ float(l[1]), float(l[2]), float(l[3]), float(l[4]), float(l[5])])

    sources = np.array(sources)   
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
        beam_spec = telescope["beam_paths"][id]
            
        if beam_spec["type"] == "gaussian":
            defined_beams[id] = AnalyticBeam("gaussian", sigma=beam_spec["sigma"])
        elif beam_spec["type"] == "uniform":
            defined_beams[id] = AnalyticBeam("uniform")
        elif beam_spec["type"] == "airy":
            defined_beams[id] = AnalyticBeam("airy", diameter=beam_spec["diameter"])
        else:
            raise RuntimeError("Expecting AnalyticBeam specification")

    # Now give each antenna the right beam
    beams = [ None for i in range(len(ant_to_beam)) ]
    for i in range(len(ant_to_beam)):
        beams[i] = defined_beams[ant_to_beam[i]]
    beam_ids = list(range(len(ant_to_beam)))
    
    
    return uvdata, beams, beam_ids, freqs, ra_dec, flux

