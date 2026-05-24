"""3GPP NR/LTE band data — frequency ranges, duplex modes, power classes."""

# Each band: (band, name, UL_low_MHz, UL_high_MHz, DL_low_MHz, DL_high_MHz, duplex, power_class_dBm)
# duplex: 'FDD' or 'TDD'
# power_class: typical UE max power (PC3=23dBm, PC2=26dBm)

NR_BANDS = [
    # FR1 Sub-6GHz
    ('n1',  '2100 FDD',    1920, 1980, 2110, 2170, 'FDD', 23),
    ('n2',  '1900 FDD',    1850, 1910, 1930, 1990, 'FDD', 23),
    ('n3',  '1800 FDD',    1710, 1785, 1805, 1880, 'FDD', 23),
    ('n5',  '850 FDD',      824,  849,  869,  894, 'FDD', 23),
    ('n7',  '2600 FDD',    2500, 2570, 2620, 2690, 'FDD', 23),
    ('n8',  '900 FDD',      880,  915,  925,  960, 'FDD', 23),
    ('n12', '700a FDD',     699,  716,  729,  746, 'FDD', 23),
    ('n13', '700c FDD',     777,  787,  746,  756, 'FDD', 23),
    ('n14', '700 PS FDD',   788,  798,  758,  768, 'FDD', 23),
    ('n18', '850 Lower FDD',815,  830,  860,  875, 'FDD', 23),
    ('n20', '800 FDD',      832,  862,  791,  821, 'FDD', 23),
    ('n25', '1900+ FDD',   1850, 1915, 1930, 1995, 'FDD', 23),
    ('n26', '850+ FDD',     814,  849,  859,  894, 'FDD', 23),
    ('n28', '700 APT FDD',  703,  748,  758,  803, 'FDD', 23),
    ('n30', '2300 FDD',    2305, 2315, 2350, 2360, 'FDD', 23),
    ('n34', '2000 TDD',    2010, 2025, 2010, 2025, 'TDD', 23),
    ('n38', '2600 TDD',    2570, 2620, 2570, 2620, 'TDD', 23),
    ('n39', '1900 TDD',    1880, 1920, 1880, 1920, 'TDD', 23),
    ('n40', '2300 TDD',    2300, 2400, 2300, 2400, 'TDD', 23),
    ('n41', '2500 TDD',    2496, 2690, 2496, 2690, 'TDD', 26),  # PC2
    ('n48', '3500 CBRS',   3550, 3700, 3550, 3700, 'TDD', 23),
    ('n50', '1500 TDD',    1431, 1517, 1431, 1517, 'TDD', 23),
    ('n51', '1500 TDD',    1427, 1432, 1427, 1432, 'TDD', 23),
    ('n65', '2100+ FDD',   1920, 2010, 2110, 2200, 'FDD', 23),
    ('n66', '1700 AWS-3',  1710, 1780, 2110, 2200, 'FDD', 23),
    ('n70', '1700 AWS-4',  1695, 1710, 1995, 2020, 'FDD', 23),
    ('n71', '600 FDD',      663,  698,  617,  652, 'FDD', 23),
    ('n74', '1500 FDD',    1427, 1470, 1475, 1518, 'FDD', 23),
    ('n75', 'DL 1500',        0,    0, 1432, 1517, 'SDL', 23),
    ('n76', 'DL 1500',        0,    0, 1427, 1432, 'SDL', 23),
    ('n77', '3300 TDD',    3300, 4200, 3300, 4200, 'TDD', 26),
    ('n78', '3500 TDD',    3300, 3800, 3300, 3800, 'TDD', 26),
    ('n79', '4700 TDD',    4400, 5000, 4400, 5000, 'TDD', 26),
    # NR-U (unlicensed)
    ('n46', '5200 NR-U',   5150, 5925, 5150, 5925, 'TDD', 23),
    ('n96', '5900 NR-U',   5925, 7125, 5925, 7125, 'TDD', 23),
]

