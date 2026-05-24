"""Impedance matching network calculator.

Supports L-match, Pi-match, T-match, single-stub, and double-stub matching.
"""

import math
import cmath

from ..utils.constants import C0


def normalize(z, z0=50):
    """Normalize impedance to Z0."""
    return z / z0


def denormalize(z_norm, z0=50):
    """Denormalize impedance from Z0."""
    return z_norm * z0


def z_to_gamma(z, z0=50):
    """Calculate reflection coefficient from impedance."""
    z_norm = normalize(z, z0)
    return (z_norm - 1) / (z_norm + 1)


def gamma_to_z(gamma, z0=50):
    """Calculate impedance from reflection coefficient."""
    return z0 * (1 + gamma) / (1 - gamma)


def z_to_y(z, z0=50):
    """Convert impedance to admittance (normalized)."""
    z_norm = normalize(z, z0)
    return 1 / z_norm


def l_match(z_load_complex, z0=50, freq_hz=1e9):
    """Design an L-match network.

    Returns two possible solutions (low-pass and high-pass configurations).
    Each solution is a dict with 'series' and 'shunt' components.
    Component values are in Farads (C) or Henries (L).

    Parameters:
        z_load_complex: complex load impedance (R + jX)
        z0: system reference impedance
        freq_hz: operating frequency in Hz
    """
    zl = z_load_complex
    rl, xl = zl.real, zl.imag
    w = 2 * math.pi * freq_hz

    solutions = []

    # Solution A: shunt element on load side
    # First, decide topology based on whether we need to step up or down
    _l_match_solution(zl, z0, w, solutions, shunt_first=True)
    _l_match_solution(zl, z0, w, solutions, shunt_first=False)

    return solutions


def _l_match_solution(zl, z0, w, solutions, shunt_first):
    """Internal helper for L-match calculation."""
    rl, xl = zl.real, zl.imag

    try:
        if rl < z0:
            # R_L < Z0: use series L, shunt C (low-pass toward load)
            # or series C, shunt L (high-pass toward load)
            q = math.sqrt(z0 / rl - 1)
            xs = q * rl - xl  # series reactance
            bp = q / z0       # shunt susceptance

            # Series element
            if xs > 0:
                ls = xs / w
                solutions.append({
                    'topology': 'L-match (shunt-first, low-pass)',
                    'series': ('L', ls),
                    'shunt': ('C', bp / w) if bp > 0 else ('L', -1 / (bp * w)),
                    'series_value': f'{ls * 1e9:.2f} nH',
                    'shunt_value': f'{bp / w * 1e12:.2f} pF' if bp > 0 else f'{-1 / (bp * w) * 1e9:.2f} nH',
                })
            else:
                cs = -1 / (xs * w)
                solutions.append({
                    'topology': 'L-match (shunt-first, high-pass)',
                    'series': ('C', cs),
                    'shunt': ('L', -1 / (bp * w)) if bp < 0 else ('C', bp / w),
                    'series_value': f'{cs * 1e12:.2f} pF',
                    'shunt_value': f'{-1 / (bp * w) * 1e9:.2f} nH',
                })
        else:
            # R_L > Z0: series-first topology
            q = math.sqrt(rl / z0 - 1)
            xs_mirror = -xl
            bp_mirror = q / rl

            # For series-first, we reverse: shunt is on source side
            if xs_mirror > 0:
                ls = xs_mirror / w
                solutions.append({
                    'topology': 'L-match (series-first, low-pass)',
                    'series': ('L', ls),
                    'shunt': ('C', bp_mirror / w) if bp_mirror > 0 else ('L', -1 / (bp_mirror * w)),
                    'series_value': f'{ls * 1e9:.2f} nH',
                    'shunt_value': f'{bp_mirror / w * 1e12:.2f} pF',
                })
            else:
                cs = -1 / (xs_mirror * w)
                solutions.append({
                    'topology': 'L-match (series-first, high-pass)',
                    'series': ('C', cs),
                    'shunt': ('L', -1 / (bp_mirror * w)) if bp_mirror < 0 else ('C', bp_mirror / w),
                    'series_value': f'{cs * 1e12:.2f} pF',
                    'shunt_value': f'{-1 / (bp_mirror * w) * 1e9:.2f} nH',
                })
    except (ValueError, ZeroDivisionError):
        pass


def single_stub_match(z_load_complex, z0=50, freq_hz=1e9, stub_type='shunt'):
    """Design a single-stub matching network.

    Parameters:
        z_load_complex: complex load impedance
        z0: system reference impedance
        freq_hz: operating frequency
        stub_type: 'shunt' or 'series'

    Returns list of solutions with stub position and length in wavelengths.
    """
    zl = z_load_complex
    gamma_load = z_to_gamma(zl, z0)
    gamma_mag = abs(gamma_load)
    gamma_phase = cmath.phase(gamma_load)

    wl = C0 / freq_hz
    beta = 2 * math.pi / wl
    solutions = []

    if stub_type == 'shunt':
        # Shunt stub: find position where Y = 1 + jB
        # Use the reflection coefficient rotation method
        _shunt_stub_solutions(zl, z0, solutions)
    else:
        # Series stub: find position where Z = 1 + jX
        _series_stub_solutions(zl, z0, solutions)

    # Convert electrical lengths to physical lengths
    for sol in solutions:
        d_wl = sol['d_wavelengths']
        l_wl = sol['l_wavelengths']
        sol['d_mm'] = d_wl * wl * 1000
        sol['l_mm'] = l_wl * wl * 1000
        sol['d_mm_str'] = f'{sol["d_mm"]:.2f} mm'
        sol['l_mm_str'] = f'{sol["l_mm"]:.2f} mm'

    return solutions


