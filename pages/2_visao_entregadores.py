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

st.set_page_config( page_title ='Overall Metrics', layout='wide')

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


# Average Rating By courier
def avg_rating_courier(df1):
                df2 = (df1.loc[:, ['Delivery_person_ID', 'Delivery_person_Ratings']].groupby(['Delivery_person_ID'])
                                                                                    .mean()
                                                                                    .round(2)
                                                                                    .reset_index()
                                                                                    .sort_values('Delivery_person_Ratings', ascending=False))
                return df2

# Average Rating By Traffic
def avg_rating_traffic(df1):
    df2 = (df1.loc[:, ['Road_traffic_density', 'Delivery_person_Ratings']].groupby(['Road_traffic_density'])
                                                                            .agg({'mean', 'std'})
                                                                            .round(2))
    df2.columns = ['Delivery_mean', 'Delivery_Std']
    df2 = df2.reset_index()
    return df2

# Average Rating By Weatherconditions
def avg_rating_wc(df1):
                df2 = (df1.loc[:, ['Weatherconditions', 'Delivery_person_Ratings']].groupby(['Weatherconditions'])
                                                                                    .agg({'mean', 'std'})
                                                                                    .round(2))
                df2.columns = ['Delivery_mean', 'Delivery_std']
                df2 = df2.reset_index()
                return df2

# Top Fastest Couriers
def top_fastest(df1):
    df2 = (df1.loc[:, ['City', 'Delivery_person_ID', 'Time_taken(min)']].groupby(['City','Delivery_person_ID'])
                                                                        .mean()
                                                                        .round(2)
                                                                        .reset_index())
    df_top = df2.sort_values(['City', 'Time_taken(min)']).groupby(['City']).head(10).reset_index(drop=True)
    return df_top

# Top Slowest Couriers
def top_slowest(df1):
    df2 = (df1.loc[:, ['City', 'Delivery_person_ID', 'Time_taken(min)']].groupby(['City','Delivery_person_ID'])
                                                                        .mean()
                                                                        .round(2)
                                                                        .reset_index())
    df_top = df2.sort_values(['City', 'Time_taken(min)'], ascending=False).groupby(['City']).head(10).reset_index(drop=True)
    return df_top

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

st.header('Overall Metrics')

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

tab1, tab2, tab3 = st.tabs(['Management Overview', '-', '-'])

#------------------- Cards -----------------------
with tab1:
    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            maior_idade = df1['Delivery_person_Age'].max()
            st.metric(label='Oldest Courier Age', value=maior_idade)
        with col2:
            menor_idade = df1['Delivery_person_Age'].min()
            st.metric(label='Youngest Courier Age', value=menor_idade)
        with col3:
            melhor = df1['Vehicle_condition'].max()
            st.metric(label='Best vehicle condition', value=melhor)
        with col4:
            pior = df1['Vehicle_condition'].min()
            st.metric(label='Worst Vehicle Condition', value=pior)

#------------------ Middle Tables ------------------
    with st.container():
        st.markdown("""---""")
        col1, col2 = st.columns(2)
        with col1:
            df2 = avg_rating_courier(df1)
            st.markdown('##### Average Rating by Courier')
            st.dataframe(df2, use_container_width=True, hide_index=True)
            
        with col2:
            df2 = avg_rating_traffic(df1)
            st.markdown('##### Average Rating by Traffic Density')
            st.dataframe(df2, use_container_width=True, hide_index=True)
            
            df2 = avg_rating_wc(df1)
            st.markdown('##### Average Rating by Weather Condition')
            st.dataframe(df2, use_container_width=True, hide_index=True)

            

#----------------- Last Tables ---------------------
    with st.container():
        st.markdown("""---""")
        col1, col2 = st.columns(2)
        with col1:
            df_top = top_fastest(df1)
            st.markdown('##### Top Fastest Couries')
            st.dataframe(df_top, use_container_width=True, hide_index=True)
            
        with col2:
            df_top = top_slowest(df1)
            st.markdown('##### Top Slowest Couries')
            st.dataframe(df_top, use_container_width=True, hide_index=True)
            








