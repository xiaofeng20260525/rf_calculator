"""Transmission line and PCB calculator.

Supports:
- Microstrip impedance and effective dielectric constant
- Stripline impedance
- CPW (Co-planar Waveguide) impedance
- Wavelength calculations
- Skin depth
- VSWR / Return Loss / Reflection Coefficient conversions
"""

import math
from ..utils.constants import C0


def microstrip_impedance(w, h, er, t=0):
    """Calculate microstrip characteristic impedance.

    Uses Wheeler's equations (approximate, accurate to ~1% for W/H < 10).

    Parameters:
        w: trace width (same unit as h)
        h: substrate height (same unit as w)
        er: relative dielectric constant
        t: conductor thickness (same unit, 0 for approximation)
    Returns:
        (Z0, ereff): characteristic impedance in ohms, effective dielectric constant
    """
    if w <= 0 or h <= 0:
        return 0, er

    wh_ratio = w / h

    # Effective dielectric constant
    if wh_ratio <= 1:
        ereff = (er + 1) / 2 + (er - 1) / 2 * (
            1 / math.sqrt(1 + 12 / wh_ratio) + 0.04 * (1 - wh_ratio) ** 2
        )
    else:
        ereff = (er + 1) / 2 + (er - 1) / 2 * (1 / math.sqrt(1 + 12 / wh_ratio))

    # Adjust for conductor thickness if provided
    if t > 0 and t < h:
        w_eff = w
        if wh_ratio < 1 / (2 * math.pi):
            w_eff = w + t / math.pi * (1 + math.log(4 * math.pi * w / t))
        else:
            w_eff = w + t / math.pi * (1 + math.log(2 * h / t))
        wh_ratio = w_eff / h

    # Characteristic impedance
    if wh_ratio <= 1:
        z0 = 60 / math.sqrt(ereff) * math.log(8 / wh_ratio + wh_ratio / 4)
    else:
        z0 = 120 * math.pi / (math.sqrt(ereff) * (wh_ratio + 1.393 + 0.667 * math.log(wh_ratio + 1.444)))

    return z0, ereff


def microstrip_width(z0_target, h, er, t=0):
    """Calculate microstrip width for a target impedance.

    Uses iterative approximation.

    Parameters:
        z0_target: target characteristic impedance (ohms)
        h: substrate height
        er: dielectric constant
        t: conductor thickness
    Returns:
        (w, ereff): trace width and effective dielectric constant
    """
    if z0_target <= 0 or h <= 0:
        return 0, er

    # Starting guess
    if z0_target < 50:
        w_guess = 2 * h
    elif z0_target < 100:
        w_guess = h
    else:
        w_guess = h / 2

    # Binary search
    w_min, w_max = h * 0.01, h * 20
    for _ in range(50):
        z0_guess, ereff = microstrip_impedance(w_guess, h, er, t)
        if abs(z0_guess - z0_target) < 0.01:
            break
        if z0_guess > z0_target:
            w_min = w_guess
        else:
            w_max = w_guess
        w_guess = (w_min + w_max) / 2

    return w_guess, ereff


def stripline_impedance(w, h, er):
    """Calculate symmetric stripline characteristic impedance.

    Uses Cohn's model (accurate).

    Parameters:
        w: trace width
        h: total substrate height (ground-to-ground)
        er: dielectric constant
    Returns:
        Z0 in ohms
    """
    if w <= 0 or h <= 0:
        return 0

    wh = w / h

    if wh < 0.35:
        # Narrow strip approximation
        z0 = 60 / math.sqrt(er) * math.log(4 * h / (math.pi * w))
    else:
        # Wide strip approximation
        x = math.pi * wh / 2
        z0 = 94.15 / (math.sqrt(er) * (wh + 0.441))

    return z0


