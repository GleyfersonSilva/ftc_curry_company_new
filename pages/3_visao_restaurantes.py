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
import plotly.graph_objects as go

st.set_page_config( page_title ='Restaurants Overview', layout='wide')

## ========================================================================================================================================
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

# Average Delivery Time and Standard Deviation By city
def avg_std_city(df1):
    df2 = df1.loc[:, ['City', 'Time_taken(min)']].groupby(['City']).agg({'Time_taken(min)': ['mean', 'std']})
    df2.columns = ['avg_time', 'std_time']
    df2 = df2.reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar( name='Control', x=df2['City'], y=df2['avg_time'], error_y=dict(type='data', array=df2['std_time'])))
    fig.update_layout(barmode='group')
    return fig

# Average Delivery Time and Standard Deviation by City and Order Type
def avg_std_city_order_type(df1):
    df2 = df1.loc[:, ['City', 'Type_of_order', 'Time_taken(min)']].groupby(['City', 'Type_of_order']).agg({'Time_taken(min)': ['mean', 'std']}).round(2)
    df2.columns = ['avg_time', 'std_time']
    df2 = df2.reset_index()
    return df2

# Average Distance Between Restaurants and Delivery Locations
def avg_distance_pie(df1):
    cols = ['Restaurant_longitude', 'Restaurant_latitude', 'Delivery_location_longitude', 'Delivery_location_latitude']
    df1['Distance'] = df1.loc[:, cols].apply( lambda x: haversine((x['Restaurant_latitude'], x['Restaurant_longitude']), (x['Delivery_location_latitude'], x['Delivery_location_longitude'])), axis=1)  
    avg_distance = df1.loc[:,['City','Distance']].groupby(['City']).mean().round(2).reset_index()
    fig = go.Figure( data=( go.Pie(labels=avg_distance['City'], values=avg_distance['Distance'], pull=[0,0.1,0], marker=dict(colors=px.colors.qualitative.Plotly))))
    #fig.update_layout( legend=dict(x=1,y=1,xanchor='right',yanchor='top'))
    return fig

# Average Delivery Time and Standard Deviation by City and Traffic Type
def avg_std_city_traffic(df1):
    df2 = df1.loc[:, ['City', 'Road_traffic_density', 'Time_taken(min)']].groupby(['City', 'Road_traffic_density']).agg({'Time_taken(min)': ['mean', 'std']}).round(2)
    df2.columns = ['avg_time', 'std_time']
    df2 = df2.reset_index()
    fig = px.sunburst(df2, path=['City','Road_traffic_density'], values='avg_time', color='std_time', color_continuous_scale='RdBu', color_continuous_midpoint=np.average(df2['std_time']))
    return fig

def avg_std_time(df1, operator, festival ):
                df2 = df1.loc[:, ['Festival', 'Time_taken(min)']].groupby(['Festival']).agg({'Time_taken(min)': ['mean', 'std']}).round(2)
                df2.columns = ['avg_time', 'std_time']
                df2 = df2.reset_index()
                value = df2.loc[df2['Festival'] == festival, operator]
                return value



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

st.header('Restaurants Overview')

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

tab1, tab2, tab3 = st.tabs(['Restaurants Overview', '-', '-'])
with tab1:

#----------------------- Cards ----------------------------------
    with st.container():
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:

            deliveries = df1['Delivery_person_ID'].nunique()
            st.metric(label='Unique Couriers', value=deliveries)
        with col2:
            cols = ['Restaurant_longitude', 'Restaurant_latitude', 'Delivery_location_longitude', 'Delivery_location_latitude']
            df1['Distance'] = df1.loc[:, cols].apply( lambda x: haversine((x['Restaurant_latitude'], x['Restaurant_longitude']), (x['Delivery_location_latitude'], x['Delivery_location_longitude'])), axis=1)
            avg_distance = df1['Distance'].mean().round(2)
            st.metric(label='Average Distance', value=avg_distance)
        with col3:

            value = avg_std_time(df1, 'avg_time', 'Yes')
            st.metric(label='Avg. Delivery Time - Festival', value=value)
            
        with col4:
            value = avg_std_time(df1, 'std_time', 'Yes')
            st.metric(label='Std. Dev - Festival', value=value)
        with col5:
            value = avg_std_time(df1, 'avg_time', 'No')
            st.metric(label='Avg. Delivery Time - Non Festival', value=value)
        with col6:
            value = avg_std_time(df1, 'std_time', 'No')
            st.metric(label='Std. Time - Non Festival', value=value)
    
    st.markdown("""---""")
#----------------- Bar and table ---------------------------------
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            fig = avg_std_city(df1)
            st.markdown('##### Average Delivery Time and Standard Deviation by City')
            st.plotly_chart(fig)
            
            
        with col2:
            df2 = avg_std_city_order_type(df1)
            st.markdown('##### Average Delivery Time and Standard Deviation by City and Order Type')
            st.dataframe(df2)

            
#------------------ Pie and Sun Burst ----------------------------------
    st.markdown("""---""")
    with st.container():
        col1, col2 = st.columns(2)
    with col1:
        fig = avg_distance_pie(df1)
        st.markdown('##### Average Distance Between Restaurants and Delivery Locations')
        st.plotly_chart(fig)

    with col2:
        fig = avg_std_city_traffic(df1)
        st.markdown('##### Average Delivery Time and Standard Deviation by City and Traffic Type')
        st.plotly_chart(fig)
