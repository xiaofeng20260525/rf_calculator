"""RF system calculators: IIP3 cascade, desense, PAPR, PAE, sensitivity."""

import math
from ..utils.constants import K_B, T0


def iip3_cascade(iip3_list_dbm, gain_list_db):
    """Calculate cascaded IIP3 using the cascade formula.

    1/IIP3_total = 1/IIP3_1 + G1/IIP3_2 + G1*G2/IIP3_3 + ...
    (all in linear, not dB)

    Parameters:
        iip3_list_dbm: list of IIP3 values in dBm
        gain_list_db: list of gains in dB (len = len(iip3)-1)
    Returns:
        cascaded IIP3 in dBm
    """
    if not iip3_list_dbm:
        return 0.0

    iip3_lin = [10 ** (v / 10) for v in iip3_list_dbm]  # mW
    g_lin = [10 ** (g / 10) for g in gain_list_db]       # linear

    inv_sum = 1.0 / iip3_lin[0]
    g_prod = 1.0

    for i in range(1, len(iip3_lin)):
        if i - 1 < len(g_lin):
            g_prod *= g_lin[i - 1]
        inv_sum += g_prod / iip3_lin[i]

    iip3_total_lin = 1.0 / inv_sum
    return 10 * math.log10(iip3_total_lin)


def oip3_cascade(iip3_list_dbm, gain_list_db):
    """Calculate cascaded OIP3.

    OIP3 = IIP3 + Gain
    Returns cascaded OIP3 in dBm.
    """
    iip3 = iip3_cascade(iip3_list_dbm, gain_list_db)
    total_gain = sum(gain_list_db)
    return iip3 + total_gain


def imd_level(pout_dbm, iip3_dbm):
    """Calculate IMD3 level given output power and IIP3.

    P_IMD3 = 3*P_out - 2*IIP3
    Returns IMD3 level in dBm.
    """
    return 3 * pout_dbm - 2 * iip3_dbm


def imd_to_carrier_ratio(pout_dbm, iip3_dbm):
    """Calculate IMD3-to-carrier ratio (dBc).

    C/I ratio = 2*(IIP3 - P_out)
    """
    return 2 * (iip3_dbm - pout_dbm)


def icpr_estimate(iip3_dbm, pout_dbm, papr_db=8.5):
    """Estimate ACLR/ACPR from IIP3.

    ACLR ≈ 2*(IIP3 - P_out) + PAPR_correction
    (Rough estimate, actual depends on PA nonlinearity profile)
    """
    return 2 * (iip3_dbm - pout_dbm) + papr_db * 0.85


# ==================== Desense / Isolation ====================

def tx_leakage_at_rx(tx_power_dbm, isolation_db, tx_duplexer_loss=0, rx_duplexer_loss=0):
    """Calculate TX leakage power at RX input.

    Parameters:
        tx_power_dbm: TX output power
        isolation_db: total isolation (duplexer + switch + PCB)
        tx_duplexer_loss: TX path duplexer loss
        rx_duplexer_loss: RX path duplexer loss
    Returns:
        TX leakage at RX input in dBm
    """
    return tx_power_dbm - isolation_db - tx_duplexer_loss - rx_duplexer_loss


def rx_desense(tx_leakage_dbm, rx_sensitivity_dbm=-100, rx_bandwidth_hz=10e6, rx_nf_db=3.0):
    """Calculate RX desense from TX leakage.

    Desense = 10*log10(1 + P_leakage / (kT*B*F))
    Where F is the RX noise factor (linear).

    Returns:
        desense in dB (positive = degradation)
    """
    nf_linear = 10 ** (rx_nf_db / 10)
    noise_power_linear = K_B * T0 * rx_bandwidth_hz * nf_linear  # Watts
    tx_leakage_linear = 10 ** ((tx_leakage_dbm - 30) / 10)  # Watts

    desense_linear = 1 + tx_leakage_linear / noise_power_linear
    desense_db = 10 * math.log10(desense_linear)
    return desense_db