def stripline_width(z0_target, h, er):
    """Calculate stripline width for target impedance.

    Returns width in same units as h.
    """
    if z0_target <= 0:
        return 0

    w_min, w_max = h * 0.01, h * 10
    w_guess = h / 2

    for _ in range(50):
        z0_guess = stripline_impedance(w_guess, h, er)
        if abs(z0_guess - z0_target) < 0.01:
            break
        if z0_guess > z0_target:
            w_min = w_guess
        else:
            w_max = w_guess
        w_guess = (w_min + w_max) / 2

    return w_guess


def cpw_impedance(w, s, h, er):
    """Calculate CPW (Coplanar Waveguide) characteristic impedance.

    Approximate formula. Assumes thick substrate (h >> w, s).

    Parameters:
        w: center conductor width
        s: gap width (each side)
        h: substrate height
        er: dielectric constant
    Returns:
        Z0 in ohms
    """
    if w <= 0 or s <= 0:
        return 0

    ereff = (er + 1) / 2

    k = w / (w + 2 * s)
    k_prime = math.sqrt(1 - k ** 2)

    # Complete elliptic integral approximation
    if k < 0.707:
        k_ratio = math.pi / math.log(2 * (1 + math.sqrt(k_prime)) / (1 - math.sqrt(k_prime)))
    else:
        k_ratio = math.log(2 * (1 + math.sqrt(k)) / (1 - math.sqrt(k))) / math.pi

    z0 = 30 * math.pi / math.sqrt(ereff) * k_ratio
    return z0


def skin_depth(freq_hz, conductivity=5.8e7, ur=1):
    """Calculate skin depth.

    delta = 1 / sqrt(pi * f * mu * sigma)

    Parameters:
        freq_hz: frequency in Hz
        conductivity: conductivity in S/m (default: copper 5.8e7)
        ur: relative permeability (default: 1 for non-magnetic)
    Returns:
        skin depth in meters
    """
    mu0 = 4e-7 * math.pi
    mu = mu0 * ur

    if freq_hz <= 0:
        return float('inf')

    return 1 / math.sqrt(math.pi * freq_hz * mu * conductivity)


def guided_wavelength(freq_hz, er_eff):
    """Calculate guided wavelength in a transmission line.

    lambda_g = lambda_0 / sqrt(er_eff)
    """
    lambda_0 = C0 / freq_hz
    return lambda_0 / math.sqrt(er_eff)


def quarter_wave_length(freq_hz, er_eff):
    """Calculate quarter-wave length."""
    return guided_wavelength(freq_hz, er_eff) / 4


def wavelength_in_medium(freq_hz, er):
    """Calculate wavelength in a dielectric medium."""
    return C0 / (freq_hz * math.sqrt(er))


# ==================== Trace Loss Calculations ====================

MU0 = 4e-7 * math.pi  # permeability of free space


def _surface_resistance(freq_hz, conductivity=5.8e7):
    """Calculate RF surface resistance Rs (Ω/sq).

    Rs = sqrt(π * f * μ₀ * ρ) = sqrt(π * f * μ₀ / σ)
    = 1 / (σ * δ)
    where δ = skin depth
    """
    return math.sqrt(math.pi * freq_hz * MU0 / conductivity)


def _roughness_factor(rms_roughness_um, skin_depth_um):
    """Hammerstad surface roughness correction factor.

    Kr = 1 + 2/π * arctan(1.4 * (Rrms/δ)²)

    Parameters:
        rms_roughness_um: RMS surface roughness in μm (typical: 0.4 for ED copper, 2.0 for thick)
        skin_depth_um: skin depth in μm
    """
    if skin_depth_um <= 0:
        return 1.0
    ratio = rms_roughness_um / skin_depth_um
    return 1 + (2 / math.pi) * math.atan(1.4 * (ratio ** 2))


