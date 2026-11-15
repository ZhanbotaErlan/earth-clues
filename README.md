# Earth Clues 🌍

**Explore climate and water trends, then turn data clues into questions and possible actions.**

Earth Clues is an interactive, multilingual Streamlit app built by **Quanthelix team — Zhanbota Erlan**. It explores 17 atmosphere, soil, snow, water, and energy variables for 47 countries across Central, South, Southeast, East, and West Asia. The app uses country-area time series derived from NASA MERRA-2 and GLDAS data.

## What you can do

- Click a country on the map or choose it from the menus; switch the variable used to color the map.
- Explore annual values, seasonal patterns, reference-period anomalies, and descriptive linear trends.
- Compare up to three countries over shared complete years and examine similarity metrics.
- Choose a user role (farmer, city planner, water manager, or resident) to see relevant action ideas.
- Use Presentation Mode for a shorter live demonstration.
- Download an action brief as Markdown or a one-page PDF.
- Open source and country-context links alongside the results.

The interface supports **English, Russian, and Chinese**.

## Run locally

Keep these items together at the repository root:

```text
earth-clues/
├── app.py
├── requirements.txt
├── world_countries.geojson
└── data/
    └── Region/Country/*.csv
```

With Python 3.9 or newer:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

On Windows, activate the environment with `.venv\Scripts\activate` instead.

## Deploy on Streamlit Community Cloud

Upload `README.md`, `LICENSE`, `.gitignore`, `app.py`, `requirements.txt`, `world_countries.geojson`, and the complete `data/` folder to a GitHub repository. In Streamlit Community Cloud, select that repository and set the main file path to `app.py`. The service installs packages listed in `requirements.txt`.

## Data and interpretation

The current files span January 2016 through July 2026. Annual comparisons use **complete years only** (2016–2025 in the supplied dataset); a year needs 12 valid monthly values. Missing values are not treated as zero. Some variables or countries have incomplete coverage.

Anomaly labels compare a country with **its own available record**. They are exploratory screening clues, not official climate normals or safety thresholds. Trend slopes and R² describe the selected data; statistical significance has not been tested. Possible drivers and suggested responses are hypotheses informed by linked country or regional sources, not causal findings. National averages cannot describe city conditions, individual floods, or local impacts.

Known source limitations are shown in the app, including unverified pressure units and country-boundary identity conflicts affecting some comparisons. MERRA-2 and GLDAS are different systems; their water-budget variables should not be assumed to close together.

## Sources

- [NASA MERRA-2 documentation](https://gmao.gsfc.nasa.gov/gmaoftp/mikeb/Harvey/MERRA2.README.pdf)
- [NASA GLDAS model output](https://ldas.gsfc.nasa.gov/gldas/model-output)
- [Natural Earth map data](https://www.naturalearthdata.com/about/terms-of-use/)
- The CSV files include NASA Giovanni reproduction links where available. Country climate context links are displayed in the app.

Earth Clues is an independent project and is not an official NASA product.

## License

The original application code and documentation are released under the [MIT License](LICENSE). The NASA-derived CSV files in `data/` and Natural Earth-derived `world_countries.geojson` retain their respective source terms; the MIT license does not relicense those third-party materials. See the source links above and the reproduction links in the CSV files.

