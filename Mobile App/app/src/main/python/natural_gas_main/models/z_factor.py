"""
Standing-Katz style Z-factor estimators.

The ANN weights and DAK coefficients are adapted from the MIT licensed
mkamyab/zfactor project, which implements methods from:

Kamyab et al., "Using artificial neural networks to estimate the Z-Factor
for natural hydrocarbon gases", Journal of Petroleum Science and Engineering,
2010, 73, 248-257.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
import math
from functools import lru_cache
from typing import Dict, List, Optional, Any

from natural_gas_main.models.gas_data import GasMixture

_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PseudoCriticalProperties:
    temperature_k: float
    pressure_pa: float
    molar_mass_kg_mol: float


@dataclass(frozen=True)
class ZFactorEstimate:
    method: str
    z_factor: Optional[float]
    ppr: float
    tpr: float
    valid: bool
    warning: Optional[str] = None


CRITICAL_PROPS_FALLBACK = {
    "Methane": (190.564, 4.5992e6, 0.016043),
    "Ethane": (305.32, 4.872e6, 0.030070),
    "n-Propane": (369.83, 4.2502e6, 0.044096),
    "Propane": (369.83, 4.2502e6, 0.044096),
    "n-Butane": (425.12, 3.796e6, 0.058122),
    "IsoButane": (407.82, 3.640e6, 0.058122),
    "Isobutane": (407.82, 3.640e6, 0.058122),
    "n-Pentane": (469.7, 3.370e6, 0.072149),
    "Isopentane": (460.35, 3.378e6, 0.072149),
    "Neopentane": (433.78, 3.196e6, 0.072149),
    "n-Hexane": (507.6, 3.025e6, 0.086175),
    "Isohexane": (497.9, 3.040e6, 0.086175),
    "n-Heptane": (540.2, 2.740e6, 0.10020),
    "n-Octane": (568.7, 2.490e6, 0.11423),
    "n-Nonane": (594.6, 2.290e6, 0.12826),
    "n-Decane": (617.7, 2.120e6, 0.14229),
    "n-Undecane": (639.0, 1.980e6, 0.15632),
    "n-Dodecane": (658.0, 1.820e6, 0.17034),
    "Nitrogen": (126.192, 3.3958e6, 0.028013),
    "CarbonDioxide": (304.128, 7.3773e6, 0.04401),
    "HydrogenSulfide": (373.1, 9.00e6, 0.03408),
    "Water": (647.096, 22.064e6, 0.018015),
    "Hydrogen": (32.938, 1.2858e6, 0.002016),
    "Oxygen": (154.581, 5.043e6, 0.031999),
    "Helium": (5.195, 0.2275e6, 0.004003),
    "Argon": (150.687, 4.863e6, 0.039948),
    "CarbonMonoxide": (132.85, 3.4935e6, 0.02801),
    "Ethylene": (282.35, 5.0418e6, 0.02805),
    "Propylene": (365.21, 4.620e6, 0.04208),
    "Air": (132.63, 3.786e6, 0.02897),
    "Methanol": (512.6, 8.09e6, 0.03204),
}

class StandingKatzZFactor:
    """ANN10/ANN5/DAK Z estimators based on pseudo-reduced properties."""

    # Cache for pure-component critical properties (name -> (Tcrit, pcrit, M))
    _props_cache: Dict[str, tuple] = {}

    PPR_MIN = 0.0
    PPR_MAX = 30.0
    TPR_MIN = 1.0
    TPR_MAX = 3.0
    Z_MIN = 0.25194
    Z_MAX = 2.66
    DAK_TOLERANCE = 1e-4
    DAK_MAX_ITERATIONS = 20

    WB1_5 = [
        [-1.5949, 7.9284, 7.2925],
        [-1.7917, 1.2117, 2.221],
        [5.3547, -4.5424, -0.9846],
        [4.6209, 2.2228, 8.9966],
        [-2.3577, -0.1499, -1.5063],
    ]
    WB2_5 = [
        [2.3617, -4.0858, 1.2062, -1.1518, -1.2915, 2.0626],
        [10.0141, 9.8649, -11.4445, -123.0698, 7.5898, 95.1393],
        [10.4103, 14.1358, -10.9061, -125.5468, 6.3448, 93.8916],
        [-1.7794, 14.0742, -1.4195, 12.0894, -15.4537, -9.9439],
        [-0.5988, -0.4354, -0.336, 9.9429, -0.4029, -8.3371],
    ]
    WB3_5 = [1.4979, -37.466, 37.7958, -7.7463, 6.9079, 2.8462]

    WB1_10 = [
        [2.2458, -2.2493, -3.7801],
        [3.4663, 8.1167, -14.9512],
        [5.0509, -1.8244, 3.5017],
        [6.1185, -0.2045, 0.3179],
        [1.3366, 4.9303, 2.2153],
        [-2.8652, 1.1679, 1.0218],
        [-6.5716, -0.8414, -8.1646],
        [-6.1061, 12.7945, 7.2201],
        [13.0884, 7.5387, 19.2231],
        [70.7187, 7.6138, 74.6949],
    ]
    WB2_10 = [
        [4.674, 1.4481, -1.5131, 0.0461, -0.1427, 2.5454, -6.7991, -0.5948, -1.6361, 0.5801, -3.0336],
        [-6.7171, -0.7737, -5.6596, 2.975, 14.6248, 2.7266, 5.5043, -13.2659, -0.7158, 3.076, 15.9058],
        [7.0753, -3.0128, -1.1779, -6.445, -1.1517, 7.3248, 24.7022, -0.373, 4.2665, -7.8302, -3.1938],
        [2.5847, -12.1313, 21.3347, 1.2881, -0.2724, -1.0393, -19.1914, -0.263, -3.2677, -12.4085, -10.2058],
        [-19.8404, 4.8606, 0.3891, -4.5608, -0.9258, -7.3852, 18.6507, 0.0403, -6.3956, -0.9853, 13.5862],
        [16.7482, -3.8389, -1.2688, 1.9843, -0.1401, -8.9383, -30.8856, -1.5505, -4.7172, 10.5566, 8.2966],
        [2.4256, 2.1989, 18.8572, -14.5366, 11.64, -19.3502, 26.6786, -8.9867, -13.9055, 5.195, 9.7723],
        [-16.388, 12.1992, -2.2401, -4.0366, -0.368, -6.9203, -17.8283, -0.0244, 9.3962, -1.7107, -1.0572],
        [14.6257, 7.5518, 12.6715, -12.7354, 10.6586, -43.1601, 1.3387, -16.3876, 8.5277, 45.9331, -6.6981],
        [-6.9243, 0.6229, 1.6542, -0.6833, 1.3122, -5.588, -23.4508, 0.5679, 1.7561, -3.1352, 5.8675],
    ]
    WB3_10 = [-30.1311, 2.0902, -3.5296, 18.1108, -2.528, -0.7228, 0.0186, 5.3507, -0.1476, -5.0827, 3.9767]

    def __init__(self, coolprop_module: Any):
        self.cp = coolprop_module

    def pseudo_critical(self, mixture: GasMixture) -> PseudoCriticalProperties:
        """Calculate Kay-rule pseudo-critical properties.

        Applies Wichert-Aziz (1972) correction when H₂S and/or CO₂
        are present in the mixture.
        """
        mole_fractions = self._mole_fractions(mixture)
        tpc = 0.0
        ppc = 0.0
        molar_mass = 0.0

        for name, x in mole_fractions.items():
            cp_name = GasMixture._format_gas_name_for_coolprop(name)
            if cp_name not in self._props_cache:
                if self.cp is not None:
                    self._props_cache[cp_name] = (
                        self.cp.PropsSI("Tcrit", cp_name),
                        self.cp.PropsSI("pcrit", cp_name),
                        self.cp.PropsSI("M", cp_name),
                    )
                else:
                    # Fallback database when CoolProp is not available
                    if cp_name in CRITICAL_PROPS_FALLBACK:
                        self._props_cache[cp_name] = CRITICAL_PROPS_FALLBACK[cp_name]
                    else:
                        raise ValueError(f"Bileşen '{cp_name}' için kritik özellikler veri tabanında bulunamadı.")
            tc, pc, mw = self._props_cache[cp_name]
            tpc += x * tc
            ppc += x * pc
            molar_mass += x * mw


        if tpc <= 0 or ppc <= 0 or molar_mass <= 0:
            raise ValueError("Pseudo-critical properties could not be calculated")

        y_h2s = mole_fractions.get("HydrogenSulfide", 0.0) + mole_fractions.get("Hidrojen Sülfür", 0.0)
        y_co2 = mole_fractions.get("CarbonDioxide", 0.0) + mole_fractions.get("Karbondioksit", 0.0)
        total_acid = y_h2s + y_co2

        if total_acid > 0.01:
            tpc, ppc = self._wichert_aziz(tpc, ppc, y_h2s, y_co2, total_acid)

        return PseudoCriticalProperties(tpc, ppc, molar_mass)

    @staticmethod
    def _wichert_aziz(
        tpc_k: float,
        ppc_pa: float,
        y_h2s: float,
        y_co2: float,
        total_acid: float,
    ) -> tuple[float, float]:
        """Apply Wichert-Aziz (1972) correction for acid gases.

        Args:
            tpc_k: Kay's rule pseudo-critical temperature (K)
            ppc_pa: Kay's rule pseudo-critical pressure (Pa)
            y_h2s: H₂S mole fraction
            y_co2: CO₂ mole fraction
            total_acid: y_h2s + y_co2

        Returns:
            (corrected_Tpc_K, corrected_Ppc_Pa)

        Reference:
            Wichert, E. and Aziz, K. (1972). "Calculate Z's for Sour Gases."
            Hydrocarbon Processing, Vol. 51, No. 5, pp. 119-122.
        """
        epsilon_r = (
            120.0 * (total_acid ** 0.9 - total_acid ** 1.6)
            + 15.0 * (y_h2s ** 0.5 - y_h2s ** 4.0)
        )
        tpc_r = tpc_k * 9.0 / 5.0
        tpc_prime_r = tpc_r - epsilon_r
        ppc_prime_pa = ppc_pa * tpc_prime_r / (
            tpc_r + y_h2s * (1.0 - y_h2s) * epsilon_r
        )
        tpc_prime_k = tpc_prime_r * 5.0 / 9.0

        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"Wichert-Aziz correction applied: "
            f"y_H2S={y_h2s:.4f}, y_CO2={y_co2:.4f}, "
            f"ε={epsilon_r:.2f}°R, "
            f"Tpc: {tpc_k:.2f}→{tpc_prime_k:.2f}K, "
            f"Ppc: {ppc_pa/1e5:.3f}→{ppc_prime_pa/1e5:.3f}bar"
        )

        return tpc_prime_k, ppc_prime_pa

    @staticmethod
    def sutton_pseudo_critical(
        sg_gas: float,
        y_n2: float = 0.0,
        y_co2: float = 0.0,
        y_h2s: float = 0.0,
    ) -> PseudoCriticalProperties:
        """Sutton (1985) pseudo-critical correlation from specific gravity.

        Use when full gas composition is unknown. Estimates pseudo-critical
        T and P from SG and non-hydrocarbon impurities.

        Reference: Sutton, R.P. (1985), SPE 14265.

        Returns PseudoCriticalProperties in K and Pa.
        """
        y_hc = 1.0 - y_n2 - y_co2 - y_h2s
        if y_hc <= 0:
            raise ValueError("Hydrocarbon fraction must be > 0 for Sutton correlation")

        raw_sg_hc = (sg_gas - 0.9672 * y_n2 - 1.5195 * y_co2 - 1.1767 * y_h2s) / y_hc
        if raw_sg_hc < 0.55:
            _logger.debug(
                f"Sutton SG_hc clamped to 0.55 (raw={raw_sg_hc:.3f}); "
                f"Tpc/Ppc may be overestimated for light gas"
            )
        sg_hc = max(0.55, raw_sg_hc)

        tpc_hc_f = 169.2 + 349.5 * sg_hc - 74.0 * sg_hc ** 2
        ppc_hc_psi = 756.8 - 131.0 * sg_hc - 3.6 * sg_hc ** 2

        tpc_f = y_hc * tpc_hc_f + y_n2 * 227.3 + y_co2 * 548.0 + y_h2s * 672.0
        ppc_psi = y_hc * ppc_hc_psi + y_n2 * 493.0 + y_co2 * 1071.0 + y_h2s * 1306.0

        tpc_k = tpc_f * 5.0 / 9.0
        ppc_pa = ppc_psi * 6894.757

        total_acid = y_co2 + y_h2s
        if total_acid > 0.01:
            tpc_k, ppc_pa = StandingKatzZFactor._wichert_aziz(
                tpc_k, ppc_pa, y_h2s, y_co2, total_acid
            )

        molar_mass = sg_gas * 28.9625 / 1000.0
        return PseudoCriticalProperties(tpc_k, ppc_pa, molar_mass)

    def estimates(
        self,
        mixture: GasMixture,
        temperature_k: float,
        pressure_pa: float,
    ) -> List[ZFactorEstimate]:
        pseudo = self.pseudo_critical(mixture)
        ppr = pressure_pa / pseudo.pressure_pa
        tpr = temperature_k / pseudo.temperature_k
        valid = self._is_valid_range(ppr, tpr)
        warning = None if valid else (
            "Standing-Katz ANN/DAK geçerlilik aralığı dışında "
            f"(0<=Ppr<=30, 1<=Tpr<=3; Ppr={ppr:.3f}, Tpr={tpr:.3f})"
        )

        methods = [
            ("Standing-Katz ANN10", self.ann10),
            ("Standing-Katz ANN5", self.ann5),
            ("Dranchuk-Abou-Kassem", self.dak),
        ]
        estimates = []
        for method, func in methods:
            try:
                z_factor = func(ppr, tpr)
            except Exception as exc:
                estimates.append(ZFactorEstimate(method, None, ppr, tpr, False, str(exc)))
                continue
            estimates.append(ZFactorEstimate(method, z_factor, ppr, tpr, valid, warning))
        return estimates

    def ann10(self, ppr: float, tpr: float) -> float:
        return self._ann(ppr, tpr, self.WB1_10, self.WB2_10, self.WB3_10)

    def ann5(self, ppr: float, tpr: float) -> float:
        return self._ann(ppr, tpr, self.WB1_5, self.WB2_5, self.WB3_5)

    def dak(self, ppr: float, tpr: float) -> float:
        if not self._is_valid_range(ppr, tpr):
            raise ValueError(
                f"DAK input out of valid range: "
                f"Ppr={ppr:.3f} (need 0–30), Tpr={tpr:.3f} (need 1.0–3.0)"
            )
        a1, a2, a3, a4, a5 = 0.3265, -1.07, -0.5339, 0.01569, -0.05165
        a6, a7, a8, a9 = 0.5475, -0.7361, 0.1844, 0.1056
        a10, a11 = 0.6134, 0.721

        z_new = 1.0
        density = self._reduced_density(ppr, tpr, z_new)
        for _ in range(self.DAK_MAX_ITERATIONS):
            z_old = z_new
            z_new = (
                1
                + (a1 + a2 / tpr + a3 / tpr**3 + a4 / tpr**4 + a5 / tpr**5) * density
                + (a6 + a7 / tpr + a8 / tpr**2) * density**2
                - a9 * (a7 / tpr + a8 / tpr**2) * density**5
                + a10 * (1 + a11 * density**2) * density**2 / tpr**3 * math.exp(-a11 * density**2)
            )
            density = self._reduced_density(ppr, tpr, z_new)
            if abs(z_new - z_old) < self.DAK_TOLERANCE:
                break
        else:
            import logging
            logging.getLogger(__name__).warning(
                f"DAK did not converge after {self.DAK_MAX_ITERATIONS} iterations. "
                f"Last Z={z_new:.4f}, Ppr={ppr:.2f}, Tpr={tpr:.2f}"
            )
        if not math.isfinite(z_new) or z_new <= 0:
            raise ValueError("DAK did not converge to a physical Z value")
        return z_new

    def _ann(self, ppr: float, tpr: float, wb1: list, wb2: list, wb3: list) -> float:
        ppr_n = 2.0 / (self.PPR_MAX - self.PPR_MIN) * (ppr - self.PPR_MIN) - 1.0
        tpr_n = 2.0 / (self.TPR_MAX - self.TPR_MIN) * (tpr - self.TPR_MIN) - 1.0

        n1 = [self._log_sig(ppr_n * row[0] + tpr_n * row[1] + row[2]) for row in wb1]
        n2 = []
        for row in wb2:
            neuron = sum(n1[j] * row[j] for j in range(len(n1))) + row[len(n1)]
            n2.append(self._log_sig(neuron))

        z_n = sum(n2[j] * wb3[j] for j in range(len(n2))) + wb3[len(n2)]
        return (z_n + 1) * (self.Z_MAX - self.Z_MIN) / 2 + self.Z_MIN

    def _mole_fractions(self, mixture: GasMixture) -> Dict[str, float]:
        if mixture.fraction_type == "molar":
            total = sum(component.to_decimal() for component in mixture.components)
            return {component.name: component.to_decimal() / total for component in mixture.components}

        mole_amounts = {}
        total_moles = 0.0
        for component in mixture.components:
            cp_name = GasMixture._format_gas_name_for_coolprop(component.name)
            mw = self.cp.PropsSI("M", cp_name)
            moles = component.to_decimal() / mw
            mole_amounts[component.name] = moles
            total_moles += moles

        if total_moles <= 0:
            raise ValueError("Mass fractions could not be converted to mole fractions")
        return {name: moles / total_moles for name, moles in mole_amounts.items()}

    @staticmethod
    def _log_sig(value: float) -> float:
        if value >= 0:
            z = math.exp(-value)
            return 1 / (1 + z)
        z = math.exp(value)
        return z / (1 + z)

    @staticmethod
    def _reduced_density(ppr: float, tpr: float, z_factor: float) -> float:
        return 0.27 * ppr / tpr / z_factor

    @classmethod
    def _is_valid_range(cls, ppr: float, tpr: float) -> bool:
        return cls.PPR_MIN <= ppr <= cls.PPR_MAX and cls.TPR_MIN <= tpr <= cls.TPR_MAX
