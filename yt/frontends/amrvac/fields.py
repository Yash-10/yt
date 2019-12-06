"""
AMRVAC-specific fields

"""

#-----------------------------------------------------------------------------
# Copyright (c) 2013, yt Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from yt.fields.field_info_container import \
    FieldInfoContainer
from yt.fields.magnetic_field import setup_magnetic_field_aliases
from yt.units import dimensions
from yt import mylog

# We need to specify which fields we might have in our dataset.  The field info
# container subclass here will define which fields it knows about.  There are
# optionally methods on it that get called which can be subclassed.

direction_aliases = {
    "cartesian": ("x", "y", "z"),
    "polar": ("r", "theta", "z"),
    "cylindrical": ("r", "z", "theta"),
    "spherical": ("r", "theta", "phi")
}

class AMRVACFieldInfo(FieldInfoContainer):
    code_density = "code_mass / code_length**3"
    code_moment = "code_mass / code_length**2 / code_time"
    code_pressure = "code_mass / code_length / code_time**2"

    # format: (native(?) field, (units, [aliases], display_name))
    # note: aliases will correspond to "gas" typed fields, whereas the native ones are "amrvac" typed
    known_other_fields = (
        ("rho", (code_density, ["density"], None)),
        ("m1", (code_moment, ["moment_1"], None)),
        ("m2", (code_moment, ["moment_2"], None)),
        ("m3", (code_moment, ["moment_3"], None)),
        ("e", (code_pressure, ["energy_density"], None)),
        ("b1", ("code_magnetic", ["magnetic_1"], None)),
        ("b2", ("code_magnetic", ["magnetic_2"], None)),
        ("b3", ("code_magnetic", ["magnetic_3"], None))
    )

    known_particle_fields = ()

    def setup_fluid_fields(self):
        def _v1(field, data):
            return data["gas", "moment_1"] / data["gas", "density"]
        def _v2(field, data):
            return data["gas", "moment_2"] / data["gas", "density"]
        def _v3(field, data):
            return data["gas", "moment_3"] / data["gas", "density"]

        us = self.ds.unit_system
        aliases = direction_aliases[self.ds.geometry]
        for idir, alias, func in zip("123", aliases, (_v1, _v2, _v3)):
            if not ("amrvac", "m%s" % idir) in self.field_list:
                break
            self.add_field(("gas", "velocity_%s" % alias), function=func,
                            units=us['velocity'],
                            dimensions=dimensions.velocity,
                            sampling_type="cell")
            self.alias(("gas", "velocity_%s" % idir), ("gas", "velocity_%s" % alias),
                        units=us"velocity"])
            self.alias(("gas", "moment_%s" % alias), ("gas", "moment_%s" % idir),
                        units=us["density"]*us["velocity"])


        setup_magnetic_field_aliases(self, "amrvac", ["mag%s" % ax for ax in "xyz"])


        # fields with nested dependencies are defined thereafter by increasing level of complexity

        # kinetic energy depends on velocities
        def _kinetic_energy_density(field, data):
            # devnote : have a look at issue 1301
            return 0.5 * data["gas", "density"] * data["gas", "velocity_amplitude"]**2

        self.add_field(("gas", "kinetic_energy_density"), function=_kinetic_energy_density,
                        units=us["density"]*us["velocity"]**2,
                        dimensions=dimensions.density*dimensions.velocity**2,
                        sampling_type="cell")


        # thermal pressure depends kinetic energy and equation of state
        def _thermal_pressure(field, data):
            ds = data.ds
            gamma = ds.gamma
            namelist = ds.namelist
            if namelist.get(["hd_list"], {}).get("hd_ernergy", True):
                # important note : energy density and pressure are actually expressed in the same unit
                pth = (gamma - 1) * data["gas", "energy_density"] - data["gas", "kinetic_energy_density"]
            else:
                # todo: move this warning so it's only triggered once ?
                mylog.warning("thermal_pressure field is assumed polytropic when hd_energy = False." \
                              "If your simulation used usr_set_pthermal you should redefine this field.")
                hd_adiab = namelist.get("hd_list", {}).get("hd_adiab", 1.)

                # this complicated unit is required for the equation of state to make physical sense
                hd_adiab *= ds.mass_unit**(1-gamma) * ds.length_unit**(2+3*(gamma-1)) / ds.time_unit**2
                pth = hd_adiab * entropy_unit * data["gas", "density"]**gamma
            return pth

        self.add_field(("gas", "thermal_pressure"), function=_thermal_pressure,
                        units=us["density"]*us["velocity"]**2,
                        dimensions=dimensions.density*dimensions.velocity**2,
                        sampling_type="cell")


        # sound speed depends on thermal pressure
        def _sound_speed(field, data):
            return np.sqrt(data.ds.gamma * data["thermal_pressure"] / data["gas", "density"])

        self.add_field(("gas", "sound_speed"), function=_sound_speed,
                        units=us["velocity"],
                        dimensions=dimensions.velocity,
                        sampling_type="cell")


        # mach number depends on sound speed
        def _mach(field, data):
            return data["gas", "velocity_magnitude"] / data["sound_speed"]

        self.add_field(("gas", "mach"), function=_mach,
                        units="auto",
                        dimensions=dimensions.dimensionless,
                        sampling_type="cell")