def microstrip_conductor_loss(w_mm, h_mm, z0_ohm, freq_hz, conductivity=5.8e7,
                               roughness_um=0.4):
    """Calculate microstrip conductor loss per unit length.

    Simplified approximation:
    αc = 8.686 * Rs / (Z₀ * W_eff)    [dB/m]

    With effective width accounting for current distribution.
    Returns (alpha_c_db_per_mm, alpha_c_db_per_cm).
    """
    Rs = _surface_resistance(freq_hz, conductivity)
    delta_um = skin_depth(freq_hz, conductivity) * 1e6

    # Roughness correction
    Kr = _roughness_factor(roughness_um, delta_um)
    Rs_corrected = Rs * Kr

    # Effective width (simplified)
    w_eff_m = max(w_mm, 0.01) * 1e-3

    # Conductor loss in Np/m -> dB/m
    alpha_np_per_m = Rs_corrected / (z0_ohm * w_eff_m)
    alpha_db_per_m = 8.686 * alpha_np_per_m
    alpha_db_per_cm = alpha_db_per_m / 100

    return {
        'Rs_ohm_per_sq': Rs,
        'skin_depth_um': delta_um,
        'roughness_factor': Kr,
        'Rs_corrected': Rs_corrected,
        'alpha_db_per_m': alpha_db_per_m,
        'alpha_db_per_cm': alpha_db_per_cm,
        'alpha_db_per_mm': alpha_db_per_m / 1000,
    }


def microstrip_dielectric_loss(freq_hz, er, ereff, loss_tangent=0.02):
    """Calculate microstrip dielectric loss per unit length.

    αd = 27.3 * er/√ereff * (ereff-1)/(er-1) * tanδ / λ₀    [dB/m]

    Parameters:
        freq_hz: frequency in Hz
        er: substrate dielectric constant
        ereff: effective dielectric constant
        loss_tangent: dielectric loss tangent (FR4≈0.02, Rogers 4350≈0.0037)
    Returns (alpha_d_db_per_m, alpha_d_db_per_cm).
    """
    lambda_0 = C0 / freq_hz
    if loss_tangent <= 0 or lambda_0 <= 0:
        return 0

    factor = 27.3 * (er / math.sqrt(ereff)) * (ereff - 1) / (er - 1)
    alpha_db_per_m = factor * loss_tangent / lambda_0
    alpha_db_per_cm = alpha_db_per_m / 100

    return {
        'alpha_db_per_m': alpha_db_per_m,
        'alpha_db_per_cm': alpha_db_per_cm,
        'alpha_db_per_mm': alpha_db_per_m / 1000,
        'loss_tangent': loss_tangent,
        'lambda_0_mm': lambda_0 * 1000,
    }


def microstrip_total_loss(w_mm, h_mm, z0_ohm, ereff, er, freq_hz, loss_tangent=0.02,
                          length_mm=10, conductivity=5.8e7, roughness_um=0.4):
    """Calculate total microstrip insertion loss.

    Returns dict with detailed breakdown:
        - conductor loss
        - dielectric loss
        - total loss per unit length
        - total loss for given length
    """
    cond = microstrip_conductor_loss(w_mm, h_mm, z0_ohm, freq_hz, conductivity, roughness_um)
    diel = microstrip_dielectric_loss(freq_hz, er, ereff, loss_tangent)

    total_db_per_mm = cond['alpha_db_per_mm'] + diel['alpha_db_per_mm']
    total_loss_db = total_db_per_mm * length_mm

    return {
        'freq_mhz': freq_hz / 1e6,
        'w_mm': w_mm,
        'h_mm': h_mm,
        'z0_ohm': z0_ohm,
        'ereff': ereff,
        'er': er,
        'loss_tangent': loss_tangent,
        'length_mm': length_mm,
        'conductor_loss_db_per_mm': cond['alpha_db_per_mm'],
        'conductor_loss_db_per_cm': cond['alpha_db_per_cm'],
        'dielectric_loss_db_per_mm': diel['alpha_db_per_mm'],
        'dielectric_loss_db_per_cm': diel['alpha_db_per_cm'],
        'total_loss_db_per_mm': total_db_per_mm,
        'total_loss_db_per_cm': total_db_per_mm * 10,
        'total_loss_db': total_loss_db,
        'surface_resistance_ohm_sq': cond['Rs_ohm_per_sq'],
        'skin_depth_um': cond['skin_depth_um'],
        'roughness_factor': cond['roughness_factor'],
    }