def rx_sensitivity_detailed(bandwidth_hz, nf_db, snr_min_db, temperature_k=T0):
    """Detailed RX sensitivity calculation.

    Thermal noise floor: kT = -174 dBm/Hz (at 290K)
    Noise in BW: kT + 10*log10(BW)
    Total noise: kT + 10*log10(BW) + NF
    Sensitivity: kT + 10*log10(BW) + NF + SNR_min

    Returns dict with breakdown.
    """
    kt_dbm_per_hz = 10 * math.log10(K_B * temperature_k) + 30
    noise_bw_db = 10 * math.log10(bandwidth_hz)
    noise_floor_dbm = kt_dbm_per_hz + noise_bw_db
    total_noise_dbm = noise_floor_dbm + nf_db
    sensitivity_dbm = total_noise_dbm + snr_min_db

    return {
        'kt_dbm_per_hz': kt_dbm_per_hz,
        'noise_bw_db': noise_bw_db,
        'noise_floor_dbm': noise_floor_dbm,
        'total_noise_dbm': total_noise_dbm,
        'sensitivity_dbm': sensitivity_dbm,
        'nf_db': nf_db,
        'snr_min_db': snr_min_db,
    }


# ==================== PAPR / PAE ====================

def papr(peak_power_dbm, avg_power_dbm):
    """Calculate Peak-to-Average Power Ratio.

    PAPR = P_peak - P_avg  [dB]
    """
    return peak_power_dbm - avg_power_dbm


def avg_from_peak(peak_power_dbm, papr_db):
    """Calculate average power from peak power and PAPR."""
    return peak_power_dbm - papr_db


def peak_from_avg(avg_power_dbm, papr_db):
    """Calculate peak power from average power and PAPR."""
    return avg_power_dbm + papr_db


def pa_efficiency(pout_dbm, pin_dbm, pdc_mw):
    """Calculate Power Added Efficiency (PAE).

    PAE = (P_out - P_in) / P_DC * 100%

    Parameters:
        pout_dbm: output power in dBm
        pin_dbm: input power in dBm
        pdc_mw: DC power consumption in mW
    Returns:
        PAE in percentage
    """
    pout_mw = 10 ** ((pout_dbm - 30) / 10) * 1000
    pin_mw = 10 ** ((pin_dbm - 30) / 10) * 1000
    if pdc_mw <= 0:
        return 0.0
    return (pout_mw - pin_mw) / pdc_mw * 100


def drain_efficiency(pout_dbm, pdc_mw):
    """Calculate Drain Efficiency.

    DE = P_out / P_DC * 100%
    """
    pout_mw = 10 ** ((pout_dbm - 30) / 10) * 1000
    if pdc_mw <= 0:
        return 0.0
    return pout_mw / pdc_mw * 100


def max_rate_power(pout_dbm, papr_db):
    """Estimate maximum rated power with PAPR applied.

    P_rated = P_avg + PAPR_headroom
    """
    return pout_dbm + papr_db


def dc_power_estimate(pout_dbm, gain_db, pae_percent):
    """Estimate DC power consumption from output power and PAE.

    P_DC = P_RF_out / (PAE/100)
    """
    pout_mw = 10 ** ((pout_dbm - 30) / 10) * 1000
    if pae_percent <= 0:
        return 0
    return pout_mw / (pae_percent / 100)


def pa_current(pdc_mw, vcc_v=3.7):
    """Calculate PA current from DC power.

    I = P_DC / Vcc
    Returns current in mA.
    """
    if vcc_v <= 0:
        return 0
    return pdc_mw / vcc_v


# ==================== Power / Crest Factor ====================

def crest_factor(signal_type='LTE'):
    """Typical PAPR / Crest Factor for common signals.

    Returns estimated PAPR in dB.
    """
    values = {
        'CW': 3.0,
        'QPSK': 4.0,
        '16QAM': 5.5,
        '64QAM': 6.5,
        '256QAM': 7.5,
        'LTE': 8.5,
        'LTE_DFTS': 6.0,
        'NR_CP': 8.5,
        'NR_DFTS': 6.0,
        'NR_256QAM': 10.0,
        'WCDMA': 3.5,
        'WiFi_6': 10.0,
        'WiFi_7': 10.5,
    }
    return values.get(signal_type, 8.0)


