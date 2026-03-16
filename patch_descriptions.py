import re

file_path = "src/coreason_manifest/spec/ontology.py"
with open(file_path) as f:
    content = f.read()

replacements = {
    r'generative_persona: Literal\["hesitant_novice", "fast_expert", "distracted_browser"\] = Field\(\n        default="fast_expert", description="The imitation learning persona governing the emulation."\n    \)': r'generative_persona: Literal["hesitant_novice", "fast_expert", "distracted_browser"] = Field(\n        default="fast_expert",\n        description="The imitation learning persona governing the behavioral emulation profile.",\n    )',
    r'kinematic_noise: "KinematicNoiseProfile \| None" = Field\(default=None\)': r'kinematic_noise: "KinematicNoiseProfile | None" = Field(\n        default=None,\n        description="The stochastic pointer trajectory perturbation profile for human-like motor control emulation.",\n    )',
    r'environmental_spoofing: "EnvironmentalSpoofingProfile \| None" = Field\(default=None\)': r'environmental_spoofing: "EnvironmentalSpoofingProfile | None" = Field(\n        default=None,\n        description="The browser fingerprint and environmental telemetry spoofing geometry.",\n    )',
    r"emulation_fidelity_target: float = Field\(..., ge=0.0, le=1.0\)": r'emulation_fidelity_target: float = Field(\n        ge=0.0,\n        le=1.0,\n        description="The target normalized score for human-likeness against anti-bot heuristic classifiers.",\n    )',
    r'tls_cipher_permutation: Literal\["chrome_windows", "safari_macos", "firefox_macos", "android_webview"\] = Field\(\n        default="chrome_windows", description="The JA3/JA4 TLS Client Hello fingerprint to project."\n    \)': r'tls_cipher_permutation: Literal["chrome_windows", "safari_macos", "firefox_macos", "android_webview"] = Field(\n        default="chrome_windows",\n        description="The JA3/JA4 TLS Client Hello fingerprint to project during handshake emulation.",\n    )',
    r'webgl_entropy_seed_hash: str = Field\(..., min_length=1, max_length=128, pattern="\^\[a-zA-Z0-9_.:-\]\+\$"\)': r'webgl_entropy_seed_hash: str = Field(\n        min_length=1,\n        max_length=128,\n        pattern="^[a-zA-Z0-9_.:-]+$",\n        description="The Content Identifier (CID) of the WebGL canvas entropy seed used to generate a deterministic spoofed fingerprint.",\n    )',
    r"user_agent_template: str = Field\(..., max_length=2000\)": r'user_agent_template: str = Field(\n        max_length=2000,\n        description="The User-Agent string template projected to exogenous web servers to mask the true computational substrate.",\n    )',
    r'hardware_concurrency_mask: int = Field\(\n        default=8, gt=0, le=256, description="Spoofed CPU core count projected to the DOM."\n    \)': r'hardware_concurrency_mask: int = Field(\n        gt=0,\n        le=256,\n        default=8,\n        description="The spoofed CPU core count projected to the DOM via navigator.hardwareConcurrency.",\n    )',
    r"timezone_offset_minutes: int = Field\(..., ge=-720, le=840\)": r'timezone_offset_minutes: int = Field(\n        ge=-720,\n        le=840,\n        description="The spoofed UTC timezone offset in minutes, bounded to the valid terrestrial range.",\n    )',
    r"screen_resolution_width: int = Field\(..., ge=1, le=15360\)": r'screen_resolution_width: int = Field(\n        ge=1,\n        le=15360,\n        description="The spoofed horizontal display resolution in pixels.",\n    )',
    r"screen_resolution_height: int = Field\(..., ge=1, le=15360\)": r'screen_resolution_height: int = Field(\n        ge=1,\n        le=15360,\n        description="The spoofed vertical display resolution in pixels.",\n    )',
    r'velocity_profile: Literal\["minimum_jerk", "constant", "fractional_brownian"\] = Field\(\n        default="minimum_jerk", description="The mathematical model governing movement acceleration."\n    \)': r'velocity_profile: Literal["minimum_jerk", "constant", "fractional_brownian"] = Field(\n        default="minimum_jerk",\n        description="The mathematical model governing movement acceleration and velocity smoothing.",\n    )',
    r"pink_noise_amplitude: float = Field\(..., ge=0.0, le=1.0\)": r'pink_noise_amplitude: float = Field(\n        ge=0.0,\n        le=1.0,\n        description="The normalized amplitude of the 1/f noise injected into the pointer trajectory. Bounded [0.0, 1.0].",\n    )',
    r"frequency_exponent: float = Field\(..., ge=0.0, le=5.0\)": r'frequency_exponent: float = Field(\n        ge=0.0,\n        le=5.0,\n        description="The spectral exponent β in the 1/f^β power spectral density function governing noise color.",\n    )',
    r'target_overshoot_radius_pixels: int = Field\(\n        default=0, ge=0, le=5000, description="The Euclidean radius for corrective submovements."\n    \)': r'target_overshoot_radius_pixels: int = Field(\n        ge=0,\n        le=5000,\n        default=0,\n        description="The Euclidean radius in pixels for corrective submovements overshooting the target coordinate.",\n    )',
    r'hick_hyman_dwell_time_ms: int = Field\(\n        default=0, ge=0, le=86400000, description="Cognitive choice reaction delay in milliseconds."\n    \)': r'hick_hyman_dwell_time_ms: int = Field(\n        ge=0,\n        le=86400000,\n        default=0,\n        description="Cognitive choice reaction delay in milliseconds, modeled via Hick-Hyman Law.",\n    )',
    r'noise_type: Literal\["pink", "brownian", "gaussian"\] = Field\(...\)': r'noise_type: Literal["pink", "brownian", "gaussian"] = Field(\n        description="The stochastic process governing the noise generation for pointer trajectory perturbation.",\n    )',
}

for old, new in replacements.items():
    content = re.sub(old, new, content)

with open(file_path, "w") as f:
    f.write(content)
