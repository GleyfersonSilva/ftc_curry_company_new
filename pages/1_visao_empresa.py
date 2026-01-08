#executar streamlit: streamlit run arquivo.extrensão
#matar o processo: Ctrl+C

# Bibliotecas
import pandas as pd
import numpy as np
import plotly.express as px
from haversine import haversine
import streamlit as st
from PIL import Image
import folium
from streamlit_folium import folium_static

st.set_page_config( page_title ='Company Overview', layout='wide')

# ========================================================================================================================================
#                                                   FUNÇÕES
# ========================================================================================================================================

def clean_code(df1):
    # 1. Convertendo da coluna Age de texto para numero
    linhas_selecionadas = df1['Delivery_person_Age'] != 'NaN '
    df1 = df1.loc[linhas_selecionadas, :].copy()
    df1['Delivery_person_Age'] = df1['Delivery_person_Age'].astype(int)

    # 2. Convertendo a coluna Ratings de texto para número decimal
    df1['Delivery_person_Ratings'] = df1['Delivery_person_Ratings'].astype(float)

    # 3. Convertendo a coluna order_date de texto para data
    df1['Order_Date'] = pd.to_datetime( df1['Order_Date'], format='%d-%m-%Y')

    # 4. Convertendo mutiple_deliveries de texto para número inteiro
    linhas_selecionadas = df1['multiple_deliveries'] != 'NaN '
    df1 = df1.loc[linhas_selecionadas, :].copy()
    df1['multiple_deliveries'] = df1['multiple_deliveries'].astype(int)

    # 5. Removendo os espaços dentro de strings
    # df1 = df1.reset_index(drop=True)
    # for i in range(len(df1)):
    #   df1.loc[i, 'ID'] = df1.loc[i, 'ID'].strip()

    # 6. Removendo os espaços dentro de strings de forma otimizada

    df1.loc[:,'ID'] = df1.loc[:,'ID'].str.strip()
    df1.loc[:,'Delivery_person_ID'] = df1.loc[:,'Delivery_person_ID'].str.strip()
    df1.loc[:,'Road_traffic_density'] = df1.loc[:,'Road_traffic_density'].str.strip()
    df1.loc[:,'Type_of_order'] = df1.loc[:,'Type_of_order'].str.strip()
    df1.loc[:,'Type_of_vehicle'] = df1.loc[:,'Type_of_vehicle'].str.strip()
    df1.loc[:,'Festival'] = df1.loc[:,'Festival'].str.strip()
    df1.loc[:,'City'] = df1.loc[:,'City'].str.strip()

    # 7. Limpando a coluna de Time Taken
    df1 = df1[df1['Time_taken(min)'].notna()].copy()  # remove NaN
    df1['Time_taken(min)'] = df1['Time_taken(min)'].apply(lambda x: x.split('(min) ')[1])
    df1['Time_taken(min)'] = df1['Time_taken(min)'].astype(int)

    # 8. Limpando NaN do dataset

    df1 = df1.loc[df1['Road_traffic_density'] != 'NaN', :]
    df1 = df1.loc[df1['City'] != 'NaN', :]
    df1 = df1.loc[df1['Festival'] != 'NaN', :]


    # 9. adicionando semana do ano

    df1['week_of_year'] = df1['Order_Date'].dt.strftime('%U')
    return df1



# Orders By Day 
def order_by_day(df1):
    df2 = df1.loc[:, ['ID', 'Order_Date']].groupby(['Order_Date']).count().reset_index().sort_values('Order_Date')
    fig = px.bar(df2, x='Order_Date', y='ID')
    return fig

# Orders By Traffic

def order_by_traffic(df1):        
    df2 = df1.loc[:, ['Road_traffic_density', 'ID']].groupby(['Road_traffic_density']).count().reset_index()
    df2['Order_Perc'] = df2['ID'] / df2['ID'].sum()
    df2['Order_Perc'] = df2['Order_Perc'].round(2)
    fig = px.pie(df2, values='Order_Perc', names='Road_traffic_density')
    return fig

# Orders Volume City
def order_volume_city(df1):
    df_aux = df1.loc[:, ['City', 'Road_traffic_density', 'ID']].groupby(['City', 'Road_traffic_density']).count().reset_index()
    fig = px.scatter(df_aux, x='City', y='Road_traffic_density', size='ID', color='City' )
    return fig

# Orders By Week

