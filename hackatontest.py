import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Cache de gegevensophaal functie om onnodige herhalingen van verzoeken te voorkomen
@st.cache_data
def fetch_data():
    url = 'https://sensornet.nl/dataserver3/event/collection/nina_events/stream?conditions%5B0%5D%5B%5D=time&conditions%5B0%5D%5B%5D=%3E%3D&conditions%5B0%5D%5B%5D=1735689600&conditions%5B1%5D%5B%5D=time&conditions%5B1%5D%5B%5D=%3C&conditions%5B1%5D%5B%5D=1742774400&conditions%5B%5D%5B%5D=label&conditions%5B%5D%5B%5D=in&conditions%5B%5D%5B%5D=21&conditions%5B%5D%5B%5D=32&conditions%5B%5D%5B%5D=33&conditions%5B%5D%5B%5D=34&args%5B%5D=aalsmeer&args%5B%5D=schiphol&fields%5B%5D=time&fields%5B%5D=location_short&fields%5B%5D=location_long&fields%5B%5D=duration&fields%5B%5D=SEL&fields%5B%5D=SELd&fields%5B%5D=SELe&fields%5B%5D=SELn&fields%5B%5D=SELden&fields%5B%5D=SEL_dB&fields%5B%5D=lasmax_dB&fields%5B%5D=callsign&fields%5B%5D=type&fields%5B%5D=altitude&fields%5B%5D=distance&fields%5B%5D=winddirection&fields%5B%5D=windspeed&fields%5B%5D=label&fields%5B%5D=hex_s&fields%5B%5D=registration&fields%5B%5D=icao_type&fields%5B%5D=serial&fields%5B%5D=operator&fields%5B%5D=tags'
    
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
vliegtuig_capaciteit = {
    'Boeing 737-800': {'passagiers': 189, 'vracht_ton': 20},
    'Embraer ERJ 170-200 STD': {'passagiers': 80, 'vracht_ton': 7},
    'Embraer ERJ 190-100 STD': {'passagiers': 98, 'vracht_ton': 8},
    'Boeing 737-700': {'passagiers': 130, 'vracht_ton': 17},
    'Airbus A320 214': {'passagiers': 180, 'vracht_ton': 20},
    'Boeing 777-300ER': {'passagiers': 396, 'vracht_ton': 60},
    'Boeing 737-900': {'passagiers': 220, 'vracht_ton': 25},
    'Boeing 777-200': {'passagiers': 314, 'vracht_ton': 50},
    'Airbus A319-111': {'passagiers': 156, 'vracht_ton': 16},
    'Boeing 787-9': {'passagiers': 296, 'vracht_ton': 45}  # Toegevoegd vliegtuigtype
}

# Stel de load factor in (85% van de capaciteit)
load_factor = 0.85

# Streamlit UI
st.title('Geluid per Passagier en Vracht per Vliegtuigtype')
st.markdown('Deze applicatie berekent en toont het geluid per passagier en per ton vracht voor verschillende vliegtuigtypes, gebaseerd op gegevens uit de luchtvaart. Hieronder zijn de grafieken van de top 10 meest gebruikte vliegtuigen')

# Haal de gegevens op van de API of gebruik mockdata
data = fetch_data()

if data is None:
    data = get_mock_data()  # Gebruik mockdata als de API niet werkt

# Voer de berekeningen uit
resultaten = bereken_geluid_per_passagier_en_vracht(data, vliegtuig_capaciteit, load_factor)

# Sorteer de resultaten
resultaten_sorted_passagier = resultaten.sort_values(by='geluid_per_passagier')
resultaten_sorted_vracht = resultaten.sort_values(by='geluid_per_vracht')

# Maak de grafieken
st.subheader('Grafieken --- Top 10 meest gebruikte vliegtuigen')

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Geluid per Passagier
sns.barplot(x='vliegtuig_type', y='geluid_per_passagier', data=resultaten_sorted_passagier, palette='viridis', ax=axes[0])
axes[0].set_title('Geluid per Passagier per Vliegtuigtype (Met Load Factor)', fontsize=14)
axes[0].set_xlabel('Vliegtuigtype', fontsize=12)
axes[0].set_ylabel('Geluid per Passagier (dB)', fontsize=12)
axes[0].tick_params(axis='x', rotation=45)

# Geluid per Ton Vracht
sns.barplot(x='vliegtuig_type', y='geluid_per_vracht', data=resultaten_sorted_vracht, palette='viridis', ax=axes[1])
axes[1].set_title('Geluid per Ton Vracht per Vliegtuigtype (Zonder Load Factor bij Vracht)', fontsize=14)
axes[1].set_xlabel('Vliegtuigtype', fontsize=12)
axes[1].set_ylabel('Geluid per Ton Vracht (dB)', fontsize=12)
axes[1].tick_params(axis='x', rotation=45)

