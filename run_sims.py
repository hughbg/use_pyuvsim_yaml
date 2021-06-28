#!/usr/bin/env python
# coding: utf-8

import numpy as np
from pyuvsim import uvsim
from hera_sim.visibilities import VisCPU
import config

# pyuvsim

uvd_out = uvsim.run_uvsim("params.yaml", return_uv=True)

sim_auto = uvd_out.get_data(0, 0, "XX")[0][0]
sim_cross = uvd_out.get_data(0, 1, "XX")[0][0]

print("pyuvsim -------------")
print("ant 0 auto amp:", np.abs(sim_auto))
print("ant 0,1 cross amp:", np.abs(sim_cross), "phase:", np.angle(sim_cross))

uvdata, beam, beam_ids, freqs, ra_dec, flux = config.load_config("params.yaml")

simulator = VisCPU(
    uvdata = uvdata,
    beams = beam,
    beam_ids = beam_ids,
    sky_freqs = freqs,
    point_source_pos = ra_dec,
    point_source_flux = flux,
    use_pixel_beams = False
)

simulator.simulate()

sim_auto = simulator.uvdata.get_data(0, 0, "XX")[0][0]
sim_cross = simulator.uvdata.get_data(0, 1, "XX")[0][0]

print("hera_sim ----")
print("ant 0 auto amp:", np.abs(sim_auto))
print("ant 0,1 cross amp:", np.abs(sim_cross), "phase:", np.angle(sim_cross))