def stripline_conductor_loss(w_mm, h_mm, z0_ohm, freq_hz, conductivity=5.8e7,
                              roughness_um=0.4):
    """Calculate stripline conductor loss per unit length.

    Similar to microstrip but with different geometry factor:
    αc = 8.686 * Rs / (2 * Z₀ * W_eff) * (1 + 2W/(π*h))  (approx)

    Returns (alpha_c_db_per_mm, alpha_c_db_per_cm).
    """
    Rs = _surface_resistance(freq_hz, conductivity)
    delta_um = skin_depth(freq_hz, conductivity) * 1e6
    Kr = _roughness_factor(roughness_um, delta_um)
    Rs_c = Rs * Kr

    w_eff_m = max(w_mm, 0.01) * 1e-3
    h_m = h_mm * 1e-3

    # Stripline geometry correction
    geo_factor = 1 + 2 * w_eff_m / (math.pi * h_m) if h_m > 0 else 1
    alpha_np_per_m = Rs_c / (2 * z0_ohm * w_eff_m) * geo_factor
    alpha_db_per_m = 8.686 * alpha_np_per_m

    return {
        'Rs_ohm_per_sq': Rs,
        'skin_depth_um': delta_um,
        'roughness_factor': Kr,
        'Rs_corrected': Rs_c,
        'alpha_db_per_m': alpha_db_per_m,
        'alpha_db_per_cm': alpha_db_per_m / 100,
        'alpha_db_per_mm': alpha_db_per_m / 1000,
    }


def stripline_dielectric_loss(freq_hz, er, loss_tangent=0.02):
    """Stripline dielectric loss (simpler than microstrip — uniform dielectric).

    αd = 27.3 * √εr * tanδ / λ₀    [dB/m]
    """
    lambda_0 = C0 / freq_hz
    if loss_tangent <= 0 or lambda_0 <= 0:
        return {'alpha_db_per_m': 0, 'alpha_db_per_cm': 0, 'alpha_db_per_mm': 0}

    alpha_db_per_m = 27.3 * math.sqrt(er) * loss_tangent / lambda_0
    return {
        'alpha_db_per_m': alpha_db_per_m,
        'alpha_db_per_cm': alpha_db_per_m / 100,
        'alpha_db_per_mm': alpha_db_per_m / 1000,
    }


def stripline_total_loss(w_mm, h_mm, z0_ohm, er, freq_hz, loss_tangent=0.02,
                         length_mm=10, conductivity=5.8e7, roughness_um=0.4):
    """Calculate total stripline insertion loss."""
    cond = stripline_conductor_loss(w_mm, h_mm, z0_ohm, freq_hz, conductivity, roughness_um)
    diel = stripline_dielectric_loss(freq_hz, er, loss_tangent)

    total_db_per_mm = cond['alpha_db_per_mm'] + diel['alpha_db_per_mm']
    total_loss_db = total_db_per_mm * length_mm

    return {
        'freq_mhz': freq_hz / 1e6,
        'w_mm': w_mm,
        'h_mm': h_mm,
        'z0_ohm': z0_ohm,
        'er': er,
        'loss_tangent': loss_tangent,
        'length_mm': length_mm,
        'conductor_loss_db_per_mm': cond['alpha_db_per_mm'],
        'dielectric_loss_db_per_mm': diel['alpha_db_per_mm'],
        'total_loss_db_per_mm': total_db_per_mm,
        'total_loss_db_per_cm': total_db_per_mm * 10,
        'total_loss_db': total_loss_db,
        'skin_depth_um': cond['skin_depth_um'],
        'roughness_factor': cond['roughness_factor'],
    }


# Common substrate loss tangents
LOSS_TANGENTS = {
    'FR4':              0.020,
    'FR4_High_Tg':      0.018,
    'Rogers_4350B':     0.0037,
    'Rogers_4003C':     0.0027,
    'Rogers_3003':      0.0013,
    'Isola_Astra_MT77': 0.0017,
    'Taconic_RF35':     0.0018,
    'PTFE':             0.0004,
    'Alumina':          0.0001,
}
