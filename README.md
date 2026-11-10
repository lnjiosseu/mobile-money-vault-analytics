# Mobile Money Vault Analytics & Support Cost Optimization

## Refined Streamlit dashboard

This Mac-compatible Streamlit dashboard uses validated synthetic portfolio data. It includes four pages: Executive Overview, Demand Analysis, Channel Economics, and Staffing Scenarios.

### Run locally on macOS

From this project folder in the VS Code terminal:

```bash
source .venv/bin/activate
python -m streamlit run app.py
```

If you are setting up a new environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL Streamlit prints, normally `http://localhost:8501`. Keep the terminal running while using the dashboard. Press `Control + C` to stop it.

### Refinements in this version

- Seven-day moving average added to daily support-contact trends.
- Channel names shortened to IVR and Live Support in charts.
- Currency, percentages, and counts formatted for readability.
- Dynamic operational interpretations added to the demand and channel pages.
- CSV download buttons added for selected-period activity and annual summary outputs.
- Single-date selection is handled as a one-day period.
- Contact cost estimates and staffing labor cost estimates are explicitly kept separate.

### Important analytical limitations

- All data are synthetic and do not represent Wave or another company's actual operations.
- Contact costs are assumption-based estimates.
- Staffing scenarios are hourly capacity estimates, not shift rosters or queueing simulations.
- The staffing calculations do not establish wait times, abandonment, or service-level attainment.
- Contact costs are not added to labor costs because the assumptions do not establish whether the cost components overlap.
- The annual channel and staffing summary tables remain full-year summaries and do not change with the daily date filter.

## Suggested portfolio description

Built an interactive Streamlit dashboard in Python to explore synthetic mobile-money vault usage and support operations. The dashboard combines daily and hourly demand analysis, channel-level handling and cost estimates, and staffing sensitivity scenarios. It includes interactive date filtering, seven-day trend smoothing, downloadable analytical outputs, and explicit documentation of modeling assumptions and limitations.
