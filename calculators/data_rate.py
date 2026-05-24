"""WiFi / LTE / NR data rate calculators."""

import math

# ==================== WiFi MCS Tables ====================

# WiFi 6 (802.11ax) MCS table: (MCS, modulation, coding_rate_x1024, data_bits_per_symbol)
# Per spatial stream, 160MHz, 1x SS, GI=0.8us (shortest), 1960 data tones
# Simplified: max PHY rate per SS per 160MHz

WIFI6_MCS = {
    # MCS: (modulation, coding_rate, bits_per_symbol_per_ss)
    0:  ('BPSK',   1/2,   0.5),
    1:  ('QPSK',   1/2,   1.0),
    2:  ('QPSK',   3/4,   1.5),
    3:  ('16QAM',  1/2,   2.0),
    4:  ('16QAM',  3/4,   3.0),
    5:  ('64QAM',  2/3,   4.0),
    6:  ('64QAM',  3/4,   4.5),
    7:  ('64QAM',  5/6,   5.0),
    8:  ('256QAM', 3/4,   6.0),
    9:  ('256QAM', 5/6,   6.67),
    10: ('1024QAM',3/4,   7.5),
    11: ('1024QAM',5/6,   8.33),
    12: ('4096QAM',3/4,   9.0),   # WiFi 7
    13: ('4096QAM',5/6,  10.0),   # WiFi 7
    14: ('4096QAM',7/8,  10.5),
}

# WiFi 5 (802.11ac) MCS
WIFI5_MCS = {
    0: ('BPSK',   1/2,   0.5),
    1: ('QPSK',   1/2,   1.0),
    2: ('QPSK',   3/4,   1.5),
    3: ('16QAM',  1/2,   2.0),
    4: ('16QAM',  3/4,   3.0),
    5: ('64QAM',  2/3,   4.0),
    6: ('64QAM',  3/4,   4.5),
    7: ('64QAM',  5/6,   5.0),
    8: ('256QAM', 3/4,   6.0),
    9: ('256QAM', 5/6,   6.67),
}

# WiFi data subcarrier counts per bandwidth
WIFI_DATA_TONES = {
    20: 234,    # WiFi 6, 20MHz: 242 total - 8 pilots = 234 data
    40: 468,    # 40MHz: 484 - 16 = 468
    80: 980,    # 80MHz: 996 - 16 = 980
    160: 1960,  # 160MHz: 2*996 - 32 = 1960
    320: 3920,  # WiFi 7 320MHz
}

# OFDM symbol duration (us) per guard interval
WIFI_SYMBOL_DURATION = {
    '0.8us (Short)': 13.6,   # WiFi 6 short GI
    '1.6us (Long)':  14.4,   # WiFi 6 long GI
    '3.2us':         16.0,   # WiFi 5 normal
}


def wifi_rate(mcs, bw_mhz=80, nss=2, gi='0.8us (Short)', wifi_gen=6):
    """Calculate WiFi PHY data rate.

    Rate = N_data_tones * bits_per_symbol * N_SS / T_symbol

    Parameters:
        mcs: MCS index (0-11 for WiFi 6, 0-9 for WiFi 5)
        bw_mhz: channel bandwidth (20/40/80/160/320)
        nss: number of spatial streams
        gi: guard interval type
        wifi_gen: 5 or 6 (802.11ac or ax)
    Returns dict with details.
    """
    mcs_table = WIFI6_MCS if wifi_gen >= 6 else WIFI5_MCS
    if mcs not in mcs_table:
        return None

    mod, cr, bits_per_sym = mcs_table[mcs]
    n_tones = WIFI_DATA_TONES.get(bw_mhz, 980)
    t_sym = WIFI_SYMBOL_DURATION.get(gi, 13.6)

    total_bits_per_sym = n_tones * bits_per_sym * nss
    rate_bps = total_bits_per_sym / (t_sym * 1e-6)
    rate_mbps = rate_bps / 1e6

    return {
        'mcs': mcs,
        'modulation': mod,
        'coding_rate': cr,
        'bits_per_symbol_per_ss': bits_per_sym,
        'data_tones': n_tones,
        'spatial_streams': nss,
        'symbol_time_us': t_sym,
        'guard_interval': gi,
        'rate_mbps': rate_mbps,
        'rate_gbps': rate_mbps / 1000,
    }


