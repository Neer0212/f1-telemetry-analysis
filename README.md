# 🏎️ F1 Analytics Hub

> Professional-grade Formula 1 data analysis — telemetry, race strategy, championship trends, and machine learning predictions built on real FastF1 timing data.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://f1-telemetry-analysis-neer.streamlit.app/)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastF1](https://img.shields.io/badge/FastF1-3.3+-E8002D)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🔗 Live App

**[f1-telemetry-analysis-neer.streamlit.app](https://f1-telemetry-analysis-neer.streamlit.app/)**

---

## 📸 Pages

| Page | Description |
|------|-------------|
| 📊 **Session Deep Dive** | Lap time distributions, race pace, and tyre strategy for any session since 2018 |
| ⚔️ **Head to Head** | Side-by-side fastest-lap telemetry — speed, delta, throttle & braking |
| 🏆 **Season Championship** | Driver and constructor standings across a full season |
| 🗺️ **Track Speed Map** | Car speed visualised across every metre of a circuit layout |
| 🤖 **Single Race Predict** | ML-powered race finish predictions using 4 trained models |
| 📖 **Race Story** | Lap-by-lap narrative of position changes, overtakes and incidents |
| ⏱️ **Quali Delta** | Lap-by-lap time delta between drivers across a qualifying session |
| 🔧 **Pit Window** | Optimal pit-stop windows and undercut/overcut opportunities |
| 📈 **Multi Season** | Driver and team performance trends across multiple seasons |
| 🛞 **Tyre Degradation** | Real lap-time degradation curves per compound — cliff laps, stint lengths, compound delta |

---

## ⚙️ Tech Stack

- **[FastF1](https://theoehrly.github.io/Fast-F1/)** — official F1 timing & telemetry data
- **[Streamlit](https://streamlit.io/)** — web app framework
- **[Pandas](https://pandas.pydata.org/) / [NumPy](https://numpy.org/)** — data processing
- **[Matplotlib](https://matplotlib.org/)** — visualisations
- **[scikit-learn](https://scikit-learn.org/)** — ML models for race predictions

---

## 🚀 Run Locally

**1. Clone the repo**
```bash
git clone https://github.com/Neer0212/f1-telemetry-analysis.git
cd f1-telemetry-analysis
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Run the app**
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

> FastF1 caches session data locally after the first load — subsequent runs for the same session are significantly faster.

---

## 📁 Project Structure

```
f1-telemetry-analysis/
├── app.py                    # Homepage
├── pages/
│   ├── 1_Deep_Dive.py
│   ├── 2_Head_to_Head.py
│   ├── 3_Season_Championship.py
│   ├── 4_Track_Speed_Map.py
│   ├── 5_Single_Race_Predict.py
│   ├── 6_Race_Story.py
│   ├── 7_Quali_Delta.py
│   ├── 8_Pit_Window.py
│   ├── 9_Multi_Season.py
│   └── 10_Tire_Degradation.py
├── f1_analysis/
│   ├── core/                 # Session loading, lap analysis, telemetry
│   ├── ml/                   # Race prediction models
│   ├── visualization/        # Plots, UI theme, styling
│   └── reports/              # Report generation utilities
└── requirements.txt
```

---

## 📊 Data Coverage

- **Seasons:** 2018 — present
- **Session types:** Race, Qualifying, Sprint, FP1/FP2/FP3
- **Data per race:** ~100,000+ telemetry data points
- **Drivers:** Full 22-driver 2026 grid reference included

---

## 🙏 Credits

- Timing and telemetry data via **[FastF1](https://theoehrly.github.io/Fast-F1/)** by Theo Ehrly
- F1 is a trademark of Formula One Licensing BV — this project is unofficial and not affiliated with Formula 1

---

*Built by [Neer0212](https://github.com/Neer0212)*
