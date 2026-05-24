"""Physical constants and common RF conversion utilities."""

import math

# Speed of light (m/s)
C0 = 299792458

# Boltzmann constant (J/K)
K_B = 1.380649e-23

# Reference temperature for noise figure (K)
T0 = 290.0

# Common dielectric constants (FR4, Rogers, etc.)
ER_FR4 = 4.4
ER_ROGERS_4350 = 3.48
ER_ROGERS_4003 = 3.38
ER_AIR = 1.0006

# Common substrate heights (mm)
H_062 = 1.575  # 62 mil
H_031 = 0.787  # 31 mil
H_020 = 0.508  # 20 mil
H_010 = 0.254  # 10 mil

# Copper conductivity (S/m)
CU_CONDUCTIVITY = 5.8e7
# Copper thickness common values (mm)
CU_1OZ = 0.035  # 1 oz/ft^2
CU_05OZ = 0.018  # 0.5 oz/ft^2


def dbm_to_watt(dbm):
    """Convert dBm to Watts."""
    return 10 ** ((dbm - 30) / 10)


def watt_to_dbm(watt):
    """Convert Watts to dBm."""
    if watt <= 0:
        return -float('inf')
    return 10 * math.log10(watt) + 30


def dbm_to_vrms(dbm, z0=50):
    """Convert dBm to Vrms across given impedance."""
    p_watt = dbm_to_watt(dbm)
    return math.sqrt(p_watt * z0)


def vrms_to_dbm(vrms, z0=50):
    """Convert Vrms to dBm across given impedance."""
    if vrms <= 0:
        return -float('inf')
    p_watt = vrms ** 2 / z0
    return watt_to_dbm(p_watt)


def db_to_linear(db):
    """Convert dB to linear ratio."""
    return 10 ** (db / 10)


def linear_to_db(linear):
    """Convert linear ratio to dB."""
    if linear <= 0:
        return -float('inf')
    return 10 * math.log10(linear)


def wavelength(freq_hz, er=1.0):
    """Calculate wavelength in meters for given frequency and dielectric constant."""
    return C0 / (freq_hz * math.sqrt(er))


def vswr_to_rl(vswr):
    """Convert VSWR to Return Loss (dB)."""
    if vswr <= 1:
        return float('inf')
    gamma = (vswr - 1) / (vswr + 1)
    return -20 * math.log10(gamma)


def rl_to_vswr(rl_db):
    """Convert Return Loss (dB) to VSWR."""
    gamma = 10 ** (-rl_db / 20)
    return (1 + gamma) / (1 - gamma)


def vswr_to_gamma(vswr):
    """Convert VSWR to reflection coefficient magnitude."""
    return (vswr - 1) / (vswr + 1)


def rl_to_gamma(rl_db):
    """Convert Return Loss (dB) to reflection coefficient magnitude."""
    return 10 ** (-rl_db / 20)


def gamma_to_vswr(gamma):
    """Convert reflection coefficient magnitude to VSWR."""
    if gamma >= 1:
        return float('inf')
    return (1 + abs(gamma)) / (1 - abs(gamma))


def gamma_to_rl(gamma):
    """Convert reflection coefficient magnitude to Return Loss (dB)."""
    if abs(gamma) <= 0:
        return float('inf')
    return -20 * math.log10(abs(gamma))


# --- dB / power / voltage unit conversions ---

def dbm_to_dbw(dbm):
    """Convert dBm to dBW."""
    return dbm - 30


def dbw_to_dbm(dbw):
    """Convert dBW to dBm."""
    return dbw + 30


def dbw_to_watt(dbw):
    """Convert dBW to Watts."""
    return 10 ** (dbw / 10)


def watt_to_dbw(watt):
    """Convert Watts to dBW."""
    if watt <= 0:
        return -float('inf')
    return 10 * math.log10(watt)


def dbm_to_dbuv(dbm, z0=50):
    """Convert dBm to dBμV across given impedance.

    dBμV = 90 + 10*log10(Z0) + dBm
    For 50Ω: dBμV = dBm + 107
    For 75Ω: dBμV = dBm + 108.75
    """
    return dbm + 90 + 10 * math.log10(z0)


def dbuv_to_dbm(dbuv, z0=50):
    """Convert dBμV to dBm across given impedance."""
    return dbuv - 90 - 10 * math.log10(z0)


def dbuv_to_vrms(dbuv):
    """Convert dBμV to Vrms."""
    return 10 ** ((dbuv - 120) / 20)


def vrms_to_dbuv(vrms):
    """Convert Vrms to dBμV."""
    if vrms <= 0:
        return -float('inf')
    return 20 * math.log10(vrms) + 120


def vrms_to_vpeak(vrms):
    """Convert Vrms to Vpeak (sine wave)."""
    return vrms * math.sqrt(2)


def vpeak_to_vrms(vpeak):
    """Convert Vpeak to Vrms (sine wave)."""
    return vpeak / math.sqrt(2)


def vrms_to_vpp(vrms):
    """Convert Vrms to Vpp (sine wave)."""
    return vrms * 2 * math.sqrt(2)


def vpp_to_vrms(vpp):
    """Convert Vpp to Vrms (sine wave)."""
    return vpp / (2 * math.sqrt(2))


def dbm_to_dbmv(dbm, z0=50):
    """Convert dBm to dBmV across given impedance.

    For 50Ω: dBmV = dBm + 46.99
    """
    return dbm + 10 * math.log10(z0) + 30


def dbmv_to_dbm(dbmv, z0=50):
    """Convert dBmV to dBm across given impedance."""
    return dbmv - 10 * math.log10(z0) - 30


def dbuv_to_dbmv(dbuv):
    """Convert dBμV to dBmV."""
    return dbuv - 60


def dbmv_to_dbuv(dbmv):
    """Convert dBmV to dBμV."""
    return dbmv + 60


def dbuv_to_dbuvm(dbuv):
    """Convert dBμV to dBμV/m (simple, no distance factor)."""
    return dbuv  # placeholder — E-field depends on antenna factor


def watt_to_vrms(watt, z0=50):
    """Convert Watts to Vrms across given impedance."""
    if watt <= 0:
        return 0
    return math.sqrt(watt * z0)


def vrms_to_watt(vrms, z0=50):
    """Convert Vrms to Watts."""
    if vrms <= 0:
        return 0
    return vrms ** 2 / z0


def dbuv_to_dbm_75(dbuv):
    """Shorthand: dBμV to dBm at 75Ω."""
    return dbuv_to_dbm(dbuv, 75)


def dbm_to_dbuv_75(dbm):
    """Shorthand: dBm to dBμV at 75Ω."""
    return dbm_to_dbuv(dbm, 75)