def wifi_rate_simple(mcs, bw_mhz, nss, gi='0.8us (Short)'):
    """Simplified WiFi rate estimate."""
    if mcs <= 11:
        bits = {0: 0.5, 1: 1.0, 2: 1.5, 3: 2.0, 4: 3.0, 5: 4.0,
                6: 4.5, 7: 5.0, 8: 6.0, 9: 6.67, 10: 7.5, 11: 8.33}[mcs]
    else:
        bits = 10.0  # 4096QAM

    tones = {20: 234, 40: 468, 80: 980, 160: 1960, 320: 3920}[bw_mhz]
    t_sym = {'0.8us (Short)': 13.6, '1.6us (Long)': 14.4, '3.2us': 16.0}[gi]
    return tones * bits * nss / (t_sym * 1e-6) / 1e6


# ==================== LTE Rate Calculator ====================

# LTE MCS -> TBS index mapping (simplified)
# Modulation order (bits per RE) per MCS index
LTE_MODULATION = {
    # MCS: (modulation, bits_per_RE, TBS_index)
    0:  ('QPSK',    2,   0),
    1:  ('QPSK',    2,   1),
    2:  ('QPSK',    2,   2),
    3:  ('QPSK',    2,   3),
    4:  ('QPSK',    2,   4),
    5:  ('QPSK',    2,   5),
    6:  ('QPSK',    2,   6),
    7:  ('QPSK',    2,   7),
    8:  ('QPSK',    2,   8),
    9:  ('QPSK',    2,   9),
    10: ('16QAM',   4,   9),
    11: ('16QAM',   4,  10),
    12: ('16QAM',   4,  11),
    13: ('16QAM',   4,  12),
    14: ('16QAM',   4,  13),
    15: ('16QAM',   4,  14),
    16: ('16QAM',   4,  15),
    17: ('64QAM',   6,  15),
    18: ('64QAM',   6,  16),
    19: ('64QAM',   6,  17),
    20: ('64QAM',   6,  18),
    21: ('64QAM',   6,  19),
    22: ('64QAM',   6,  20),
    23: ('64QAM',   6,  21),
    24: ('64QAM',   6,  22),
    25: ('64QAM',   6,  23),
    26: ('64QAM',   6,  24),
    27: ('64QAM',   6,  25),
    28: ('256QAM',  8,  26),
    29: ('256QAM',  8,  26),
    30: ('256QAM',  8,  27),
    31: ('256QAM',  8,  27),
}


def lte_rate(n_rb, mcs, mimo_layers=2, overhead_pct=25, dl_ratio=1.0):
    """Calculate LTE PHY data rate (approximate).

    Simplified: Rate = N_RB * 12 * 14 * bits_per_RE * layers * (1-overhead/100) / TTI * dl_ratio

    Parameters:
        n_rb: number of resource blocks (6, 15, 25, 50, 75, 100)
        mcs: MCS index 0-31
        mimo_layers: MIMO layers (1, 2, 4)
        overhead_pct: overhead percentage for control channels (default 25%)
        dl_ratio: DL slot ratio (1.0 = FDD, 0.6 = TDD 60% DL)
    Returns dict with details.
    """
    if mcs not in LTE_MODULATION:
        return None

    mod, bits_per_re, tbs_idx = LTE_MODULATION[mcs]
    total_re = n_rb * 12 * 14
    usable_re = total_re * (1 - overhead_pct / 100)
    bits_per_sf = usable_re * bits_per_re * mimo_layers
    rate_bps = bits_per_sf / 0.001 * dl_ratio
    rate_mbps = rate_bps / 1e6

    result = {
        'n_rb': n_rb,
        'channel_bw_mhz': _rb_to_bw(n_rb),
        'mcs': mcs,
        'modulation': mod,
        'bits_per_re': bits_per_re,
        'tbs_index': tbs_idx,
        'mimo_layers': mimo_layers,
        'overhead_pct': overhead_pct,
        'dl_ratio': dl_ratio,
        'total_re': total_re,
        'usable_re': usable_re,
        'bits_per_subframe': bits_per_sf,
        'rate_mbps': rate_mbps,
    }
    if dl_ratio < 1.0:
        result['rate_mbps_full'] = rate_mbps / dl_ratio
    return result