def duty_cycle_avg_power(peak_power_dbm, duty_pct):
    """Calculate average power from peak and duty cycle.

    P_avg = P_peak + 10*log10(duty/100)
    """
    if duty_pct <= 0 or duty_pct > 100:
        return None
    return peak_power_dbm + 10 * math.log10(duty_pct / 100)


def duty_from_avg_peak(avg_power_dbm, peak_power_dbm):
    """Calculate duty cycle from average and peak powers."""
    return 10 ** ((avg_power_dbm - peak_power_dbm) / 10) * 100


# ==================== Harmonic Calculations ====================

def harmonic_frequencies(fundamental_mhz, harmonics=[2, 3, 4, 5]):
    """Calculate harmonic frequencies from fundamental (MHz).

    Returns dict: {H2: freq_mhz, H3: freq_mhz, ...}
    """
    return {f'H{n}': fundamental_mhz * n for n in harmonics}


def harmonic_power(fundamental_power_dbm, harmonic_suppression_dbc, harmonics=[2, 3]):
    """Calculate harmonic power levels given suppression.

    Parameters:
        fundamental_power_dbm: PA output power at fundamental
        harmonic_suppression_dbc: dict {2: -40, 3: -50} or single value
    Returns dict with harmonic powers in dBm.
    """
    if isinstance(harmonic_suppression_dbc, (int, float)):
        harmonic_suppression_dbc = {n: harmonic_suppression_dbc for n in harmonics}

    result = {'fundamental_dbm': fundamental_power_dbm}
    for n in harmonics:
        supp = harmonic_suppression_dbc.get(n, -30)
        result[f'H{n}_dbc'] = supp
        result[f'H{n}_dbm'] = fundamental_power_dbm + supp
    return result


def harmonic_filter_requirement(harmonic_dbm, spec_limit_dbm):
    """Calculate required additional filtering.

    Returns: additional_attenuation_db needed to meet spec.
    """
    return harmonic_dbm - spec_limit_dbm


def harmonic_falls_in_band(harmonic_freq_mhz, band, bands_db=None):
    """Check if a harmonic frequency falls into a given cellular band.

    Parameters:
        harmonic_freq_mhz: harmonic frequency
        band: band name like 'n77', 'B41'
        bands_db: list of band tuples (from utils.bands)
    Returns (in_range, ul_or_dl, band_info) or None if bands_db not provided.
    """
    if bands_db is None:
        return None

    for b in bands_db:
        if b[2] <= harmonic_freq_mhz <= b[3]:
            return (True, 'UL', b)
        if b[4] <= harmonic_freq_mhz <= b[5]:
            return (True, 'DL', b)
    return (False, None, None)


def harmonic_path_loss(harmonic_power_dbm, required_limit_dbm=-30):
    """Calculate required path loss / filtering to meet harmonic limit.

    Typical 3GPP limit: -30 dBm (conducted) for harmonics.
    Returns required attenuation in dB.
    """
    return max(0, harmonic_power_dbm - required_limit_dbm)


# ==================== ACLR Calculations ====================

# Typical ACLR specs (3GPP)
ACLR_SPECS = {
    'LTE_adj': -36,      # ACLR for adjacent channel (dBc)
    'LTE_alt': -36,      # ACLR for alternate channel (dBc)
    'NR_FR1_adj': -30,   # NR FR1 adjacent (dBc)
    'NR_FR1_alt': -36,   # NR FR1 alternate (dBc)
    'NR_FR2_adj': -24,   # NR FR2 adjacent (dBc)
    'WCDMA_adj': -33,    # WCDMA adjacent (dBc)
    'WCDMA_alt': -43,    # WCDMA alternate (dBc)
}


