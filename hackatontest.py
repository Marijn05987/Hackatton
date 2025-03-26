import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Cache de gegevensophaal functie om onnodige herhalingen van verzoeken te voorkomen
@st.cache_data
def fetch_data():
    url = 'https://sensornet.nl/dataserver3/event/collection/nina_events/stream?conditions%5B0%5D%5B%5D=time&conditions%5B0%5D%5B%5D=%3E%3D&conditions%5B0%5D%5B%5D=1735689600&conditions%5B1%5D%5B%5D=time&conditions%5B1%5D%5B%5D=%3C&conditions%5B%5D%5B%5D=1742774400&conditions%5B%5D%5B%5D=label&conditions%5B%5D%5B%5D=in&conditions%5B%5D%5B%5D=21&conditions%5B%5D%5B%5D=32&conditions%5B%5D%5B%5D=33&conditions%5B%5D%5B%5D=34&args%5B%5D=aalsmeer&args%5B%5D=schiphol&fields%5B%5D=time&fields%5B%5D=location_short&fields%5B%5D=location_long&fields%5B%5D=duration&fields%5B%5D=SEL&fields%5B%5D=SELd&fields%5B%5D=SELe&fields%5B%5D=SELn&fields%5B%5D=SELden&fields%5B%5D=SEL_dB&fields%5B%5D=lasmax_dB&fields%5B%5D=callsign&fields%5B%5D=type&fields%5B%5D=altitude&fields%5B%5D=distance&fields%5B%5D=winddirection&fields%5B%5D=windspeed&fields%5B%5D=label&fields%5B%5D=hex_s&fields%5B%5D=registration&fields%5B%5D=icao_type&fields%5B%5D=serial&fields%5B%5D=operator&fields%5B%5D=tags'
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Zorgt ervoor dat een HTTP-fout een uitzondering veroorzaakt
        
        if response.status_code == 200:
            colnames = pd.DataFrame(response.json()['metadata'])
            data = pd.DataFrame(response.json()['rows'])
            data.columns = colnames.headers
            data['time'] = pd.to_datetime(data['time'], unit='s')
            return data
        else:
            return None  # Als er een fout is, geef dan geen data terug
            
    except requests.exceptions.RequestException:
        return None  # Als er een netwerkfout of andere fout is, geef dan ook geen data terug

# Mockdata voor 10 vliegtuigen
def get_mock_data():
    data = pd.DataFrame({
        'time': pd.date_range(start="2025-01-01", periods=10, freq='D'),  # 10 vliegtuigen
        'vliegtuig_type': ['Boeing 737-800', 'Embraer ERJ 170-200 STD', 'Embraer ERJ 190-100 STD', 
                           'Boeing 737-700', 'Airbus A320 214', 'Boeing 777-300ER', 
                           'Boeing 737-900', 'Boeing 777-200', 'Airbus A319-111', 'Boeing 787-9'],
        'SEL_dB': [85, 90, 95, 100, 92, 88, 91, 96, 99, 93],
    })
    return data

# Cache de berekeningen van geluid per passagier en vracht
@st.cache_data
def bereken_geluid_per_passagier_en_vracht(data, vliegtuig_capaciteit, load_factor):
    results = []

    for _, row in data.iterrows():
        vliegtuig_type = row['vliegtuig_type']
        if vliegtuig_type in vliegtuig_capaciteit:
            sel_dB = row['SEL_dB']
            passagiers = vliegtuig_capaciteit[vliegtuig_type]['passagiers']
            vracht_ton = vliegtuig_capaciteit[vliegtuig_type]['vracht_ton']
            
            passagiers_bezet = passagiers * load_factor
            geluid_per_passagier = sel_dB / passagiers_bezet if passagiers_bezet != 0 else np.nan
            geluid_per_vracht = sel_dB / vracht_ton if vracht_ton != 0 else np.nan
            
            results.append({
                'vliegtuig_type': vliegtuig_type,
                'passagiers': passagiers,
                'geluid_per_passagier': geluid_per_passagier,
                'geluid_per_vracht': geluid_per_vracht
            })

    return pd.DataFrame(results)

