# Disease-Symptopedia

An interactive disease-symptom knowledge explorer with Columbia University's Disease-Symptom Knowledge Database.

<img width="1920" height="1030" alt="Capture" src="https://github.com/user-attachments/assets/f0aee52a-4db1-48b8-b8af-6f338dd19258" />

## Data Source

This project uses the **Disease-Symptom Knowledge Database** from Columbia University's Department of Biomedical Informatics (DBMI).

- **Institution**: Columbia University DBMI
- **Original Data**: New York Presbyterian Hospital (2004)
- **Methodology**: MedLEE Natural Language Processing + Statistical Analysis
- **Source URL**: https://people.dbmi.columbia.edu/~friedma/Projects/DiseaseSymptomKB/
- **Reference**: Wang X, Chused A, Elhadad N, Friedman C, Markatou M. Automated Knowledge Acquisition from Clinical Narrative Reports. AMIA Annu Symp Proc. 2008:783-787. PMCID: PMC2656103

## Features

- **Bi-directional Search**: Find diseases by symptoms OR symptoms by diseases
- **Statistical Insights**: View symptom rankings, frequency counts, and associations
- **Interactive UI**: Built with Streamlit for seamless exploration
- **Pre-loaded Data**: CSV files included (no scraping required)
- **Ready to Deploy**: One command to launch the web app

## Quick Start

### Prerequisites

- Python 3.8+
- pip package manager

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/kssrikar4/disease-symptopedia.git
cd disease-symptopedia
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the Streamlit app**
```bash
streamlit run app.py
```

4. **Open your browser**
The app will open at `http://localhost:8501`

## File Structure

```
disease-symptopedia/
│
├── app.py                          # Main Streamlit application
├── utils.py                        # Data loading utilities
├── pipeline.py                     # Web scraper (optional - data already included)
├── requirements.txt                # Python dependencies
├── README.md                       # Project documentation
│
└── disease_symptom_data/           # Pre-loaded CSV datasets
    ├── diseases_20260104_095535.csv                    # 134 diseases
    ├── symptoms_20260104_095535.csv                    # 422 symptoms
    └── disease_symptom_mappings_20260104_095535.csv    # 1865 associations
```

## Dataset Overview

### 1. **diseases_20260104_095535.csv** (7 KB)
| Column | Description |
|--------|-------------|
| `disease_code` | UMLS code for disease |
| `disease_name` | Human-readable disease name |

### 2. **symptoms_20260104_095535.csv** (19 KB)
| Column | Description |
|--------|-------------|
| `symptom_code` | UMLS code for symptom |
| `symptom_name` | Human-readable symptom name |

### 3. **disease_symptom_mappings_20260104_095535.csv** (68 KB)
| Column | Description |
|--------|-------------|
| `disease_name` | Disease name |
| `symptom_name` | Associated symptom |
| `frequency_count` | Number of occurrences in clinical reports |
| `symptom_rank` | Rank of symptom for this disease (1 = most common) |

## Usage

### Tab 1: Symptom → Diseases
1. Select a symptom from the dropdown
2. View all diseases associated with that symptom
3. See how many symptoms each disease has

### Tab 2: Disease → Symptoms
1. Select a disease from the dropdown
2. View all symptoms ranked by frequency
3. Explore top 5 most common symptoms

### Tab 3: Statistics
- View total counts (diseases, symptoms, associations)
- Explore top 10 most common symptoms
- Analyze diseases with the most symptoms

## Pipeline Architecture

The optional `pipeline.py` script performs the following operations:

### 1. **Data Collection**
- Fetches HTML from Columbia DBMI source
- Implements retry logic with exponential backoff
- Handles multiple character encodings (UTF-8, ISO-8859-1, Latin-1, CP1252)

### 2. **HTML Parsing**
- Custom `TableParser` class using Python's `HTMLParser`
- Extracts disease-symptom data from HTML tables
- Handles multi-row disease entries

### 3. **Data Validation**
- Validates UMLS codes
- Cleans and normalizes text data
- Filters invalid/incomplete records

### 4. **Data Processing**
- Extracts unique diseases and symptoms
- Creates disease-to-symptom mappings
- Calculates symptom rankings by frequency

### 5. **CSV Export**
- Generates timestamped CSV files
- Creates three separate datasets (diseases, symptoms, mappings)

### Error Handling
- **Network errors**: Automatic retry with exponential backoff (3 attempts)
- **Encoding errors**: Fallback through 4 different encodings
- **Data validation**: Skips invalid records, logs statistics
- **File I/O errors**: Graceful error messages with stack traces

## Troubleshooting

### Issue: "No data found" error
**Solution**: Ensure the `disease_symptom_data/` folder exists with all 3 CSV files.

### Issue: Port already in use
**Solution**: 
```bash
streamlit run app.py --server.port 8502
```

### Issue: Module not found errors
**Solution**:
```bash
pip install -r requirements.txt --upgrade
```

### Issue: CSV files not loading
**Solution**: Check that CSV filenames match in `app.py` (timestamp should be `20260104_095535`).

### Issue: Want to rescrape data
**Solution**:
```bash
python pipeline.py
```
This will generate new CSV files with updated timestamps.

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file 

### Data Attribution

The disease-symptom dataset is sourced from Columbia University DBMI and is used for educational and research purposes. Please cite the original work:

```bibtex
@article{wang2008automated,
  title={Automated knowledge acquisition from clinical reports},
  author={Wang, Xun and Chused, Alison and Elhadad, Noemie and Friedman, Carol and Markatou, Marianthi},
  journal={AMIA Annual Symposium Proceedings},
  year={2008},
  publisher={American Medical Informatics Association}
}
```

## Disclaimer

**This is a medical knowledge database for informational and educational purposes only.**

- ❌ NOT intended for medical diagnosis or treatment
- ❌ NOT a substitute for professional medical advice
- ✅ Always consult qualified healthcare professionals for medical concerns

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Columbia University Department of Biomedical Informatics
- New York Presbyterian Hospital
- Dr. Carol Friedman and the MedLEE team
- Streamlit for the amazing framework