# Pc Calculation with Monte Carlo Uncertainty
# Based on NASA CARA papers (Bollenbacher & Hejduk)

import numpy as np
import math

def calculate_pc(miss_distance_km, sigma_T_km, nu_eqv_km, A_star_m2):
    sigma_T_m = sigma_T_km * 1000
    nu_eqv_m = nu_eqv_km * 1000
    H_m = miss_distance_km * 1000
    Pc = (A_star_m2 / (2 * math.pi)) * (1 / (sigma_T_m * nu_eqv_m)) * math.exp(-0.5 * (H_m**2) / (nu_eqv_m**2))
    return Pc

def monte_carlo_pc(miss_distance_km, sigma_T_km, nu_eqv_km, A_star_m2, n_samples=5000):
    Pc_values = []
    for _ in range(n_samples):
        scale = np.random.uniform(0.2, 5.0)
        Pc = calculate_pc(miss_distance_km, sigma_T_km * scale, nu_eqv_km * scale, A_star_m2)
        Pc_values.append(Pc)
    Pc_values = np.array(Pc_values)
    return {
        "median": np.median(Pc_values),
        "5th_percentile": np.percentile(Pc_values, 5),
        "95th_percentile": np.percentile(Pc_values, 95),
        "mean": np.mean(Pc_values),
        "std": np.std(Pc_values)
    }

# Example: MOS 43 close approach
miss_distance_km = 15.31
sigma_T_km = 1.0
nu_eqv_km = 1.0
A_star_m2 = 10.0

result = monte_carlo_pc(miss_distance_km, sigma_T_km, nu_eqv_km, A_star_m2, n_samples=5000)
print("Pc Monte Carlo Results:")
print(f"Median Pc: {result['median']:.2e}")
print(f"5th percentile: {result['5th_percentile']:.2e}")
print(f"95th percentile: {result['95th_percentile']:.2e}")
print(f"Mean Pc: {result['mean']:.2e}")
print(f"Std Dev: {result['std']:.2e}")
