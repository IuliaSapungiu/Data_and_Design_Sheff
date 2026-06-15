# 🏊‍♂️ SwimMetrics: High-Performance Olympic & Elite Swim Analytics
SwimMetrics is a cutting-edge analytics and predictive scouting application engineered specifically for high-performance swim coaches, elite sports scientists, and national recruiters. 
Leveraging a robust data pipeline running on 25 years of historical World Aquatics Rankings data (2000–2025), this platform shifts swimming data from passive chronological logging into forward-looking talent identification, career trajectory tracking, and performance forecasting.

**🌐 Live Production Link:** [swimmetrics.streamlit.app](https://swimmetrics.streamlit.app/)

---

## 📋 Table of Contents
* [🕹️ How to Use the Platform (User Guide)](#️-how-to-use-the-platform-user-guide)
  * [Step 1: Discovering an Athlete (The Entry Points)](#step-1-discovering-an-athlete-the-entry-points)
  * [Step 2: Accessing Deep-Dive Analytical Dashboards](#step-2-accessing-deep-dive-analytical-dashboards)
* [🚀 Getting Started (Local Development)](#-getting-started-local-development)
  * [📋 Prerequisites](#-prerequisites)
  * [🛠️ Installation & Setup](#️-installation--setup)
* [⚙️ Core Algorithmic & Mathematical Foundations](#️-core-algorithmic--mathematical-foundations)
  * [1. Championship Pace Gap (Elite Evolution Standard)](#1-championship-pace-gap-elite-evolution-standard)
  * [2. Short-Term Form Forecasting](#2-short-term-form-forecasting)
  * [3. Career Trajectory & Long-Term Projections (LA 2028 Target)](#3-career-trajectory--long-term-projections-la-2028-target)
  * [4. Peer-Match Scouting Engine](#4-peer-match-scouting-engine)
* [🏗️ Architectural Overview](#️-architectural-overview)
  * [🧠 UX Engineering: The Performance Engine Pivot](#-ux-engineering-the-performance-engine-pivot)
* [📁 Repository Structure](#-repository-structure)

---

## 🕹️ How to Use the Platform (User Guide)
### Step 1: Discovering an Athlete (The Entry Points)
When you open the web application, you are presented with two primary ways to select and load an athlete's profile into the active memory pipeline:
* **The Master Search Box:** Click into the main global search bar to instantly type and lookup any athlete by name from our multi-decade database.
* **The Executive Leaderboard:** Alternatively, browse the macro global rankings directly on the home interface. Clicking on any swimmer's name inside the dynamic leaderboard tables will automatically lock them in as your target subject.

### Step 2: Accessing Deep-Dive Analytical Dashboards
Once an athlete is actively selected, the sidebar router dynamically un-hides two advanced sub-panels for targeted talent evaluation:

* **📊 1. The Progression Page**
  * Select this page to map out the athlete’s entire development history.
  * View their career acceleration slopes, trajectory metrics, and baseline consistency indexes.
  * Review automated statistical windows, including the **Short-Term Form Forecast** and long-term **Olympic LA 2028 Placements** measured directly against your official target performance bands.

* **⚔️ 2. The Comparator Page**
  * Select this page to run high-fidelity head-to-head scouting reports.
  * Compare your target swimmer against any selected peer in our granular, line-by-line *Tale of the Tape* data matrix.
  * Evaluate holistic profiles using the normalized **5-Axis Scouting Radar Chart**, which visualizes five key performance metrics on a 0–100 scale: Peak Speed, Current Form, Global Threat, Consistency (Standard Deviation), and Momentum (Progression Slope).
  * Explore the **Peer-Match Recommendation Panel**. On initial load, the system dynamically displays all athletes who are intensely aligned with your target's statistical signature. Users can adjust the frontend controls to expand or truncate this comparative peer list to view up to 10 historical twins.

## 🚀 Getting Started
Follow these steps to set up the development environment and run the SwimMetrics platform locally.

### 📋 Prerequisites
Before installation, ensure you have the following installed on your system:
* **Python 3.9 or higher**
* **Pip** (Python package installer)

### 🛠️ Installation & Setup
1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/Data_and_Design_Sheff.git](https://github.com/yourusername/Data_and_Design_Sheff.git)
   cd Data_and_Design_Sheff
   ```

2. **Install core platform dependencies:**
    ```bash
     pip install -r requirements.txt
    ```
3. **Boot the local application server:**
     ```bash
     streamlit run app.py
      ```
## ⚙️ Core Algorithmic & Mathematical Foundations
SwimMetrics isolates raw athletic performance trends from data noise by processing analytics through four fundamental mathematical and machine learning models embedded in the business logic layer:

### 1. Championship Pace Gap (Elite Evolution Standard)
* **Algorithm Used:** Dynamic Top-8 Order Statistics Inversion
* **Purpose:** To construct a highly stable, non-volatile international benchmark representing the physical baseline required to qualify for an elite 8-lane "A-Final" in any given year.
* **Mathematical Formula:**

$$\text{Championship Standard}_t = \frac{1}{8} \sum_{i=1}^{8} x_{(i), t}$$

Where $x_{(i), t}$ denotes the $i$-th fastest time recorded globally for a specific event in year $t$. By relying on the mean of the top 8 order statistics rather than a solitary world record, the platform eliminates outlier skewness caused by singular generational talents or favorable localized pool/suit variations.
  
  The algorithm chart (Progression Tab):
  <img width="1842" height="670" alt="Screenshot 2026-06-11 153025" src="https://github.com/user-attachments/assets/cd156949-5845-4ba1-ba03-94ad0dc2b469" />

### 2. Short-Term Form Forecasting
* **Algorithm Used:** Holt’s Linear Exponential Smoothing (Time-Series Forecasting)
* **Purpose:** To project short-term future performance outcomes and mathematically evaluate an athlete’s current momentum (e.g., assessing if they are actively peaking or entering a performance plateau).
* **Mathematical Formula:**

$$\text{Level Update: } \ell_t = \alpha y_t + (1-\alpha)(\ell_{t-1} + b_{t-1})$$

$$\text{Trend Update: } b_t = \beta(\ell_t - \ell_{t-1}) + (1-\beta)b_{t-1}$$

$$\text{Forecast Equation: } \hat{y}_{t+h\mid t} = \ell_t + hb_t$$

This time-series framework extracts data patterns directly from an athlete's historical sequential races, mapping level ($\ell_t$) and local trend velocity ($b_t$). By tuning smoothing parameters ($\alpha, \beta$), the model weights recent competitive blocks more heavily than outdated multi-year training markers.

  The algorithm chart (Progression Tab):
  <img width="1844" height="904" alt="Screenshot 2026-06-11 182754" src="https://github.com/user-attachments/assets/a731b242-76c7-4dbb-bb30-3897e2a098a7" />

### 3. Career Trajectory & Long-Term Projections (LA 2028 Target)
* **Algorithm Used:** Logarithmic Career Slope Decay Model
* **Purpose:** To simulate career progression pathways and predict target times for future Olympic quadrennials (such as the Los Angeles 2028 Olympic cycle) while respecting human physiological limits.
* **Mathematical Formula:**

$$t_{\text{projected}} = \alpha + \beta \ln(\text{Age}) + \epsilon$$

Because human athletic improvement naturally hits structural ceilings, simple linear regression yields physically impossible projections over long timelines. This model utilizes a logarithmic decay function over historical age-based growth tracks, enforcing the rule of diminishing returns: as a swimmer approaches peak physical maturity, dropping fractional seconds scales down exponentially.

#### 🎯 Baseline LA 2028 Olympic Target Benchmarks
The platform evaluates the logarithmic decay projections against the official milestone targets specified in the project brief. Times longer than one minute are normalized to total seconds within the engine:
##### Men's Olympic Targets
| Event | 🥇 Gold Target | 🥉 Bronze Target | 🏁 Finalist Target |
| :--- | :---: | :---: | :---: |
| **50m Freestyle** | 21.04s | 21.34s | 21.96s |
| **100m Freestyle** | 46.17s | 47.02s | 48.34s |
| **200m Freestyle** | 103.67s | 103.74s | 106.26s |
| **400m Freestyle** | 222.00s | 224.00s | 226.78s |
| **100m Backstroke** | 51.50s | 52.20s | 53.74s |
| **200m Backstroke** | 113.50s | 115.00s | 117.50s |
| **100m Breaststroke** | 57.50s | 58.50s | 59.49s |
| **200m Breaststroke** | 126.00s | 128.00s | 129.68s |
| **100m Butterfly** | 49.50s | 50.50s | 51.67s |
| **200m Butterfly** | 111.00s | 113.00s | 115.78s |
| **200m Medley** | 115.00s | 116.50s | 117.94s |

##### Women's Olympic Targets
| Event | 🥇 Gold Target | 🥉 Bronze Target | 🏁 Finalist Target |
| :--- | :---: | :---: | :---: |
| **50m Freestyle** | 23.47s | 24.20s | 24.70s |
| **100m Freestyle** | 51.64s | 51.81s | 53.61s |
| **200m Freestyle** | 112.14s | 113.41s | 117.26s |
| **400m Freestyle** | 236.00s | 239.00s | 247.90s |
| **100m Backstroke** | 57.50s | 58.50s | 59.99s |
| **200m Backstroke** | 124.00s | 126.00s | 130.39s |
| **100m Breaststroke** | 64.50s | 65.50s | 66.79s |
| **200m Breaststroke** | 139.00s | 141.00s | 143.91s |
| **100m Butterfly** | 55.50s | 56.50s | 57.92s |
| **200m Butterfly** | 124.00s | 126.00s | 128.43s |
| **200m Medley** | 127.00s | 129.00s | 131.47s |

  The algorithm chart (Progression Tab):
  <img width="1816" height="750" alt="Screenshot 2026-06-11 153428" src="https://github.com/user-attachments/assets/43fd0d89-e60e-4e83-8ceb-16f9935e61d8" />

### 4. Peer-Match Scouting Engine
* **Algorithm Used:** Multi-Dimensional Euclidean Distance Matching / K-Nearest Neighbors (KNN Variant)
* **Purpose:** To scan the multi-decade database and uncover historical structural twins for emerging junior athletes, assisting scouts in mapping out multi-year development blueprints.
* **Mathematical Formula:**

$$d(\mathbf{p}, \mathbf{q}) = \sqrt{\sum_{i=1}^{n} \left( \frac{p_i - q_i}{\sigma_i} \right)^2}$$

The matching engine structures an $n$-dimensional feature space using normalized, scale-invariant athletic coordinates including:
* Historical progression slope velocity
* Career standard deviation (consistency index)
* Peak capability metrics
* Chronological age vectors
By calculating the minimum distance $d(\mathbf{p}, \mathbf{q})$ between the target vector $\mathbf{p}$ and global dataset vectors $\mathbf{q}$, it identifies structural "statistical twins" whose historical career pathways offer reliable blueprint scenarios for current performance development.

  The algorithm chart (Comparator Tab):
  <img width="1847" height="913" alt="Screenshot 2026-06-11 182905" src="https://github.com/user-attachments/assets/9e366762-a881-4535-a971-c07454ac8431" />
  <img width="1566" height="880" alt="Screenshot 2026-06-11 182921" src="https://github.com/user-attachments/assets/baf2c4ab-41d5-4fea-8fb5-9e6e6e0fc9fe" />
  <img width="1885" height="891" alt="Screenshot 2026-06-11 182936" src="https://github.com/user-attachments/assets/58942c59-7e15-4f9c-8951-b092dc3fa1b5" />

## 🏗️ Architectural Overview
The system uses a strict, decoupled multi-layered architecture designed to separate data ingestion, analytical business logic, and presentation interfaces.

```text
┌───────────────────────────────────────────────┐
│                     USER                      │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│              STREAMLIT FRONTEND               │
│                                               │
│ app.py (Router)    | control_room.py (Home)   │
│ shared_ui.py       | pages/                   │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│    BUSINESS LOGIC LAYER - ANALYTICS ENGINE    │
│                                               │
│ progression.py     | performance.py           │
│ comparator.py      | loader.py                │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│                  DATA LAYER                   │
│                                               │
│ data_processor.py                             │
│ WA_Rankings_2000_2025_Master_v1.parquet       │
└───────────────────────────────────────────────┘
```

## 📁 Repository Structure

```
Data_and_Design_Sheff/
│
├── data/
│   ├── .streamlit/                               # Configuration settings for Streamlit UI
│   ├── WA_Rankings_2000_2025_Master_v1.parquet   # Core high-performance dataset
│   └── data_processor.py                         # Data cleaning, sanitization, and I/O pipeline
│
├── features/                                     # BUSINESS LOGIC / ANALYTICS LAYER
│   ├── comparator.py                             # Tail-of-the-tape & radar normalization logic
│   ├── loader.py                                 # Optimized data caching and memory manager
│   ├── performance.py                            # Background Top 8 gap & form utility engine
│   └── progression.py                            # Historical slope & consistency calculators
│
├── pages/                                        # PRESENTATION / UI LAYER
│   ├── 01_progression.py                         # Trajectory visualizations & predictive curves
│   ├── 02_performance.py                         # (De-integrated UI module - acts via background engine)
│   └── 03_comparator.py                          # Head-to-head metrics & radar maps
│
├── .gitignore
├── SwimMetrics-Logo.png
├── WHITESwimMetrics-Logo.png
├── app.py                                        # Global application router & configuration
├── control_room.py                               # Executive macro leaderboard dashboard
├── shared_ui.py                                  # UI brand elements & component layout wrappers
└── requirements.txt                              # Core platform dependencies

```


