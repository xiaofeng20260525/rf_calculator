"""Link budget and system cascade calculators.

Includes:
- Friis noise figure cascade
- Link budget (Friis transmission equation)
- Free space path loss
- Receiver sensitivity
- SNR / EbNo calculations
"""

import math
from ..utils.constants import C0, K_B, T0


def free_space_path_loss(distance_m, freq_hz):
    """Calculate free space path loss in dB.

    FSPL = 20*log10(4*pi*d/lambda)

    Parameters:
        distance_m: distance in meters
        freq_hz: frequency in Hz
    Returns:
        path loss in dB
    """
    wavelength = C0 / freq_hz
    if distance_m <= 0:
        return float('inf')
    return 20 * math.log10(4 * math.pi * distance_m / wavelength)


def free_space_path_loss_dbm(distance_km, freq_mhz):
    """Calculate FSPL using engineering units.

    FSPL(dB) = 32.44 + 20*log10(d_km) + 20*log10(f_MHz)
    """
    if distance_km <= 0 or freq_mhz <= 0:
        return float('inf')
    return 32.44 + 20 * math.log10(distance_km) + 20 * math.log10(freq_mhz)


def noise_figure_cascade(nf_list_db, gain_list_db):
    """Calculate cascaded noise figure using Friis formula.

    F_total = F1 + (F2-1)/G1 + (F3-1)/(G1*G2) + ...

    Parameters:
        nf_list_db: list of noise figures in dB
        gain_list_db: list of gains in dB (length = nf_list - 1, or same length with last gain ignored)
    Returns:
        cascaded noise figure in dB
    """
    if not nf_list_db:
        return 0.0

    # Convert to linear
    f_list = [10 ** (nf / 10) for nf in nf_list_db]
    g_list = [10 ** (g / 10) for g in gain_list_db]

    f_total = f_list[0]
    g_prod = 1.0

    for i in range(1, len(f_list)):
        if i - 1 < len(g_list):
            g_prod *= g_list[i - 1]
        f_total += (f_list[i] - 1) / g_prod

    return 10 * math.log10(f_total)


def link_budget(tx_power_dbm, tx_antenna_gain_dbi, distance_m, freq_hz,
                rx_antenna_gain_dbi=0, cable_loss_tx_db=0, cable_loss_rx_db=0,
                margin_db=0):
    """Calculate link budget and received power.

    Parameters:
        tx_power_dbm: transmitter output power (dBm)
        tx_antenna_gain_dbi: TX antenna gain (dBi)
        distance_m: link distance (meters)
        freq_hz: carrier frequency (Hz)
        rx_antenna_gain_dbi: RX antenna gain (dBi)
        cable_loss_tx_db: TX cable/filter loss (dB)
        cable_loss_rx_db: RX cable/filter loss (dB)
        margin_db: additional margin (dB) for fading, interference, etc.

    Returns dict with:
        tx_eirp: EIRP in dBm
        fspl: free space path loss in dB
        rx_power: received power in dBm
        rx_power_watt: received power in Watts
    """
    tx_eirp = tx_power_dbm + tx_antenna_gain_dbi - cable_loss_tx_db
    fspl = free_space_path_loss(distance_m, freq_hz)
    rx_power = tx_eirp - fspl + rx_antenna_gain_dbi - cable_loss_rx_db - margin_db

    return {
        'tx_eirp_dbm': tx_eirp,
        'fspl_db': fspl,
        'rx_power_dbm': rx_power,
        'rx_power_watt': 10 ** ((rx_power - 30) / 10),
    }


def receiver_sensitivity(bandwidth_hz, nf_db, snr_min_db):
    """Calculate receiver sensitivity.

    Sensitivity = -174 + 10*log10(BW) + NF + SNR_min  [dBm]

    Parameters:
        bandwidth_hz: signal bandwidth in Hz
        nf_db: receiver noise figure in dB
        snr_min_db: minimum required SNR in dB
    Returns:
        sensitivity in dBm
    """
    noise_floor = -174 + 10 * math.log10(bandwidth_hz)
    return noise_floor + nf_db + snr_min_db