# Pas de lay-out aan voor betere zichtbaarheid
plt.tight_layout()

# Toon de grafiek in Streamlit
st.pyplot(fig)

# Groeperen op passagiers aantal en vergelijken
st.subheader('Vergelijking van Vliegtuigen op Basis van Passagiersaantal')

# Categoriseer vliegtuigen op basis van passagiers
def categorize_by_passenger(passenger_count):
    if passenger_count <= 100:
        return '0-100 Passagiers'
    elif passenger_count <= 150:
        return '101-150 Passagiers'
    elif passenger_count <= 200:
        return '151-200 Passagiers'
    else:
        return '201+ Passagiers'

resultaten['passagiers_categorie'] = resultaten['passagiers'].apply(categorize_by_passenger)

# Maak de grafiek voor de categorisatie
plt.figure(figsize=(10, 6))
sns.boxplot(x='passagiers_categorie', y='geluid_per_passagier', data=resultaten, palette='Set2')

plt.title('Vergelijking van Geluid per Passagier per Passagierscategorie', fontsize=16)
plt.xlabel('Passagierscategorie', fontsize=12)
plt.ylabel('Geluid per Passagier (dB)', fontsize=12)
plt.xticks(rotation=45)

# Toon de grafiek in Streamlit
st.pyplot(plt)

import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# Stel de maximale weergave van rijen in voor debugging
pd.set_option('display.max_rows', 100000)  # Verhoog het aantal weergegeven rijen

# Cache de gegevensophaal functie om onnodige herhalingen van verzoeken te voorkomen
@st.cache_data
def fetch_data():
    start_date = int(pd.to_datetime('2025-01-01').timestamp())
    end_date = int(pd.to_datetime('2025-03-24').timestamp())
    response = requests.get(f'https://sensornet.nl/dataserver3/event/collection/nina_events/stream?conditions%5B0%5D%5B%5D=time&conditions%5B0%5D%5B%5D=%3E%3D&conditions%5B0%5D%5B%5D={start_date}&conditions%5B1%5D%5B%5D=time&conditions%5B1%5D%5B%5D=%3C&conditions%5B1%5D%5B%5D={end_date}&conditions%5B2%5D%5B%5D=label&conditions%5B2%5D%5B%5D=in&conditions%5B2%5D%5B2%5D%5B%5D=21&conditions%5B2%5D%5B2%5D%5B%5D=32&conditions%5B2%5D%5B2%5D%5B%5D=33&conditions%5B2%5D%5B2%5D%5B%5D=34&args%5B%5D=aalsmeer&args%5B%5D=schiphol&fields%5B%5D=time&fields%5B%5D=location_short&fields%5B%5D=location_long&fields%5B%5D=duration&fields%5B%5D=SEL&fields%5B%5D=SELd&fields%5B%5D=SELe&fields%5B%5D=SELn&fields%5B%5D=SELden&fields%5B%5D=SEL_dB&fields%5B%5D=lasmax_dB&fields%5B%5D=callsign&fields%5B%5D=type&fields%5B%5D=altitude&fields%5B%5D=distance&fields%5B%5D=winddirection&fields%5B%5D=windspeed&fields%5B%5D=label&fields%5B%5D=hex_s&fields%5B%5D=registration&fields%5B%5D=icao_type&fields%5B%5D=serial&fields%5B%5D=operator&fields%5B%5D=tags')
    colnames = pd.DataFrame(response.json()['metadata'])
    data = pd.DataFrame(response.json()['rows'])
    data.columns = colnames.headers
    data['time'] = pd.to_datetime(data['time'], unit='s')
    return data

# Haal de dataset op
data = fetch_data()

# Definieer passagierscategorieën
def categorize_by_passenger_count(passenger_count):
    if passenger_count <= 100:
        return '0-100 Passagiers'
    elif 101 <= passenger_count <= 150:
        return '101-150 Passagiers'
    elif 151 <= passenger_count <= 200:
        return '151-200 Passagiers'
    elif 201 <= passenger_count <= 300:
        return '201-300 Passagiers'
    else:
        return '301+ Passagiers'