# Stel vliegtuigcapaciteit in
vliegtuig_capaciteit_passagiersaantal = {
    'Boeing 737-800': {'passagiers': 189, 'vracht_ton': 20},
    'Embraer ERJ 170-200 STD': {'passagiers': 80, 'vracht_ton': 7},
    'Embraer ERJ 190-100 STD': {'passagiers': 98, 'vracht_ton': 8},
    'Boeing 737-700': {'passagiers': 130, 'vracht_ton': 17},
    'Airbus A320 214': {'passagiers': 180, 'vracht_ton': 20},
    'Boeing 777-300ER': {'passagiers': 396, 'vracht_ton': 60},
    'Boeing 737-900': {'passagiers': 220, 'vracht_ton': 25},
    'Boeing 777-200': {'passagiers': 314, 'vracht_ton': 50},
    'Airbus A319-111': {'passagiers': 156, 'vracht_ton': 16},
    'Boeing 787-9': {'passagiers': 296, 'vracht_ton': 45},
    'Canadair CL-600-2B19 CRJ-200LR': {'passagiers': 50, 'vracht_ton': 4},
    'Airbus A320 214SL': {'passagiers': 180, 'vracht_ton': 20},
    'Airbus A319 111': {'passagiers': 156, 'vracht_ton': 16},
    'Airbus A320-214SL': {'passagiers': 180, 'vracht_ton': 20},
    'Airbus SAS A330-203': {'passagiers': 277, 'vracht_ton': 45},
    'Boeing 787 8': {'passagiers': 242, 'vracht_ton': 40},
    'Airbus A320 232SL': {'passagiers': 180, 'vracht_ton': 20},
    'Airbus SAS A330-303': {'passagiers': 277, 'vracht_ton': 45},
    'Boeing 737-8MAX': {'passagiers': 210, 'vracht_ton': 25},
    'Airbus A321-232': {'passagiers': 220, 'vracht_ton': 30}
}

# Stel de load factor in (85% van de capaciteit)
load_factor = 0.85

# Streamlit UI
st.title('Geluid per Passagier en Vracht per Vliegtuigtype')
st.markdown('Dit applicatie berekent en toont het geluid per passagier en per ton vracht voor verschillende vliegtuigtypes, gebaseerd op gegevens uit de luchtvaart.')

# Haal de gegevens op van de API of gebruik mockdata
data = fetch_data()

if data is None:
    data = get_mock_data()  # Gebruik mockdata als de API niet werkt

# Voer de berekeningen uit
resultaten = bereken_geluid_per_passagier_en_vracht(data, vliegtuig_capaciteit_passagiersaantal, load_factor)

# Dropdown voor passagierscategorie
passagiers_opties = ['0-50 Passagiers', '51-100 Passagiers', '101-150 Passagiers', 
                     '151-200 Passagiers', '201-250 Passagiers', '251-300 Passagiers', '301+ Passagiers']
passagiers_selectie = st.selectbox('Kies een passagierscategorie:', passagiers_opties)

# Filter de gegevens op basis van de geselecteerde passagierscategorie
categorie_mapping = {
    '0-50 Passagiers': (0, 50),
    '51-100 Passagiers': (51, 100),
    '101-150 Passagiers': (101, 150),
    '151-200 Passagiers': (151, 200),
    '201-250 Passagiers': (201, 250),
    '251-300 Passagiers': (251, 300),
    '301+ Passagiers': (301, np.inf)
}

min_passagiers, max_passagiers = categorie_mapping[passagiers_selectie]
filtered_resultaten = resultaten[(resultaten['passagiers'] >= min_passagiers) & (resultaten['passagiers'] <= max_passagiers)]

# Maak de grafiek voor de geselecteerde passagierscategorie
plt.figure(figsize=(10, 6))
sns.boxplot(x='passagiers_categorie', y='geluid_per_passagier', data=filtered_resultaten, palette='Set2')

plt.title(f'Geluid per Passagier voor {passagiers_selectie}', fontsize=16)
plt.xlabel('Passagierscategorie', fontsize=12)
plt.ylabel('Geluid per Passagier (dB)', fontsize=12)
plt.xticks(rotation=45)

# Toon de grafiek in Streamlit
st.pyplot(plt)



