# Nusantara SolarWing

NusaSentinel's ISAST 2026 concept study led by Ardhya Novri Ramadhan. This repository contains the energy model, cached NASA POWER input, an interactive static demonstration, and the five-page public concept brief. The model is a proposal screen. Aircraft and route performance have not been validated in flight.

Run `python analyze.py` to regenerate `data/natuna_september_2025.json` and its JavaScript counterpart from the cached raw data. Run `python verify.py` to check data coverage, the saved 29/30 reserve result, and local website references. Open `index.html` through any local static server.

The baseline uses September 2025 NASA POWER hourly irradiance at 4.0 N, 108.0 E, shifted to WIB. Assumptions include 1.65 square metres PV, 24% cell efficiency, 96.5% MPPT efficiency, an 894.24 Wh nominal battery, 90% launch SoC and 20% reserve. The no-wind 08:00–16:00 energy screen passes on 29 of 30 days. This is not a route safety result or evidence of measured endurance.

The public brief contains five concept-paper pages. Its inherited footer mentions an ID appendix, but this five-page file has no appendix. The private submission PDF, student ID, submission form, draft archives, and PDF builder that reads a local student ID are deliberately excluded.

NASA POWER source metadata is retained in the input JSON and output. Primary source: https://power.larc.nasa.gov/docs/services/api/temporal/hourly/ . The website and paper retain the supporting references. Generated with AI coding assistance. No operational or certification claim is made.