def _rb_to_bw(n_rb):
    """Map RB count to channel bandwidth."""
    rb_map = {6: 1.4, 15: 3, 25: 5, 50: 10, 75: 15, 100: 20}
    return rb_map.get(n_rb, n_rb * 0.18)


# ==================== TDD Configurations ====================

# NR TDD slot patterns: (period_ms, DL_ratio)
NR_TDD_PATTERNS = {
    'DDDSU (2.5ms)':          (2.5, 0.74),
    'DDDDDDDSU (5ms)':        (5.0, 0.77),
    'DDDSUUDDDD (5ms)':       (5.0, 0.70),
    'DSUUU (2.5ms)':          (2.5, 0.46),
    'FDD (Full DL)':          (1.0, 1.0),
}

# LTE TDD UL/DL configurations (3GPP TS 36.211)
LTE_TDD_CONFIGS = {
    'FDD (Full DL)':          (1.0, 'FDD'),
    'TDD Config 1 (60%)':     (0.60, 'TDD DSUUDSUUD'),
    'TDD Config 2 (40%)':     (0.40, 'TDD DSUDDDSUDD'),
    'TDD Config 3 (30%)':     (0.30, 'TDD DSUUUDSUUU'),
    'TDD Config 5 (10%)':     (0.10, 'TDD DSUUUDDDDD'),
}

# ==================== NR Rate Calculator ====================

# NR MCS table (simplified from TS 38.214 Table 5.1.3.1-1)
NR_MODULATION = {
    0:  ('QPSK',    2,   120),    # MCS: (modulation, Qm, target_code_rate_x1024)
    1:  ('QPSK',    2,   157),
    2:  ('QPSK',    2,   193),
    3:  ('QPSK',    2,   251),
    4:  ('QPSK',    2,   308),
    5:  ('QPSK',    2,   379),
    6:  ('QPSK',    2,   449),
    7:  ('QPSK',    2,   526),
    8:  ('QPSK',    2,   602),
    9:  ('QPSK',    2,   679),
    10: ('16QAM',   4,   378),
    11: ('16QAM',   4,   434),
    12: ('16QAM',   4,   490),
    13: ('16QAM',   4,   553),
    14: ('16QAM',   4,   616),
    15: ('16QAM',   4,   658),
    16: ('16QAM',   4,   699),
    17: ('64QAM',   6,   466),
    18: ('64QAM',   6,   517),
    19: ('64QAM',   6,   567),
    20: ('64QAM',   6,   616),
    21: ('64QAM',   6,   666),
    22: ('64QAM',   6,   719),
    23: ('64QAM',   6,   772),
    24: ('64QAM',   6,   822),
    25: ('64QAM',   6,   873),
    26: ('64QAM',   6,   910),
    27: ('64QAM',   6,   948),
    28: ('256QAM',  8,   711),
    29: ('256QAM',  8,   750),
    30: ('256QAM',  8,   797),
    31: ('256QAM',  8,   841),
}