def order_by_week(df1):
    df2 = df1.loc[:, ['week_of_year', 'ID']].groupby(['week_of_year']).count().reset_index().sort_values('week_of_year')
    fig = px.line(df2, x='week_of_year', y='ID')
    return fig

# Average Deliveries per Driver
def avg_deliveries_driver(df1):
            df_aux01 = df1.loc[:, ['week_of_year', 'ID']].groupby(['week_of_year']).count().reset_index()
            df_aux02 = df1.loc[:, ['week_of_year', 'Delivery_person_ID']].groupby(['week_of_year']).nunique().reset_index()
            df_aux = pd.merge(df_aux01, df_aux02, how='inner')
            df_aux['order_by_deliver'] = df_aux['ID'] / df_aux['Delivery_person_ID']
            fig = px.line(df_aux, x='week_of_year', y='order_by_deliver')
            return fig
        
# Create a Map With Restaurant Locations
def restaurant_location(df1):
        df_aux = df1.loc[:, ['City', 'Road_traffic_density', 'Delivery_location_latitude', 'Delivery_location_longitude']].groupby(['City', 'Road_traffic_density']).median().reset_index()
        map = folium.Map()
        for index, location_info in df_aux.iterrows():
            folium.Marker ([location_info['Delivery_location_latitude'],
                        location_info['Delivery_location_longitude']],
                        popup=location_info[['City', 'Road_traffic_density']]).add_to(map)
        folium_static( map, width=2024, height=600)
        return None

# ========================================================================================================================================
#                                          INÍCIO DA ESTRURURA LÓGICA DO CÓDIGO
# ========================================================================================================================================

# Import dataset
df = pd.read_csv('train.csv')
df1 = df.copy()

# Limpando o Dataset
df1 = clean_code(df1)


# ========================================================================================================================================
#                                                   SIDEBAR COMPONENTS
# ========================================================================================================================================

st.header('Marketplace - Company Overview')

image_path = ('logo.png')
image = Image.open(image_path)
st.sidebar.image( image, width=120)

st.sidebar.markdown('# Curry Company')
st.sidebar.markdown('### Fastest Delivery in Town')
st.sidebar.markdown("""---""")

st.sidebar.markdown('### Choose an end date')

data_minima = df1['Order_Date'].min()
data_minima = data_minima.date()

data_maxima = df1['Order_Date'].max()
data_maxima = data_maxima.date()

data_slider = st.sidebar.slider(
    'Define the value limit',
    value = data_maxima,
    min_value = data_minima,
    max_value = data_maxima,
    format='DD-MM-YYYY'
)

st.sidebar.markdown("""---""")

lista = df1['Road_traffic_density'].unique()

traffic_options = st.sidebar.multiselect(
    'Traffic conditions',
    lista,
    default = lista
)

st.sidebar.markdown("""---""")
st.sidebar.text('Powered by Gleyferson Silva')

# Aplicando os filtros no dataframe

linhas_selecionadas = (df1['Order_Date'].dt.date < data_slider) & (df1['Road_traffic_density'].isin(traffic_options))
df1 = df1.loc[linhas_selecionadas, :]

# ========================================================================================================================================
#                                                   LAYOUT STREAMLIT
# ========================================================================================================================================

tab1, tab2, tab3 = st.tabs(['Management Overview', 'Tactical Overview', 'Geographical Overview'])

# ---------- Management Overview -------------
with tab1:
    with st.container():
        fig = order_by_day(df1)
        st.markdown('### Orders by day')
        st.plotly_chart(fig, use_container_width=True)

    with st.container():
        col1, col2 = st.columns(2)

        with col1:
                fig = order_by_traffic(df1)
                st.markdown('### Orders by traffic contition')
                st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            fig = order_volume_city(df1)
            st.markdown('### Order volume by city & traffic condition')
            st.plotly_chart(fig, use_container_width=True)
            
# ---------- Tactical Overview -------------

with tab2:
    with st.container():
        fig = order_by_week(df1) 
        st.markdown('### Orders by week')
        st.plotly_chart(fig, use_container_width=True)
        
    with st.container():
        fig = avg_deliveries_driver(df1)
        st.markdown('### Average Weekly Deliveries per Driver')
        st.plotly_chart(fig, use_container_width=True)

# ---------- Geographical Overview -------------

with tab3:
    restaurant_location(df1)
    st.markdown('### Restaurant Location Distribution')


    














