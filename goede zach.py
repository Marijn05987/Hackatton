import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import requests
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import folium
import math
from datetime import datetime
import pytz
from folium.plugins import AntPath
from streamlit_folium import folium_static

# Titel van de Streamlit app
st.title("Hackaton 👩🏼‍✈️👨🏻‍✈️👨🏼‍✈️🧑🏻‍✈️")

# Maak twee tabbladen
tab1, tab2, tab3, tab4 = st.tabs(["🛬🏭Vliegtuigfabrikanten", "🧳🚶🏽‍♀️‍➡️Passagiers en vracht", "🎧Geluidsoverzicht", "👂Geluidsdetectie"])

# Inhoud voor Tabblad 1
with tab1:

 # Titel van de Streamlit app
 st.title("Luidste Vliegtuigfabrikanten")

 # Laad de dataset
 data = pd.read_csv('data_klein.csv')

 # Voeg een nieuwe kolom 'manufacturer' toe met de eerste woordgroep uit 'type'
 data['manufacturer'] = data['type'].str.split().str[0]
 # Voeg een nieuwe kolom 'model' toe door het tweede woord uit de kolom 'type' te halen
 data['model'] = data['type'].str.split().str[1]
 
 # Tel het aantal waarnemingen per fabrikant
 manufacturer_counts = data['manufacturer'].value_counts()
 
 # Filter alleen de fabrikanten die meer dan 5 keer zijn waargenomen
 valid_manufacturers = manufacturer_counts[manufacturer_counts > 5].index
 
 # Filter de dataset op de fabrikanten die meer dan 5 keer zijn waargenomen
 filtered_data = data[data['manufacturer'].isin(valid_manufacturers)]
 
 # Bereken het gemiddelde geluidsniveau per fabrikant
 avg_sound_per_manufacturer = filtered_data.groupby('manufacturer')['lasmax_dB'].mean().sort_values(ascending=False).reset_index()
 
 # Voeg het aantal waarnemingen per fabrikant toe aan de dataset
 avg_sound_per_manufacturer['count'] = avg_sound_per_manufacturer['manufacturer'].map(manufacturer_counts)
 
 # Selecteer de top 20 luidste fabrikanten
 top_manufacturers = avg_sound_per_manufacturer.head(20)
 
 # Bereken de minimale en maximale waarde per fabrikant
 min_max_per_manufacturer = filtered_data.groupby('manufacturer')['lasmax_dB'].agg(['min', 'max']).reset_index()
 
 # Voeg de minimale en maximale waarden toe aan de top_manufacturers dataframe
 top_manufacturers = top_manufacturers.merge(min_max_per_manufacturer[['manufacturer', 'min', 'max']], on='manufacturer')
 
 # Maak een lege figuur aan voor de grafiek
 fig = go.Figure()
 
 # Voeg een enkele staaf toe die begint bij de minimum waarde en eindigt bij de maximum waarde
 for i, row in top_manufacturers.iterrows():
     fig.add_trace(go.Scatter(
         x=[row['min'], row['max']],  # x-waarden van de staaf (min naar max)
         y=[row['manufacturer'], row['manufacturer']],  # y-waarden zijn constant (voor elke fabrikant)
         mode='lines',  # Lijnmodus om een staaf te maken
         line=dict(color='lightblue', width=6),  # Lichtblauwe lijn voor de staaf
         name=row['manufacturer']
     ))
 
     # Voeg een markering toe voor de gemiddelde waarde met het aantal waarnemingen als hover-informatie
     fig.add_trace(go.Scatter(
         x=[row['lasmax_dB']],  # x-positie van de markering
         y=[row['manufacturer']],  # y-positie van de markering
         mode='markers',  # Alleen markeringen (punten)
         marker=dict(color='blue', size=10, symbol='circle'),  # Markering in blauw
         name=f"Gemiddeld: {row['manufacturer']}",
         hoverinfo='text',  # Zet hover-informatie aan
         hovertext=[f"Gemiddeld: {row['lasmax_dB']:.2f} dB<br>Waarnemingen: {row['count']}"],  # Hover tekst met gemiddelde en aantal waarnemingen
         showlegend=False  # Verberg de legenda voor de markeringen
     ))
 
 # Pas de layout aan voor betere zichtbaarheid van labels en de x-as
 fig.update_layout(
     yaxis={'tickmode': 'array'},  # Zorg ervoor dat alle fabrikanten zichtbaar zijn
     margin={"l": 200, "r": 20, "t": 50, "b": 100},  # Vergroot de marge om ruimte te maken voor labels
     width=1000,  # Pas de breedte aan om de grafiek compacter te maken
     height=600,  # Pas de hoogte aan om de grafiek compacter te maken
     xaxis_title='Geluidniveaus (dB)',  # Toevoegen van titel aan de x-as
     yaxis_title='Fabrikant',  # Toevoegen van titel aan de y-as
     showlegend=False,  # Verwijder de legenda aan de rechterkant
     xaxis=dict(
         range=[top_manufacturers['min'].min() - 5, top_manufacturers['max'].max() + 5]  # Stel de x-as limieten in zodat alles zichtbaar is
     ),
     paper_bgcolor='white',  # Achtergrondkleur instellen als wit
     plot_bgcolor='white',  # Achtergrondkleur grafiek instellen als wit
 )
 
 # Draai de y-as labels zodat ze beter leesbaar zijn
 fig.update_layout(
     yaxis_tickangle=-45,  # Draai de y-as labels met -45 graden voor betere leesbaarheid
     font=dict(size=12)  # Verklein het lettertype van de labels om ze beter leesbaar te maken
 )
 
 # Toon de grafiek in de Streamlit interface
 st.plotly_chart(fig)
 
 
 ######################################################################################
 # Filter de rijen waar 'boeing' in de 'type' kolom staat
 boeing_data = data[data['type'].str.contains('Boeing', case=False, na=False)]
 
 # Groepeer het type door alleen het eerste deel van het model te behouden (zoals 'Boeing 777')
 boeing_data['model'] = boeing_data['type'].str.extract(r'(Boeing \d+)')
 
 # Groepeer nu op het nieuwe 'model' en bereken het gemiddelde geluidsniveau per model
 avg_sound_per_boeing_model = boeing_data.groupby('model')['lasmax_dB'].agg(['mean', 'min', 'max']).reset_index()
 
 # Hernoem kolommen voor duidelijkheid
 avg_sound_per_boeing_model.columns = ['model', 'lasmax_dB', 'min_lasmax_dB', 'max_lasmax_dB']
 
 # Sorteer op gemiddeld geluidsniveau
 avg_sound_per_boeing_model = avg_sound_per_boeing_model.sort_values(by='lasmax_dB', ascending=False)
 
 # Maak een lege figuur aan voor de grafiek
 fig = go.Figure()
 
 # Voeg een enkele staaf toe die begint bij de minimum waarde en eindigt bij de maximum waarde
 for i, row in avg_sound_per_boeing_model.iterrows():
     fig.add_trace(go.Scatter(
         x=[row['min_lasmax_dB'], row['max_lasmax_dB']],  # x-waarden van de staaf (min naar max)
         y=[row['model'], row['model']],  # y-waarden zijn constant (voor elke fabrikant)
         mode='lines',  # Lijnmodus om een staaf te maken
         line=dict(color='lightblue', width=6),  # Lichtblauwe lijn voor de staaf
         name=row['model']
     ))
 
     # Voeg een markering toe voor de gemiddelde waarde
     fig.add_trace(go.Scatter(
         x=[row['lasmax_dB']],  # x-positie van de markering
         y=[row['model']],  # y-positie van de markering
         mode='markers',  # Markeringen (punt)
         marker=dict(color='blue', size=10, symbol='circle'),  # Markering in blauw
         name=f"Gemiddeld: {row['model']}",
     ))
 
 # Pas de layout aan voor betere zichtbaarheid van labels en de x-as
 fig.update_layout(
     yaxis={'tickmode': 'array'},  # Zorg ervoor dat alle Boeing-modellen zichtbaar zijn
     margin={"l": 200, "r": 20, "t": 50, "b": 100},  # Vergroot de marge om ruimte te maken voor labels
     width=1000,  # Pas de breedte aan om de grafiek compacter te maken
     height=600,  # Pas de hoogte aan om de grafiek compacter te maken
     xaxis_title='Geluidniveaus (dB)',  # Toevoegen van titel aan de x-as
     yaxis_title='Boeing Model',  # Toevoegen van titel aan de y-as
     showlegend=False,  # Verwijder de legenda aan de rechterkant
     xaxis=dict(
         range=[avg_sound_per_boeing_model['min_lasmax_dB'].min() - 5, avg_sound_per_boeing_model['max_lasmax_dB'].max() + 5]  # Stel de x-as limieten in zodat alles zichtbaar is
     ),
     paper_bgcolor='white',  # Achtergrondkleur instellen als wit
     plot_bgcolor='white',  # Achtergrondkleur grafiek instellen als wit
 )
 
 # Draai de y-as labels zodat ze beter leesbaar zijn
 fig.update_layout(
     yaxis_tickangle=-45,  # Draai de y-as labels met -45 graden voor betere leesbaarheid
     font=dict(size=12)  # Verklein het lettertype van de labels om ze beter leesbaar te maken
 )
 
 # Toon de grafiek in de Streamlit interface
 st.title("Gemiddeld Geluidsniveau per Boeing Model")
 st.plotly_chart(fig)