# Voeg passagierscategorieën toe aan vliegtuig_capaciteit_passagiersaantal
vliegtuig_capaciteit_passagiersaantal = {
    'Boeing 737-800': {'passagiers': 189, 'vracht_ton': 20},
    'Embraer ERJ 170-200 STD': {'passagiers': 80, 'vracht_ton': 7},
    'Embraer ERJ190-100STD': {'passagiers': 98, 'vracht_ton': 8},
    'Boeing 737-700': {'passagiers': 130, 'vracht_ton': 17},
    'Airbus A320 214': {'passagiers': 180, 'vracht_ton': 20},
    'Boeing 777-300ER': {'passagiers': 396, 'vracht_ton': 60},
    'Boeing 737-900': {'passagiers': 220, 'vracht_ton': 25},
    'Boeing 777-200': {'passagiers': 314, 'vracht_ton': 50},
    'Airbus A319-111': {'passagiers': 156, 'vracht_ton': 16},
    'Boeing 787-9': {'passagiers': 296, 'vracht_ton': 45},
    'Airbus A320 214SL': {'passagiers': 180, 'vracht_ton': 20},
    'Airbus SAS A330-203': {'passagiers': 277, 'vracht_ton': 45},
    'Airbus A320 232SL': {'passagiers': 180, 'vracht_ton': 20},
    'Airbus SAS A330-303': {'passagiers': 277, 'vracht_ton': 45},
    'Boeing 737-8MAX': {'passagiers': 210, 'vracht_ton': 25},
    'Airbus A321-232': {'passagiers': 220, 'vracht_ton': 30},
    'Airbus A380 861': {'passagiers': 555, 'vracht_ton': 80},  # Aantal passagiers kan variëren afhankelijk van de configuratie
    'Embraer ERJ190-100LR': {'passagiers': 98, 'vracht_ton': 8},
    'Airbus A320 232': {'passagiers': 180, 'vracht_ton': 20},
    'Embraer EMB-170 STD': {'passagiers': 70, 'vracht_ton': 7},
    'Airbus A320-271N': {'passagiers': 180, 'vracht_ton': 20},
    'Embraer EMB-195 LR': {'passagiers': 120, 'vracht_ton': 10},
    'Airbus A320-251N': {'passagiers': 180, 'vracht_ton': 20},
    'Boeing 737NG 958ER/W': {'passagiers': 160, 'vracht_ton': 20},
    'Airbus A300 B4-622RF': {'passagiers': 266, 'vracht_ton': 40},
    'Airbus A320 216': {'passagiers': 150, 'vracht_ton': 20},
    'Airbus A330 323E': {'passagiers': 277, 'vracht_ton': 40},
    'Airbus A319 112': {'passagiers': 156, 'vracht_ton': 20},
    'Airbus A350 941': {'passagiers': 315, 'vracht_ton': 60},
    'Airbus A330 302': {'passagiers': 277, 'vracht_ton': 40},
    'Airbus A319 131': {'passagiers': 156, 'vracht_ton': 20},
    'Boeing 787-8 Dreamliner': {'passagiers': 242, 'vracht_ton': 20},
    'Airbus A330 323X': {'passagiers': 277, 'vracht_ton': 40},
    'Boeing 737NG 8AS/W': {'passagiers': 160, 'vracht_ton': 20},
    'Airbus A319 114': {'passagiers': 156, 'vracht_ton': 20},
    'Boeing 777 3FXER': {'passagiers': 396, 'vracht_ton': 55}
}

for aircraft, details in vliegtuig_capaciteit_passagiersaantal.items():
    details['categorie'] = categorize_by_passenger_count(details['passagiers'])

# Controleer of de kolom 'type' bestaat
if 'type' not in data.columns:
    st.error("De kolom 'type' bestaat niet in de dataset. Controleer de kolomnamen en pas de code aan.")
else:
    # Normaliseer de vliegtuigtypen om inconsistenties te voorkomen
    data['type'] = data['type'].str.strip().str.lower()

    # Normaliseer de sleutels in vliegtuig_capaciteit_passagiersaantal
    vliegtuig_capaciteit_passagiersaantal = {
        k.lower(): v for k, v in vliegtuig_capaciteit_passagiersaantal.items()
    }

    # Filter de dataset om alleen vliegtuigen te behouden die in vliegtuig_capaciteit_passagiersaantal staan
    filtered_data = data[data['type'].isin(vliegtuig_capaciteit_passagiersaantal.keys())]

    # Voeg passagiersinformatie toe aan de dataset
    filtered_data['passagiers'] = filtered_data['type'].map(
        lambda x: vliegtuig_capaciteit_passagiersaantal[x]['passagiers']
    )

    # Bereken de gemiddelde SEL_dB per vliegtuigtype
    average_decibels_by_aircraft = filtered_data.groupby('type').agg(
        Gemiddeld_SEL_dB=('SEL_dB', 'mean'),
        Passagiers=('passagiers', 'first')
    ).reset_index()

    # Voeg passagierscategorieën toe
    average_decibels_by_aircraft['categorie'] = average_decibels_by_aircraft['Passagiers'].apply(categorize_by_passenger_count)

    # Maak een dropdownmenu voor passagierscategorieën
    categories = ['0-100 Passagiers', '101-150 Passagiers', '151-200 Passagiers', '201-300 Passagiers', '301+ Passagiers']
    selected_category = st.selectbox('Selecteer een passagierscategorie:', categories)

    # Filter de data op basis van de geselecteerde categorie
    category_data = average_decibels_by_aircraft[average_decibels_by_aircraft['categorie'] == selected_category]

    # Sorteer de data op passagiersaantal
    category_data = category_data.sort_values(by='Passagiers', ascending=False)

    # Maak een interactieve grafiek met Plotly
    fig = px.bar(
        category_data,
        x='Gemiddeld_SEL_dB',
        y='type',
        orientation='h',
        color='Passagiers',
        labels={'type': 'Vliegtuig Type', 'Gemiddeld_SEL_dB': 'Gemiddeld SEL_dB', 'Passagiers': 'Aantal Passagiers'},
        title=f'Gemiddeld Geluid (SEL_dB) voor {selected_category}',
        hover_data=['Gemiddeld_SEL_dB', 'Passagiers']
    )

    # Stel de x-aslimieten in
    fig.update_layout(xaxis=dict(range=[70, 85]))

    # Toon de interactieve grafiek in Streamlit
    st.plotly_chart(fig)