def aclr_estimate_from_iip3(pout_dbm_per_antenna, iip3_dbm, papr_db=8.5, pa_count=1):
    """Estimate ACLR from PA IIP3 (approximate, empirical).

    ACLR ≈ 10*log10( (3*Pout^3/(2*IIP3)^2) / (kT*B*F) )  simplified

    More practical estimate based on PA nonlinearity:
    ACLR ≈ 2*(IIP3 - Pout) - PAPR_correction

    For multi-antenna: ACLR improves by 10*log10(N_ant)

    Parameters:
        pout_dbm_per_antenna: output power per antenna in dBm
        iip3_dbm: PA IIP3 in dBm
        papr_db: signal PAPR in dB
        pa_count: number of PA/antenna paths (improves ACLR)
    Returns:
        estimated ACLR in dBc (more negative = better)
    """
    # Basic estimate from IIP3 backoff
    aclr = 2 * (iip3_dbm - pout_dbm_per_antenna) - papr_db * 1.2

    # Multi-antenna improvement
    if pa_count > 1:
        aclr += 10 * math.log10(pa_count)

    return aclr


def aclr_budget(pout_dbm, pa_aclr_dbc=-35, filter_rejection_db=0, switch_isolation_db=0):
    """Calculate TX chain ACLR budget.

    Overall ACLR is dominated by the worst contributor (typically PA).

    Returns dict with breakdown.
    """
    # PA dominates, filter/switch help improve
    total_aclr = pa_aclr_dbc - filter_rejection_db

    return {
        'pa_aclr_dbc': pa_aclr_dbc,
        'filter_rejection_db': filter_rejection_db,
        'switch_isolation_db': switch_isolation_db,
        'total_aclr_dbc': total_aclr,
        'pass_3gpp_lte': total_aclr <= -36,
        'pass_3gpp_nr': total_aclr <= -30,
    }


def aclr_required_backoff(target_aclr_dbc, pa_aclr_full_power_dbc=-30,
                          backoff_slope_db_per_db=2.0):
    """Calculate required power backoff to meet ACLR target.

    Parameters:
        target_aclr_dbc: desired ACLR (e.g. -36 dBc for LTE)
        pa_aclr_full_power_dbc: PA ACLR at max power
        backoff_slope_db_per_db: how many dB ACLR improves per dB backoff (typical ~2)
    Returns:
        required backoff in dB, power at backoff
    """
    delta_aclr = target_aclr_dbc - pa_aclr_full_power_dbc
    if delta_aclr >= 0:
        return 0.0  # Already meets spec
    backoff = abs(delta_aclr) / backoff_slope_db_per_db
    return backoff


def sem_estimate(pout_dbm, offset_mhz=5, bw_mhz=10, iip3_dbm=30):
    """Estimate Spectrum Emission Mask (SEM) level at offset.

    SEM is determined by:
    - ACLR for close-in offsets (< BW)
    - Phase noise for mid offsets (~BW to 2*BW)
    - Harmonics for far offsets

    Returns rough estimate in dBm/bandwidth at the offset.
    """
    if offset_mhz <= bw_mhz:
        # ACLR-dominated region
        aclr = aclr_estimate_from_iip3(pout_dbm, iip3_dbm)
        return pout_dbm + aclr
    elif offset_mhz <= 2 * bw_mhz:
        # Phase noise transition region
        return pout_dbm - 80  # rough: -80 dBc at 5-10MHz offset
    else:
        # Harmonic/spur region
        return pout_dbm - 100  # rough


# 3GPP harmonic limits (conducted, UE Power Class 3)
HARMONIC_LIMITS = {
    '3GPP_UE_PC3': {
        2: -30,   # H2: -30 dBm
        3: -30,   # H3: -30 dBm
        4: -30,   # H4: -30 dBm
        5: -30,   # H5: -30 dBm
        6: -30,
        7: -30,
        8: -30,
        9: -30,
        10: -30,
    },
    'FCC_2.4G': {
        # FCC Part 15.247 for 2.4GHz ISM
        2: -30,
        3: -30,
    },
}