#################################################################################################################

# Inhoud voor Tabblad 2
with tab2:
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
   
   # Stel de gewenste volgorde van de categorieën in
   category_order = ['0-100 Passagiers', '101-150 Passagiers', '151-200 Passagiers', '201-300 Passagiers', '301+ Passagiers']
   
   st.subheader("Boxplot: Spreiding van Geluid per Passagierscategorie")
   
   fig_box_plot = px.box(
       average_decibels_by_aircraft,
       x='categorie',
       y='Gemiddeld_SEL_dB',
       color='categorie',
       labels={'categorie': 'Passagierscategorie', 'Gemiddeld_SEL_dB': 'Gemiddeld SEL_dB'},
       title='Spreiding van Geluid per Passagierscategorie',
       category_orders={'categorie': category_order}  # Hier stel je de volgorde van de categorieën in
   )
   
   st.plotly_chart(fig_box_plot, use_container_width=True, key="box_plot")   

with tab3:
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

with tab4:
  # Titel van de Streamlit app
 st.title("Geluidsdetectie in Kudelstaartseweg")
 
 # -------------------------------------------------------------------------
 # 1) READ CSVs WITH STREAMLIT CACHE
 # -------------------------------------------------------------------------
 @st.cache_data
 def load_data():
     df = pd.read_csv('flights_today_master.csv')   # Flight data (has the coordinates)
     sensornet = pd.read_csv('my_data.csv')           # Sensor data (includes 'time', 'callsign', 'type', 'distance', 'lasmax_dB', etc.)
     return df, sensornet
 
 df, sensornet = load_data()
 
 # Schiphol coordinates
 SCHIPHOL_LAT = 52.3105
 SCHIPHOL_LON = 4.7683
 
 # -------------------------------------------------------------------------
 # 2) PARSE & TIMEZONE NORMALIZE
 #    (Keep only the "HH:MM:SS" portion in each dataset, both in UTC.)
 # -------------------------------------------------------------------------
 def parse_time_ignoring_weekday(t_str):
     """
     Removes something like 'Mon' (the first 4 chars) and attempts
     to parse what's left as '%I:%M:%S %p'. If parsing fails, returns None.
     """
     if not isinstance(t_str, str):
         return None
     time_part = t_str[4:].strip()  # remove something like "Mon "
     try:
         return pd.to_datetime(time_part, format="%I:%M:%S %p", errors='coerce')
     except:
         return None
 
 # --------------------- Flight data times => final in UTC HH:MM:SS ---------------------
 df['Time'] = df['Time'].apply(parse_time_ignoring_weekday)
 df['Time'] = df['Time'].dt.tz_localize('Etc/GMT+3').dt.tz_convert('UTC')
 df['Time'] = df['Time'].dt.strftime('%H:%M:%S')  # Now just HH:MM:SS as a string
 
 # --------------------- Sensor data => final in UTC HH:MM:SS ---------------------
 sensornet['time'] = pd.to_datetime(sensornet['time'], errors='coerce')
 sensornet['time'] = sensornet['time'].dt.tz_localize('Europe/Amsterdam').dt.tz_convert('UTC')
 sensornet['time'] = sensornet['time'].dt.strftime('%H:%M:%S')
 
 # -------------------------------------------------------------------------
 # 3) HELPER FUNCTIONS
 # -------------------------------------------------------------------------
 def haversine_distance(lat1, lon1, lat2, lon2):
     R = 6371  # Earth radius in km
     from math import radians, sin, cos, atan2, sqrt
     d_lat = radians(lat2 - lat1)
     d_lon = radians(lon2 - lon1)
     a = sin(d_lat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(d_lon/2)**2
     c = 2*atan2(sqrt(a), sqrt(1-a))
     return R * c
 
 def compute_bearing(lat1, lon1, lat2, lon2):
     from math import radians, sin, cos, atan2, degrees
     lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
     d_lon = lon2 - lon1
     x = math.sin(d_lon) * math.cos(lat2)
     y = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(d_lon)
     brng = math.atan2(x, y)
     brng = degrees(brng)
     return (brng + 360) % 360
 
 def midpoint(lat1, lon1, lat2, lon2):
     return ((lat1 + lat2) / 2.0, (lon1 + lon2) / 2.0)
 
 def time_str_to_seconds(t_str):
     """
     Given a time string in HH:MM:SS format, convert to total seconds from midnight.
     Example: "01:02:03" -> 3723 seconds.
     """
     if not isinstance(t_str, str) or len(t_str.split(':')) != 3:
         return None
     hh, mm, ss = t_str.split(':')
     return int(hh)*3600 + int(mm)*60 + int(ss)
 
 # -------------------------------------------------------------------------
 # 4) PLOT THE FLIGHT PATH + DOT MARKERS (with altitude in popup)
 # -------------------------------------------------------------------------
 def plot_flight(df, flight_number, map_obj, color):
     """
     Expects 'df' to have a 'Time' column containing only HH:MM:SS strings in UTC.
     """
     flight_df = df[df['FlightNumber'] == flight_number].copy()
     flight_df.sort_values(by='Time', inplace=True, na_position='first')
     
     # Keep only points within 20 km of Schiphol
     def distance_to_schiphol(row):
         return haversine_distance(SCHIPHOL_LAT, SCHIPHOL_LON, row['Latitude'], row['Longitude'])
     
     flight_df['DistanceToSchiphol'] = flight_df.apply(distance_to_schiphol, axis=1)
     flight_df = flight_df[flight_df['DistanceToSchiphol'] < 20]
     
     if len(flight_df) < 2:
         return  # No path to draw if fewer than 2 points
     
     coords = flight_df[['Latitude','Longitude']].values.tolist()
 
     # Use AntPath with slower animation (delay set to 2500ms)
     folium.plugins.AntPath(
         coords, color=color, weight=3, opacity=0.6, delay=2500
     ).add_to(map_obj)
     
     # For each segment along the flight path, place a small dot marker (in matching color)
     for i in range(len(coords) - 1):
         lat1, lon1 = coords[i]
         lat2, lon2 = coords[i + 1]
         row2 = flight_df.iloc[i + 1]
         
         time2 = row2.get('Time', None)
         altitude_ft = row2.get('Altitude_feet', 'N/A')
         
         if not time2 or time2 in ["NaT", "nan"]:
             popup_str = (
                 f"<b>Flight:</b> {flight_number}<br>"
                 f"<b>Time:</b> N/A<br>"
                 f"<b>Altitude:</b> {altitude_ft} ft"
             )
         else:
             popup_str = (
                 f"<b>Flight:</b> {flight_number}<br>"
                 f"<b>Time:</b> {time2} UTC<br>"
                 f"<b>Altitude:</b> {altitude_ft} ft"
             )
         
         lat_mid, lon_mid = midpoint(lat1, lon1, lat2, lon2)
         
         folium.CircleMarker(
             location=[lat_mid, lon_mid],
             radius=3,  # small dot marker
             color=color,
             fill=True,
             fill_color=color,
             fill_opacity=0.8,
             popup=popup_str
         ).add_to(map_obj)
 
 # -------------------------------------------------------------------------
 # 5) BUILD THE BASE MAP
 # -------------------------------------------------------------------------
 m = folium.Map(location=[52.235, 4.748], zoom_start=11.5)
 
 # 20 km circle around Schiphol
 folium.Circle(
     location=[SCHIPHOL_LAT, SCHIPHOL_LON],
     radius=20000,
     color='lightgray',
     fill=True,
     fill_color='black',
     fill_opacity=0
 ).add_to(m)
 
 # -------------------------------------------------------------------------
 # 6) DEFINE FLIGHTS + COLORS, PLOT THEIR PATHS
 # -------------------------------------------------------------------------
 flight_numbers = ["KLM1342", "PGT1259"]
 colors = ["blue", "red"]
 for fn, col in zip(flight_numbers, colors):
     sub_df = df[df['FlightNumber'] == fn].copy()
     plot_flight(sub_df, fn, m, col)
 
 # -------------------------------------------------------------------------
 # 7) ADD STATIONARY SENSORS (including Kudelstaartseweg)
 # -------------------------------------------------------------------------
 sensors = [
     ("Kudelstaartseweg", 52.235, 4.748)
 ]
 
 for i, (name, lat, lon) in enumerate(sensors):
     # For Kudelstaartseweg, use the PNG marker
     if name == "Kudelstaartseweg":
         folium.Marker(
             location=[lat, lon],
             icon=folium.CustomIcon(
                 icon_image='sound-sensor2.png', 
                 icon_size=(50, 50)
             ),
             popup=f"Sensor: {name}"
         ).add_to(m)
     else:
         color = "darkorange"
         marker_html = f"""
         <div style="border-radius: 50%; background-color: {color};
                     width: 30px; height: 30px;
                     display: flex; align-items: center; justify-content: center;">
             <span style="font-weight: bold; color: black;">{name[:2]}</span>
         </div>
         """
         folium.Marker(
             location=[lat, lon],
             icon=folium.DivIcon(
                 icon_size=(30,30),
                 icon_anchor=(15,15),
                 html=marker_html
             ),
             popup=f"Sensor: {name}"
         ).add_to(m)
 
 # -------------------------------------------------------------------------
 # 8) CREATE MARKERS FOR EACH FLIGHT AT CLOSEST-TIME MATCH,
 #    OFFSET THEM, AND DRAW DASHED LINE.
 #    MARKER COLOR MATCHES THE FLIGHT PATH, DISPLAYS lasmax_dB INSIDE THE ICON,
 #    AND THE POPUP SHOWS SENSOR DATA: time, type, distance (m), and callsign.
 # -------------------------------------------------------------------------
 def add_closest_time_marker(flight, color, df, sensornet, folium_map, offset_lat=0.0, offset_lon=0.0):
     """
     For a given flight, find the sensor time in sensornet for that callsign,
     locate the closest flight-time row in df, place a marker at an offset location,
     and draw a dashed line from that offset to the real lat/lon.
     
     The marker icon shows the 'lasmax_dB' (rounded, with "dB").
     The popup displays sensor data (from the selected row) with keys in bold:
       - Time, Type, Distance (m), Callsign.
     """
     sensor_rows = sensornet[sensornet['callsign'] == flight].copy()
     if sensor_rows.empty:
         return
 
     sensor_row = sensor_rows.iloc[0]
     sensor_time_str = sensor_row['time']     # "HH:MM:SS"
     sensor_time_sec = time_str_to_seconds(sensor_time_str)
     lasmax_value = sensor_row.get('lasmax_dB', None)
     sensor_type = sensor_row.get('type', 'N/A')
     sensor_distance = sensor_row.get('distance', 'N/A')
     sensor_callsign = sensor_row.get('callsign', 'N/A')
     
     flight_rows = df[df['FlightNumber'] == flight].copy()
     if flight_rows.empty:
         return
 
     flight_rows['time_sec'] = flight_rows['Time'].apply(time_str_to_seconds)
     flight_rows['diff'] = (flight_rows['time_sec'] - sensor_time_sec).abs()
     idx_closest = flight_rows['diff'].idxmin()
     
     lat_real = flight_rows.loc[idx_closest, 'Latitude']
     lon_real = flight_rows.loc[idx_closest, 'Longitude']
     flight_time_str = flight_rows.loc[idx_closest, 'Time']  # "HH:MM:SS"
 
     lat_marker = lat_real + offset_lat
     lon_marker = lon_real + offset_lon
 
     if pd.notnull(lasmax_value):
         lasmax_rounded = int(round(lasmax_value))
     else:
         lasmax_rounded = "N/A"
 
     marker_html = f"""
     <div style="border-radius: 50%; background-color: {color};
                 width: 40px; height: 40px;
                 display: flex; align-items: center; justify-content: center;
                 font-weight: bold; color: white;">
         {lasmax_rounded} dB
     </div>
     """
 
     popup_text = (
         f"<b>Flight:</b> {flight}<br>"
         f"<b>Time:</b> {sensor_time_str} UTC<br>"
         f"<b>Type:</b> {sensor_type}<br>"
         f"<b>Distance:</b> {sensor_distance} m<br>"
     )
     
     folium.Marker(
         location=[lat_marker, lon_marker],
         icon=folium.DivIcon(
             icon_size=(40,40),
             icon_anchor=(20,20),
             html=marker_html
         ),
         popup=popup_text
     ).add_to(folium_map)
 
     folium.PolyLine(
         locations=[(lat_marker, lon_marker), (lat_real, lon_real)],
         weight=2,
         color=color,
         dash_array='5,5'
     ).add_to(folium_map)
 
 # Offsets dictionary (adjust as needed for more flights)
 offsets = {
     "KLM1342": (0.0025, 0.0075),   # shift ~30m north
     "PGT1259": (0.0025, -0.0075)   # shift ~30m south
 }
 
 for (fn, col) in zip(flight_numbers, colors):
     off_lat, off_lon = offsets.get(fn, (0.0, 0.0))
     add_closest_time_marker(fn, col, df, sensornet, m, offset_lat=off_lat, offset_lon=off_lon)
 
 # -------------------------------------------------------------------------
 # 9) ADD A LEGEND TO THE MAP
 # -------------------------------------------------------------------------
 legend_html = '''
      <div style="position: fixed; 
                  bottom: 50px; left: 50px; width: 150px; height: 90px; 
                  border:2px solid grey; z-index:9999; font-size:14px;
                  background-color:white;
                  opacity: 0.8;
                  padding: 10px;">
      <b>Flight Legend</b><br>
      <i style="color:blue;">&#9632;</i>&nbsp;KLM1342<br>
      <i style="color:red;">&#9632;</i>&nbsp;PGT1259
      </div>
      '''
 m.get_root().html.add_child(folium.Element(legend_html))
 
 # -------------------------------------------------------------------------
 # 10) DISPLAY THE MAP IN STREAMLIT
 # -------------------------------------------------------------------------
 folium_static(m)