# Common LTE bands
LTE_BANDS = [
    ('B1',  '2100 FDD', 1920, 1980, 2110, 2170, 'FDD'),
    ('B2',  '1900 FDD', 1850, 1910, 1930, 1990, 'FDD'),
    ('B3',  '1800 FDD', 1710, 1785, 1805, 1880, 'FDD'),
    ('B4',  '1700 FDD', 1710, 1755, 2110, 2155, 'FDD'),
    ('B5',  '850 FDD',   824,  849,  869,  894, 'FDD'),
    ('B7',  '2600 FDD', 2500, 2570, 2620, 2690, 'FDD'),
    ('B8',  '900 FDD',   880,  915,  925,  960, 'FDD'),
    ('B12', '700a FDD',  699,  716,  729,  746, 'FDD'),
    ('B13', '700c FDD',  777,  787,  746,  756, 'FDD'),
    ('B17', '700b FDD',  704,  716,  734,  746, 'FDD'),
    ('B20', '800 FDD',   832,  862,  791,  821, 'FDD'),
    ('B25', '1900+ FDD',1850, 1915, 1930, 1995, 'FDD'),
    ('B26', '850+ FDD',  814,  849,  859,  894, 'FDD'),
    ('B28', '700 APT',   703,  748,  758,  803, 'FDD'),
    ('B34', '2000 TDD', 2010, 2025, 2010, 2025, 'TDD'),
    ('B38', '2600 TDD', 2570, 2620, 2570, 2620, 'TDD'),
    ('B39', '1900 TDD', 1880, 1920, 1880, 1920, 'TDD'),
    ('B40', '2300 TDD', 2300, 2400, 2300, 2400, 'TDD'),
    ('B41', '2500 TDD', 2496, 2690, 2496, 2690, 'TDD'),
    ('B66', '1700 AWS', 1710, 1780, 2110, 2200, 'FDD'),
    ('B71', '600 FDD',   663,  698,  617,  652, 'FDD'),
]

# NR-ARFCN parameters for each band (simplified)
# Ref: 3GPP TS 38.101-1 Table 5.4.2.1-1


def nrarfcn_to_freq(nrarfcn, band=None):
    """Convert NR-ARFCN to frequency (MHz).

    Simplified: F = F_ref + (N - N_ref) * deltaF_global
    For most FR1: deltaF_global = 5kHz or 15kHz
    Approximate: F_MHz ≈ N * 0.005 + 0 MHz (sub-3GHz) or N * 0.015 + 3000 MHz (above 3GHz)
    """
    if nrarfcn <= 600000:
        return nrarfcn * 0.005  # below 3GHz, deltaF = 5kHz
    elif nrarfcn <= 2016667:
        return 3000 + (nrarfcn - 600000) * 0.015  # 3GHz-24.25GHz, deltaF = 15kHz
    else:
        return None


def freq_to_nrarfcn(freq_mhz):
    """Convert frequency (MHz) to approximate NR-ARFCN."""
    if freq_mhz < 3000:
        return int(freq_mhz / 0.005)
    elif freq_mhz < 24250:
        return 600000 + int((freq_mhz - 3000) / 0.015)
    else:
        return None


def earfcn_to_freq_lte(earfcn, direction='DL'):
    """Convert LTE EARFCN to frequency (MHz) for given direction."""
    # Simplified approximation
    if 0 <= earfcn <= 599:
        return 2110 + earfcn * 0.1  # B1 DL
    elif 600 <= earfcn <= 1199:
        return 1930 + (earfcn - 600) * 0.1  # B2 DL
    elif 1200 <= earfcn <= 1949:
        return 1805 + (earfcn - 1200) * 0.1  # B3 DL
    elif 2750 <= earfcn <= 3449:
        return 2620 + (earfcn - 2750) * 0.1  # B7 DL
    # Generic approximate
    return 700 + earfcn * 0.1


def get_band_info(band_name):
    """Look up band info by name like 'n77' or 'B41'."""
    for b in NR_BANDS + LTE_BANDS:
        if b[0] == band_name:
            return b
    return None


def search_band_by_freq(freq_mhz):
    """Find bands that cover the given frequency."""
    results = []
    all_bands = list(NR_BANDS) + [(b[0], b[1], b[2], b[3], b[4], b[5], b[6], '') for b in LTE_BANDS]
    for b in NR_BANDS:
        if b[4] <= freq_mhz <= b[5] or b[2] <= freq_mhz <= b[3]:
            results.append(b)
    return results