def noise_floor(bandwidth_hz, temperature_k=T0):
    """Calculate thermal noise floor.

    N = k*T*B  in Watts
    N_dBm = -174 + 10*log10(B) + 10*log10(T/T0)
    """
    n_linear = K_B * temperature_k * bandwidth_hz
    n_dbm = 10 * math.log10(n_linear) + 30
    return {
        'noise_power_w': n_linear,
        'noise_power_dbm': n_dbm,
    }


def snr_to_ebno(snr_db, bit_rate_bps, bandwidth_hz):
    """Convert SNR to Eb/No.

    Eb/No = SNR + 10*log10(BW / Rb)
    """
    if bit_rate_bps <= 0:
        return float('inf')
    return snr_db + 10 * math.log10(bandwidth_hz / bit_rate_bps)


def ebno_to_snr(ebno_db, bit_rate_bps, bandwidth_hz):
    """Convert Eb/No to SNR."""
    if bandwidth_hz <= 0:
        return float('inf')
    return ebno_db + 10 * math.log10(bit_rate_bps / bandwidth_hz)


def max_range(tx_power_dbm, tx_antenna_gain_dbi, freq_hz,
              rx_antenna_gain_dbi, rx_sensitivity_dbm,
              cable_loss_tx_db=0, cable_loss_rx_db=0, margin_db=0):
    """Calculate maximum range given receiver sensitivity.

    Uses FSPL model. Returns distance in meters.
    """
    tx_eirp = tx_power_dbm + tx_antenna_gain_dbi - cable_loss_tx_db
    max_path_loss = tx_eirp + rx_antenna_gain_dbi - rx_sensitivity_dbm - cable_loss_rx_db - margin_db

    if max_path_loss <= 0:
        return 0.0

    wavelength = C0 / freq_hz
    # FSPL = 20*log10(4*pi*d/lambda) => d = lambda * 10^(FSPL/20) / (4*pi)
    distance = wavelength * 10 ** (max_path_loss / 20) / (4 * math.pi)
    return distance


def cascade_stages_table(nf_list_db, gain_list_db, stage_names=None):
    """Build a cascade analysis table for display.

    Returns list of dicts with cumulative NF and gain at each stage.
    """
    if stage_names is None:
        stage_names = [f'Stage {i + 1}' for i in range(len(nf_list_db))]

    f_list = [10 ** (nf / 10) for nf in nf_list_db]
    g_linear_list = [10 ** (g / 10) for g in gain_list_db]

    stages = []
    f_cum = f_list[0]
    g_cum = 1.0

    for i, name in enumerate(stage_names):
        g_cum_before = g_cum

        f_cum = f_list[0]
        g_cum = 1.0
        for j in range(min(i + 1, len(f_list))):
            if j == 0:
                f_cum = f_list[0]
                g_cum = g_linear_list[0] if j < len(g_linear_list) else 1.0
            else:
                g_prev = g_linear_list[j - 1] if j - 1 < len(g_linear_list) else 1.0
                f_cum += (f_list[j] - 1) / (g_cum)
                if j < len(g_linear_list):
                    g_cum *= g_linear_list[j]

        # Recalculate properly
        f_cum_total = f_list[0]
        g_prod = 1.0
        for j in range(1, i + 1):
            if j - 1 < len(g_linear_list):
                g_prod *= g_linear_list[j - 1]
            f_cum_total += (f_list[j] - 1) / g_prod

        g_total = 1.0
        for j in range(min(i + 1, len(g_linear_list))):
            g_total *= g_linear_list[j]

        nf_cum_db = 10 * math.log10(f_cum_total)
        g_cum_db = 10 * math.log10(g_total)

        stages.append({
            'name': name,
            'nf_db': nf_list_db[i] if i < len(nf_list_db) else 0,
            'gain_db': gain_list_db[i] if i < len(gain_list_db) else 0,
            'nf_cum_db': nf_cum_db,
            'gain_cum_db': g_cum_db,
        })

    return stages