# Bar Chart: Gemiddeld Geluid per Passagierscategorie
# Scatterplot: Correlatie tussen passagiers en gemiddeld geluid
st.subheader("Scatterplot: Correlatie tussen Passagiers en Geluid")
fig_scatter_plot = px.scatter(
    average_decibels_by_aircraft,
    x='Passagiers',
    y='Gemiddeld_SEL_dB',
    color='categorie',
    labels={'Passagiers': 'Aantal Passagiers', 'Gemiddeld_SEL_dB': 'Gemiddeld SEL_dB'},
    title='Correlatie tussen Geluid en Aantal Passagiers',
    hover_data=['type']
)
st.plotly_chart(fig_scatter_plot, use_container_width=True, key="scatter_plot")

# Boxplot: Spreiding van geluid per passagierscategorie
st.subheader("Boxplot: Spreiding van Geluid per Passagierscategorie")
fig_box_plot = px.box(
    average_decibels_by_aircraft,
    x='categorie',
    y='Gemiddeld_SEL_dB',
    color='categorie',
    labels={'categorie': 'Passagierscategorie', 'Gemiddeld_SEL_dB': 'Gemiddeld SEL_dB'},
    title='Spreiding van Geluid per Passagierscategorie'
)
st.plotly_chart(fig_box_plot, use_container_width=True, key="box_plot")


# Line Chart: Tijdreeksanalyse van gemiddeld geluid
st.subheader("Lijngrafiek: Tijdreeksanalyse van Gemiddeld Geluid")
filtered_data['date'] = filtered_data['time'].dt.date
time_series = filtered_data.groupby('date').agg(Gemiddeld_SEL_dB=('SEL_dB', 'mean')).reset_index()
fig_line_chart = px.line(
    time_series,
    x='date',
    y='Gemiddeld_SEL_dB',
    labels={'date': 'Datum', 'Gemiddeld_SEL_dB': 'Gemiddeld SEL_dB'},
    title='Tijdreeksanalyse van Gemiddeld Geluid'
)
st.plotly_chart(fig_line_chart, use_container_width=True, key="line_chart")




# Bar Chart: Gemiddeld Geluid per Weekdag
st.subheader("Bar Chart: Gemiddeld Geluid per Weekdag")

# Voeg een kolom toe voor de dag van de week
filtered_data['weekday'] = filtered_data['time'].dt.day_name()

# Bereken het gemiddelde SEL_dB per weekdag
weekday_data = filtered_data.groupby('weekday').agg(Gemiddeld_SEL_dB=('SEL_dB', 'mean')).reset_index()

# Sorteer de weekdagen in de juiste volgorde
weekday_order = ['Sunday', 'Saturday', 'Friday', 'Thursday', 'Wednesday', 'Tuesday', 'Monday'] 
weekday_data['weekday'] = pd.Categorical(weekday_data['weekday'], categories=weekday_order, ordered=True)
weekday_data = weekday_data.sort_values('weekday')

# Maak de bar chart
fig_weekday_chart = px.bar(
    weekday_data,
    x='Gemiddeld_SEL_dB',
    y='weekday',
    labels={'weekday': 'Weekdag', 'Gemiddeld_SEL_dB': 'Gemiddeld SEL_dB'},
    title='Gemiddeld Geluid (SEL_dB) per Weekdag',
    color='Gemiddeld_SEL_dB',
    color_continuous_scale='Viridis'
)

# Stel de limieten van de x-as in op 60 tot 80
fig_weekday_chart.update_layout(
    xaxis=dict(
        range=[70, 85]  # Limiet van de x-as van 60 tot 80
    )
)

# Toon de chart
st.plotly_chart(fig_weekday_chart, use_container_width=True, key="weekday_chart")
