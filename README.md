# RF Calculator v2.3 — 射频计算工具箱

> 手机射频工程师常用计算工具 | Python + ttkbootstrap + Matplotlib

---

## 目录

1. [阻抗匹配 & Smith圆图](#1-阻抗匹配--smith圆图)
2. [空间损耗和链路预算](#2-空间损耗和链路预算)
3. [传输线 & PCB计算](#3-传输线--pcb计算)
4. [发射机计算](#4-发射机计算)
5. [接收机计算](#5-接收机计算)
6. [频段速查](#6-频段速查)
7. [速率计算](#7-速率计算)
8. [单位换算](#8-单位换算)

---

## 1. 阻抗匹配 & Smith圆图

### 1.1 L-Match 匹配网络

**原理：** 使用一个串联元件 + 一个并联元件将负载阻抗 ZL 匹配到系统阻抗 Z₀。

**匹配公式：**

- **当 RL < Z₀ 时（低阻匹配）：**
  - Q = √(Z₀ / RL − 1)
  - Xs = Q × RL − XL（串联电抗）
  - Bp = Q / Z₀（并联电纳）

- **当 RL > Z₀ 时（高阻匹配）：**
  - Q = √(RL / Z₀ − 1)
  - Xs = ±(Q × Z₀)（串联电抗，正号取电感，负号取电容）
  - XL 被吸收到并联支路：Bp' = Q/RL + BL，其中 BL = −XL/(RL² + XL²)

- **元件值转换：**
  - 电感：L = Xs / ω（ω = 2πf）
  - 电容：C = 1 / (ω × Xs)
  - 电感（并联）：L = 1 / (ω × Bp)
  - 电容（并联）：C = Bp / ω

### 1.2 Single-Stub 匹配

**原理：** 在距负载 d 处并联（或串联）一段长度 l 的终端开路/短路传输线。

**计算公式：**

- **Step 1 — 旋转到 g=1 圆（确定 stub 位置 d）：**
  - tan(βd) = (−BL ± √[GL × (BL² + (1 − GL)²)]) / (GL² + BL² − GL)
  - 其中 yL = gL + jbL = Z₀ / ZL（归一化负载导纳）

- **Step 2 — 计算 stub 长度 l：**
  - 开路 stub：B_stub = tan(βl)
  - 短路 stub：B_stub = −cot(βl)
  - β = 2π / λg（传播常数）

### 1.3 VSWR / Return Loss / |Γ| 互转

**定义：**
- **反射系数 Γ：** Γ = (ZL − Z₀) / (ZL + Z₀)

**互转公式：**
- VSWR = (1 + |Γ|) / (1 − |Γ|)
- Return Loss (dB) = −20 × log₁₀(|Γ|)
- |Γ| = (VSWR − 1) / (VSWR + 1) = 10^(−RL / 20)
- Mismatch Loss (dB) = −10 × log₁₀(1 − |Γ|²)

---

## 2. 空间损耗和链路预算

### 2.1 链路预算（Friis 传输方程）

**原理：** 计算信号从发射机到接收机的功率传递过程。

**计算公式：**

- **EIRP（等效全向辐射功率）：**
  - EIRP (dBm) = Ptx + Gtx − Ltx_cable
  - 其中 Ptx = 发射功率，Gtx = TX 天线增益，Ltx_cable = TX 线缆损耗

- **FSPL（自由空间路径损耗）：**
  - FSPL = (4π × d / λ)²
  - FSPL (dB) = 20 × log₁₀(4π × d / λ)
  - 工程常用：FSPL = 32.44 + 20 × log₁₀(d_km) + 20 × log₁₀(f_MHz)

- **接收功率：**
  - Prx (dBm) = EIRP − FSPL + Grx − Lrx_cable − Margin
  - 其中 Grx = RX 天线增益，Lrx_cable = RX 线缆损耗

### 2.2 自由空间路径损耗（FSPL）

**原理：** 电磁波在自由空间中传播时，功率密度随距离平方衰减。

**计算公式：**
- FSPL (dB) = 20 × log₁₀(4π × d / λ)
- λ = c / f，c ≈ 3 × 10⁸ m/s

**典型值（1 km）：**
| 频率 | FSPL |
|------|------|
| 1 GHz | 92 dB |
| 2.4 GHz | 100 dB |
| 5 GHz | 106 dB |
| 10 GHz | 112 dB |

### 2.3 最大通信距离

**原理：** 在给定各项参数下，接收功率刚好等于灵敏度时的距离。

**计算：** 从 Friis 方程反解 d：
- FSPL_max = EIRP − Sensitivity + Grx − Lrx − Margin
- d_max = (λ / 4π) × 10^(FSPL_max / 20)

---

## 3. 传输线 & PCB计算

### 3.1 微带线（Microstrip）阻抗

**原理：** Wheeler 方程，基于保角变换的近似解。

**计算公式：**

- **有效介电常数（W/h ≤ 1）：**
  - εr_eff = (εr + 1)/2 + (εr − 1)/2 × [1/√(1 + 12h/W) + 0.04 × (1 − W/h)²]

- **有效介电常数（W/h > 1）：**
  - εr_eff = (εr + 1)/2 + (εr − 1)/2 × [1/√(1 + 12h/W)]

- **特性阻抗（W/h ≤ 1）：**
  - Z₀ = 60 / √εr_eff × ln(8h/W + W/4h)

- **特性阻抗（W/h > 1）：**
  - Z₀ = 120π / [√εr_eff × (W/h + 1.393 + 0.667 × ln(W/h + 1.444))]

**参数：**
- W：走线宽度
- h：基板厚度
- εr：基板介电常数
- t：铜厚（可选）

### 3.2 带状线（Stripline）阻抗

**原理：** Cohn 模型，对称带状线。

**计算公式：**

- **窄带近似（W/h < 0.35）：**
  - Z₀ = 60 / √εr × ln(4h / πW)

- **宽带近似（W/h ≥ 0.35）：**
  - Z₀ = 94.15 / [√εr × (W/h + 0.441)]

**特点：** 均匀介质，εr_eff = εr。

### 3.3 共面波导（CPW）阻抗

**原理：** 基于椭圆积分近似。

**计算公式：**
- k = W / (W + 2S)
- k' = √(1 − k²)
- K(k)/K(k') ≈ π / ln[2(1 + √k')/(1 − √k')]（k < 0.707 时）
- Z₀ = 30π / √εr_eff × K(k') / K(k)
- εr_eff ≈ (εr + 1) / 2

**参数：** W = 中心线宽，S = 间隙宽度。

### 3.4 波长计算

**公式：**
- 自由空间波长：λ₀ = c / f
- 导波波长：λg = λ₀ / √εr_eff
- 四分之一波长：λ/4 = λg / 4

### 3.5 趋肤深度

**原理：** 导体在高频下电流集中在表面，有效导电厚度。

**公式：**
- δ = 1 / √(π × f × μ₀ × σ)
- μ₀ = 4π × 10⁻⁷ H/m（真空磁导率）
- σ = 5.8 × 10⁷ S/m（铜的电导率）

**典型值（铜）：**
| 频率 | 趋肤深度 |
|------|----------|
| 1 GHz | 2.1 μm |
| 2.45 GHz | 1.3 μm |
| 5 GHz | 0.9 μm |
| 10 GHz | 0.7 μm |

### 3.6 走线损耗

**原理：** 传输线总损耗 = 导体损耗 + 介质损耗。

#### 3.6.1 导体损耗（αc）

**公式：**
- 表面电阻：Rs = √(π × f × μ₀ / σ)（Ω/□）
- 微带线导体损耗：αc = 8.686 × Rs / (Z₀ × Weff)（dB/m）
- 带状线导体损耗：αc = 8.686 × Rs / (2 × Z₀ × Weff) × [1 + 2W/(πh)]（dB/m）

#### 3.6.2 表面粗糙度修正（Hammerstad 模型）

**公式：**
- Kr = 1 + 2/π × arctan(1.4 × (Rrms / δ)²)
- 实际 Rs = Rs × Kr
- Rrms：RMS 粗糙度（典型值：ED 铜 0.4 μm，厚铜 2.0 μm）

#### 3.6.3 介质损耗（αd）

**微带线：**
- αd = 27.3 × εr/√εr_eff × (εr_eff − 1)/(εr − 1) × tanδ / λ₀（dB/m）

**带状线（均匀介质）：**
- αd = 27.3 × √εr × tanδ / λ₀（dB/m）

**常用损耗角 tanδ：**
| 基板 | tanδ |
|------|------|
| FR4 | 0.020 |
| Rogers 4350B | 0.0037 |
| Rogers 4003C | 0.0027 |
| Rogers 3003 | 0.0013 |
| PTFE | 0.0004 |

#### 3.6.4 总损耗

- α_total = αc + αd
- IL = α_total × L（L 为走线长度）

---

## 4. 发射机计算

### 4.1 IIP3 / OIP3 级联

**原理：** 非线性器件产生的三阶互调产物，多级级联时整体 IIP3 由各级共同决定。

**计算公式：**

- **级联 IIP3（所有值均为线性，非 dB）：**
  - 1 / IIP3_total = 1/IIP3₁ + G₁/IIP3₂ + G₁G₂/IIP3₃ + ...

- **级联 OIP3：**
  - OIP3_total = IIP3_total + Gain_total

- **IMD3 电平（输出端）：**
  - P_IMD3 = 3 × P_out − 2 × OIP3

- **载波干扰比：**
  - C/I = 2 × (OIP3 − P_out)

### 4.2 PAPR（峰均比）

**原理：** 通信信号峰值功率与平均功率的差异。

**公式：**
- PAPR = P_peak − P_avg（dB）

**占空比对平均功率的影响：**
- P_avg = P_peak + 10 × log₁₀(duty% / 100)
- duty% = 10^((P_avg − P_peak) / 10) × 100

**典型 PAPR 值：**
| 信号类型 | PAPR |
|----------|------|
| CW | 3.0 dB |
| QPSK | 4.0 dB |
| 16QAM | 5.5 dB |
| 64QAM | 6.5 dB |
| 256QAM | 7.5 dB |
| LTE CP-OFDM | 8.5 dB |
| NR CP-OFDM | 8.5 dB |
| NR 256QAM | 10.0 dB |
| WiFi 6 | 10.0 dB |

### 4.3 PAE（功率附加效率）

**原理：** PA 将 DC 功率转换为 RF 功率的效率。

**公式：**
- PAE = (Pout − Pin) / Pdc × 100%
- 漏极效率（Drain Efficiency）= Pout / Pdc × 100%
- I_dc = Pdc / Vcc（mA）

**参数：**
- Pout = RF 输出功率（dBm → mW 转换）
- Pin = RF 输入功率（dBm → mW 转换）
- Pdc = DC 功耗（mW）
- Vcc = 供电电压（V）

### 4.4 TX 谐波

**原理：** PA 非线性产生的二次（H2）、三次（H3）等谐波分量。

**公式：**
- Hn_freq = f₀ × n（n = 2, 3, 4...）
- Hn_power = Pout + Hn_suppression（dBm）
- Hn_suppression = Hn 相对于基波的抑制量（dBc）

**3GPP UE 传导谐波限值：** −30 dBm

**所需额外滤波：** Filtering_required = Hn_power − (−30 dBm)

### 4.5 ACLR（邻道泄漏比）预算

**原理：** PA 非线性使得发射信号泄漏到相邻频道。

**从 OIP3 估算 ACLR（近似）：**
- ACLR ≈ 2 × (OIP3 − Pout) − 1.2 × PAPR

**TX 链路 ACLR：**
- TX_ACLR = PA_ACLR − Filter_Rejection

**3GPP 规范：**
- LTE：ACLR ≤ −36 dBc
- NR FR1：ACLR ≤ −30 dBc

---

## 5. 接收机计算

### 5.1 噪声系数级联（Friis 公式）

**原理：** 多级放大器/器件的整体噪声系数由各级 NF 和 Gain 决定。

**公式：**
- F_total = F₁ + (F₂ − 1)/G₁ + (F₃ − 1)/(G₁G₂) + ...

**转换：**
- NF (dB) = 10 × log₁₀(F)
- F = 10^(NF/10)
- G = 10^(Gain/10)

**特点：** 第一级的 NF 和 Gain 对整体噪声系数影响最大。

### 5.2 接收灵敏度预算

**原理：** 接收机能检测到的最小信号功率。

**分步计算：**

1. **热噪声密度：** kT = −174 dBm/Hz（@290K）
   - k = 1.38 × 10⁻²³ J/K（玻尔兹曼常数）
   - T = 290 K（室温）

2. **带宽内噪声：** Noise BW = 10 × log₁₀(BW)

3. **噪声底：** Noise Floor = kT + Noise BW

4. **总噪声：** Total Noise = Noise Floor + NF

5. **灵敏度：** Sensitivity = Total Noise + SNR_min

**Eb/No（每比特能量噪声比）：**
- Eb/No = SNR + 10 × log₁₀(BW / R_b)
- BW = 信号带宽（Hz），R_b = 数据速率（bps）

**示例：**
- BW = 10 MHz，NF = 3 dB，SNR_min = 1 dB
- Sensitivity = −174 + 70 + 3 + 1 = −100 dBm

### 5.3 TX-RX 隔离 & Desense 分析

**原理：** TX 发射信号通过有限隔离泄漏到 RX 通路，抬高 RX 噪声底造成灵敏度下降（退敏）。

**Desense 产生机理：**
1. TX 主信号通过双工器/开关泄漏到 RX
2. PA 宽带噪声在 RX 频段的泄漏
3. 电源/DCDC 纹波耦合
4. MIPI/时钟谐波干扰

**计算：**

1. **泄漏功率：** P_leak = P_TX − Isolation

2. **RX 噪声功率（线性）：** N = k × T × BW × F
   - F = 10^(NF/10)

3. **Desense：** Desense (dB) = 10 × log₁₀(1 + P_leak / N)

**判据：**
| P_leak vs N | Desense | 影响 |
|-------------|---------|------|
| P_leak << N（低 20+ dB） | < 0.1 dB | 可忽略 |
| P_leak ≈ N | ~3 dB | 灵敏度减半 |
| P_leak >> N | 数十 dB | 需增加隔离 |

**典型隔离度：**
| 器件 | 隔离度 |
|------|--------|
| SAW Filter | 25–35 dB |
| BAW Filter | 35–45 dB |
| Duplexer | 50–55 dB |
| Antenna Switch | 20–30 dB |

---

## 6. 频段速查

### 6.1 3GPP NR FR1 Band

包含 35 个 NR 频段（n1, n2, n3, n5, n7, n8, n12, n13, n14, n18, n20, n25, n26, n28, n30, n34, n38, n39, n40, n41, n48, n50, n51, n65, n66, n70, n71, n74, n75, n76, n77, n78, n79, n46, n96）

关键信息：UL/DL 频率范围、双工模式（FDD/TDD/SDL）、UE 功率等级。

### 6.2 LTE Band

包含 21 个常用 LTE 频段（B1, B2, B3, B4, B5, B7, B8, B12, B13, B17, B20, B25, B26, B28, B34, B38, B39, B40, B41, B66, B71）

### 6.3 NR-ARFCN ↔ 频率转换

**公式：**
- **子 3 GHz（ΔF_Global = 5 kHz）：** F_MHz = N × 0.005
- **3–24.25 GHz（ΔF_Global = 15 kHz）：** F_MHz = 3000 + (N − 600000) × 0.015

**反算：**
- **子 3 GHz：** N = F_MHz / 0.005
- **3–24.25 GHz：** N = 600000 + (F_MHz − 3000) / 0.015

---

## 7. 速率计算

### 7.1 WiFi 速率（802.11ac/ax/be）

**原理：** 基于 OFDM，每个 symbol 传输一定数量的数据 bits。

**公式：**
- PHY Rate = N_data_tones × bits_per_symbol_per_SS × N_SP / T_symbol

**参数：**
| 带宽 | 数据子载波数 |
|------|-------------|
| 20 MHz | 234 |
| 40 MHz | 468 |
| 80 MHz | 980 |
| 160 MHz | 1960 |
| 320 MHz | 3920 |

**OFDM 符号时间：**
| Guard Interval | T_symbol |
|---------------|----------|
| 0.8 μs (Short) | 13.6 μs |
| 1.6 μs (Long) | 14.4 μs |
| 3.2 μs | 16.0 μs |

**MCS 与调制/bits per symbol：**
| MCS | 调制 | Bits/SS |
|-----|------|---------|
| 0 | BPSK | 0.50 |
| 1 | QPSK | 1.00 |
| 3 | 16QAM | 2.00 |
| 5 | 64QAM | 4.00 |
| 8 | 256QAM | 6.00 |
| 10 | 1024QAM (WiFi 6) | 7.50 |
| 11 | 1024QAM (WiFi 6) | 8.33 |
| 12 | 4096QAM (WiFi 7) | 9.00 |

**示例：** WiFi 6, 160MHz, MCS11, 2×2: Rate = 1960 × 8.33 × 2 / 13.6e-6 = 2401 Mbps

### 7.2 LTE 速率

**原理：** 基于 RB × 子载波 × OFDM 符号 × 调制阶数 × MIMO × 时间。

**公式：**
- Rate = RB × 12_SC × 14_symbols × Qm × Layers × (1 − OH%) / 1ms × DL_ratio

**其中：**
- RB：资源块数（1.4MHz=6, 3MHz=15, 5MHz=25, 10MHz=50, 15MHz=75, 20MHz=100）
- 12_SC：每个 RB 12 个子载波
- 14_symbols：每个子帧 14 个 OFDM 符号
- Qm：调制阶数（QPSK=2, 16QAM=4, 64QAM=6, 256QAM=8）
- OH%：控制信道开销（~25%）
- DL_ratio：TDD 下行占比（FDD=1.0, TDD Config1=0.6, Config2=0.4...）

**TDD 配置（3GPP TS 36.211）：**
| Config | DL 占比 | 子帧模式 |
|--------|---------|----------|
| FDD | 100% | 全 DL |
| Config 1 | 60% | DSUUDSUUD |
| Config 2 | 40% | DSUDDDSUDD |
| Config 3 | 30% | DSUUUDSUUU |

**示例：** LTE 20MHz, MCS28 (256QAM), 2×2 MIMO, FDD:
- Rate = 100 × 12 × 14 × 8 × 2 × 0.75 / 0.001 = 201.6 Mbps

### 7.3 NR (5G) 速率

**公式：**
- Rate = RB × 12_SC × Slots_per_ms × 14_symbols × Qm × CodeRate × Layers × CA × (1 − OH%) × 1000

**Numerology（子载波间隔）：**
| μ | SCS (kHz) | Slots/ms |
|---|-----------|----------|
| 0 | 15 | 1 |
| 1 | 30 | 2 |
| 2 | 60 | 4 |
| 3 | 120 | 8 |

**FR1 RB 数（SCS=30kHz）：**
| BW (MHz) | RB |
|----------|-----|
| 10 | 24 |
| 20 | 51 |
| 40 | 106 |
| 50 | 133 |
| 100 | 273 |

**NR TDD Slot 模式：**
| Pattern | DL 占比 |
|---------|---------|
| DDDSU (2.5ms) | 74% |
| DDDDDDDSU (5ms) | 77% |
| DDDSUUDDDD (5ms) | 70% |
| DSUUU (2.5ms) | 46% |
| FDD | 100% |

**NR MCS 表（Qm × CodeRate）：**
| MCS | 调制 | Qm | Target CR |
|-----|------|----|-----------|
| 0 | QPSK | 2 | 120/1024 |
| 4 | QPSK | 2 | 308/1024 |
| 10 | 16QAM | 4 | 378/1024 |
| 17 | 64QAM | 6 | 466/1024 |
| 20 | 64QAM | 6 | 616/1024 |
| 27 | 64QAM | 6 | 948/1024 |
| 28 | 256QAM | 8 | 711/1024 |
| 31 | 256QAM | 8 | 841/1024 |

**示例：** NR 100MHz, SCS=30kHz, MCS27, 4×4 MIMO, FDD:
- Rate = 273 × 12 × 2 × 14 × 6 × (948/1024) × 4 × 0.86 × 1000 / 1e6 = 1728 Mbps

---

## 8. 单位换算

### 8.1 功率换算

- P(W) = 10^((P_dBm − 30) / 10)
- P(dBm) = 10 × log₁₀(P_W) + 30
- P(dBW) = P(dBm) − 30
- P(mW) = 10^(P_dBm / 10)

### 8.2 电压换算（@ Z₀ 参考阻抗）

- Vrms = √(P_W × Z₀)
- dBμV = 20 × log₁₀(Vrms × 10⁶) = 20 × log₁₀(Vrms) + 120
- dBmV = dBμV − 60
- dBμV = P(dBm) + 90 + 10 × log₁₀(Z₀)
  - @50Ω: dBμV = dBm + 107.0
  - @75Ω: dBμV = dBm + 108.8

### 8.3 峰值电压

- Vpeak = Vrms × √2
- Vpp = 2 × Vpeak = 2√2 × Vrms

### 8.4 电流

- I_rms = Vrms / Z₀（A）
- I_rms (mA) = Vrms / Z₀ × 1000

### 8.5 dB ↔ 线性比值

- **功率比：** Ratio = 10^(dB/10)，dB = 10 × log₁₀(Ratio)
- **电压比：** Ratio = 10^(dB/20)，dB = 20 × log₁₀(Ratio)

### 8.6 常用对照表

| dBm | 功率 | Vrms @ 50Ω | Vrms @ 75Ω |
|-----|------|-----------|-----------|
| −30 | 1 μW | 7.07 mV | 8.66 mV |
| 0 | 1 mW | 224 mV | 274 mV |
| 10 | 10 mW | 707 mV | 866 mV |
| 20 | 100 mW | 2.24 V | 2.74 V |
| 30 | 1 W | 7.07 V | 8.66 V |
| 40 | 10 W | 22.4 V | 27.4 V |

---

## 运行方式

```bash
pip install -r requirements.txt
python main.py
```

或直接运行预编译版本：`dist/RF_Calculator.exe`

## 技术栈

- Python 3.12
- ttkbootstrap（Bootstrap 风格 UI）
- Matplotlib（Smith 圆图 / 结构示意图）
- NumPy / SciPy（数值计算）
- PyInstaller（打包为独立 EXE）