def _shunt_stub_solutions(zl, z0, solutions):
    """Calculate shunt stub matching solutions using admittance chart approach."""
    yl = 1 / normalize(zl, z0)

    gl = yl.real
    bl = yl.imag

    # For shunt stub, we need to rotate to a point where g = 1
    # Using transmission line equation
    if gl == 0:
        return

    # tan(beta*d) that gives g = 1
    discriminant = gl * (1 - gl) + bl ** 2
    if discriminant < 0:
        return

    sqrt_d = math.sqrt(discriminant)

    # Two solutions for d
    t_d_options = []
    denom = gl ** 2 + bl ** 2

    t1 = (bl + sqrt_d) / (denom - gl)
    t2 = (bl - sqrt_d) / (denom - gl)

    if denom != gl:
        t_d_options.append(t1)
    if abs(t1 - t2) > 1e-10 and denom != gl:
        t_d_options.append(t2)

    for t_d in t_d_options:
        # d in wavelengths
        d_wl = math.atan(t_d) / (2 * math.pi)
        if d_wl < 0:
            d_wl += 0.5

        # Susceptance at this point
        num = (1 - gl * t_d ** 2 + bl * t_d * 2)
        den = (gl ** 2 + (bl + t_d) ** 2)
        # The susceptance we need to cancel
        b_stub = -(bl * (1 - t_d ** 2) + t_d * (1 - gl ** 2 - bl ** 2)) / (gl ** 2 + (bl + t_d) ** 2)

        # Stub length for open stub (preferred at high freq)
        # Open stub: B = tan(beta*l), l = atan(B) / (2*pi)
        l_wl_open = math.atan(b_stub) / (2 * math.pi)
        if l_wl_open < 0:
            l_wl_open += 0.5

        # Short stub: B = -cot(beta*l), l = -acot(B) / (2*pi)
        if b_stub != 0:
            l_wl_short = -1 / math.tan(math.atan(b_stub)) + 0.25
        else:
            l_wl_short = 0.25

        if l_wl_short < 0:
            l_wl_short += 0.5

        solutions.append({
            'type': 'Shunt Stub - Open',
            'd_wavelengths': d_wl,
            'l_wavelengths': l_wl_open,
            'stub_end': 'open',
        })
        solutions.append({
            'type': 'Shunt Stub - Short',
            'd_wavelengths': d_wl,
            'l_wavelengths': l_wl_short,
            'stub_end': 'short',
        })


def _series_stub_solutions(zl, z0, solutions):
    """Calculate series stub matching solutions."""
    zl_norm = normalize(zl, z0)
    rl = zl_norm.real
    xl = zl_norm.imag

    if rl == 0:
        return

    discriminant = rl * (1 - rl) + xl ** 2
    if discriminant < 0:
        return

    sqrt_d = math.sqrt(discriminant)
    denom = rl ** 2 + xl ** 2

    t_d_options = []
    t1 = (xl + sqrt_d) / (denom - rl)
    t2 = (xl - sqrt_d) / (denom - rl)

    if denom != rl:
        t_d_options.append(t1)
    if abs(t1 - t2) > 1e-10 and denom != rl:
        t_d_options.append(t2)

    for t_d in t_d_options:
        d_wl = math.atan(-t_d) / (2 * math.pi)
        if d_wl < 0:
            d_wl += 0.5

        # Reactance needed
        x_stub = - (xl * (1 - t_d ** 2) + t_d * (1 - rl ** 2 - xl ** 2)) / (rl ** 2 + (xl + t_d) ** 2)

        # Short stub: X = tan(beta*l)
        l_wl_short = math.atan(x_stub) / (2 * math.pi)
        if l_wl_short < 0:
            l_wl_short += 0.5

        # Open stub: X = -cot(beta*l)
        if x_stub != 0:
            l_wl_open = -1 / math.tan(math.atan(x_stub)) + 0.25
        else:
            l_wl_open = 0.25
        if l_wl_open < 0:
            l_wl_open += 0.5

        solutions.append({
            'type': 'Series Stub - Short',
            'd_wavelengths': d_wl,
            'l_wavelengths': l_wl_short,
            'stub_end': 'short',
        })
        solutions.append({
            'type': 'Series Stub - Open',
            'd_wavelengths': d_wl,
            'l_wavelengths': l_wl_open,
            'stub_end': 'open',
        })


def calculate_impedance_from_rcs(r, c, freq_hz, series=True):
    """Calculate complex impedance for R-C or R-L combination."""
    w = 2 * math.pi * freq_hz
    if series:
        return complex(r, -1 / (w * c)) if c > 0 else complex(r, w * c)  # negative c => inductor
    else:
        # Parallel
        xc = -1 / (w * c)
        return 1 / (1 / r + 1 / complex(0, xc))