# NR numerology: subcarrier spacing -> slots per 1ms
NR_NUMEROLOGY = {
    0: {'scs_khz': 15, 'slots_per_ms': 1,   'symbols_per_slot': 14},
    1: {'scs_khz': 30, 'slots_per_ms': 2,   'symbols_per_slot': 14},
    2: {'scs_khz': 60, 'slots_per_ms': 4,   'symbols_per_slot': 14},
    3: {'scs_khz': 120,'slots_per_ms': 8,   'symbols_per_slot': 14},
    4: {'scs_khz': 240,'slots_per_ms': 16,  'symbols_per_slot': 14},
}

NR_BW_RB = {
    # NR channel BW (MHz) -> max RBs (FR1, SCS=30kHz)
    5:   11,  10:  24,  15:  38,  20:  51,
    25:  65,  30:  78,  40:  106, 50:  133,
    60:  162, 70:  189, 80:  217, 90:  245,
    100: 273,
}


def nr_rate(n_rb, mcs, mimo_layers=4, scs_khz=30, overhead_pct=14,
            carrier_agg=1, dl_ratio=1.0):
    """Calculate NR PHY data rate.

    Rate = N_RB * 12 * N_slots_per_ms * N_symbols_per_slot
         * Qm * code_rate * MIMO_layers * (1-overhead) * CA_factor * dl_ratio * 1000

    Parameters:
        n_rb: resource blocks
        mcs: MCS index 0-31
        mimo_layers: MIMO layers (1-4 for FR1)
        scs_khz: subcarrier spacing (15/30/60/120)
        overhead_pct: overhead for PDCCH/DMRS/SSB (typical 14%)
        carrier_agg: carrier aggregation factor
        dl_ratio: DL slot ratio (1.0=FDD, 0.74=DDDSU, 0.77=DDDDDDDSU etc.)
    Returns dict.
    """
    if mcs not in NR_MODULATION:
        return None

    _, qm, target_cr = NR_MODULATION[mcs]
    cr = target_cr / 1024.0

    # Find numerology index from SCS
    numer = {15: 0, 30: 1, 60: 2, 120: 3, 240: 4}.get(scs_khz, 1)
    num_cfg = NR_NUMEROLOGY[numer]

    # REs per ms per layer
    re_per_ms = n_rb * 12 * num_cfg['slots_per_ms'] * num_cfg['symbols_per_slot']
    usable_re = re_per_ms * (1 - overhead_pct / 100)

    # Bits per ms per layer
    bits_per_ms = usable_re * qm * cr
    # MIMO + CA + TDD DL ratio
    total_bits_per_ms = bits_per_ms * mimo_layers * carrier_agg * dl_ratio

    # Rate in Mbps
    rate_mbps = total_bits_per_ms * 1000 / 1e6
    rate_gbps = rate_mbps / 1000

    result = {
        'n_rb': n_rb,
        'mcs': mcs,
        'modulation_order': qm,
        'target_code_rate': cr,
        'scs_khz': scs_khz,
        'slots_per_ms': num_cfg['slots_per_ms'],
        'mimo_layers': mimo_layers,
        'carrier_agg': carrier_agg,
        'dl_ratio': dl_ratio,
        'overhead_pct': overhead_pct,
        're_per_ms_total': re_per_ms * mimo_layers,
        'usable_re': usable_re * mimo_layers,
        'rate_mbps': rate_mbps,
        'rate_gbps': rate_gbps,
    }
    if dl_ratio < 1.0:
        result['rate_mbps_full_dl'] = rate_mbps / dl_ratio
    return result


def nr_max_rate(bw_mhz=100, mcs=27, mimo_layers=4, scs_khz=30,
                overhead_pct=14, ca=1):
    """Quick NR peak rate estimate for a given channel BW."""
    n_rb = NR_BW_RB.get(bw_mhz, int(bw_mhz * 2.5))
    return nr_rate(n_rb, mcs, mimo_layers, scs_khz, overhead_pct, ca)
