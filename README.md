# Proyek Analisis Data: Bike Sharing Dataset

## Struktur
```
submission
├── dashboard
│   ├── dashboard.py
│   ├── main_data.csv      # data harian (bersih)
│   └── hour_data.csv      # data per jam (bersih)
├── data
│   ├── day.csv
│   ├── hour.csv
│   └── Readme.txt
├── Proyek_Analisis_Data.ipynb
├── README.md
├── requirements.txt
└── url.txt
```

## Setup Environment
```
python -m venv .venv
.venv\Scripts\activate        # Windows  (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
```

## Menjalankan Dashboard
```
streamlit run dashboard/dashboard.py
```

## Deploy ke Streamlit Community Cloud
1. Upload folder `submission` ke repository GitHub (publik).
2. Buka https://share.streamlit.io lalu klik **New app**.
3. Pilih repository, branch, dan isi *Main file path* dengan `dashboard/dashboard.py`.
4. Klik **Deploy**, lalu tempel tautan hasilnya ke `url.txt`.
