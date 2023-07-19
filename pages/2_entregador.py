import streamlit as st
import plotly.express as px

import pandas as pd
import numpy as np
import folium

import matplotlib.pyplot as plt

from streamlit_folium import folium_static
from PIL import Image

df = pd.read_csv ('https://raw.githubusercontent.com/siquette/Food_Delivery_Dataset/main/metadados/train.csv')

# ===========================
# Function
# ===========================
def clean_code( df ):
    # removing NA
    df = df.loc[(df['Delivery_person_Age'] != 'NaN '), :]
    df = df.loc[(df['City'] != 'NaN '), :]
    df = df.loc[(df['Road_traffic_density'] != 'NaN '), :]
    df = df.loc[(df['Festival'] != 'NaN '), :]
    df = df.loc[(df['multiple_deliveries'] != 'NaN '), :].copy()

    # converting data type
    df['Delivery_person_Ratings'] = df['Delivery_person_Ratings'].astype( float )
    df['Delivery_person_Age']     = df['Delivery_person_Age'].astype( int )
    df['Order_Date']              = pd.to_datetime( df['Order_Date'], format='%d-%m-%Y' )
    df['multiple_deliveries']     = df['multiple_deliveries'].astype( int )

    # removing espacos
    df.loc[:, 'ID'] = df.loc[:, 'ID'].str.strip()
    df.loc[:, 'Road_traffic_density'] = df.loc[:, 'Road_traffic_density'].str.strip()
    df.loc[:, 'Type_of_order'] = df.loc[:, 'Type_of_order'].str.strip()
    df.loc[:, 'Type_of_vehicle'] = df.loc[:, 'Type_of_vehicle'].str.strip()
    df.loc[:, 'City'] = df.loc[:, 'City'].str.strip()
    df.loc[:, 'Festival'] = df.loc[:, 'Festival'].str.strip()

    # cleaning coluna time taken
    df['Time_taken(min)'] = df['Time_taken(min)'].apply( lambda x: x.split( '(min) ')[1] )
    df['Time_taken(min)'] = df['Time_taken(min)'].astype( int )

    df['week_of_year'] = df['Order_Date'].dt.strftime( "%U" )

    return df


def get_avg_rating_by_traffic( df ):
    df_aux = ( df.loc[:, ['Delivery_person_Ratings', 'Road_traffic_density']]
                 .groupby( 'Road_traffic_density')
                 .agg( {'Delivery_person_Ratings': ['mean', 'std' ]} ) )

    # mudanca de nome das colunas
    df_aux.columns = ['delivery_mean', 'delivery_std']

    # reset do index
    df_aux = df_aux.reset_index()

    return df_aux

def get_avg_rating_by_weather( df ):
    df_aux = ( df.loc[:, ['Delivery_person_Ratings', 'Weatherconditions']]
                 .groupby( 'Weatherconditions' )
                 .agg( {'Delivery_person_Ratings': ['mean', 'std']} ) )

    # mudanca de nome das colunas
    df_aux.columns = ['delivery_mean', 'delivery_std']

    # reset do index
    df_aux = df_aux.reset_index()

    return df_aux


def get_faster_delivery( df ):
    df = ( df.loc[:, ['Delivery_person_ID', 'City', 'Time_taken(min)']]
             .groupby( ['City', 'Delivery_person_ID'] )
             .mean()
             .sort_values( ['City', 'Time_taken(min)'], ascending=True )
             .reset_index() )

    df_aux01 = df.loc[df['City'] == 'Metropolitian', :].head(10)
    df_aux02 = df.loc[df['City'] == 'Urban', :].head(10)
    df_aux03 = df.loc[df['City'] == 'Semi-Urban', :].head(10)

    df3 = pd.concat( [df_aux01, df_aux02, df_aux03] ).reset_index( drop=True )

    return df3

def get_slower_delivery( df ):
    df = ( df.loc[:, ['Delivery_person_ID', 'City', 'Time_taken(min)']]
             .groupby( ['City', 'Delivery_person_ID'] )
             .mean()
             .sort_values( ['City', 'Time_taken(min)'], ascending=False )
             .reset_index() )

    df_aux01 = df.loc[df['City'] == 'Metropolitian', :].head(10)
    df_aux02 = df.loc[df['City'] == 'Urban', :].head(10)
    df_aux03 = df.loc[df['City'] == 'Semi-Urban', :].head(10)

    df3 = pd.concat( [df_aux01, df_aux02, df_aux03] ).reset_index( drop=True )

    return df3


# ===========================
# Título
# ===========================
st.header("Marketplace - Visão Entregadores")  ## Main Title

# ===========================
# Filtros - Side bar
# ===========================


st.sidebar.markdown( "# Curry Company" )
st.sidebar.markdown( "## Fastest Delivery in Town" )
st.sidebar.markdown( """---""" )

st.sidebar.markdown( "## Selecione um data limite" )
date_slider = st.sidebar.slider(
        "Até qual valor?",
        value=pd.datetime( 2022, 4, 13 ),
        min_value=pd.datetime( 2022, 2, 11),
        max_value=pd.datetime( 2022, 5, 6 ), 
        format="DD-MM-YYYY"
    )
st.sidebar.markdown( """---""" )

st.sidebar.markdown( "## Selecione uma condição de trânsito" )
traffic_options = st.sidebar.multiselect(
        'Quais a condições do trânsito?',
        ['Low', 'Medium', 'High', 'Jam'], default='Medium' )
# ===========================
# ETL
# ===========================



# Limpeza
df = clean_code( df )

# Tranformação
df = df.loc[df['Order_Date'] <= date_slider, :]
df = df.loc[df['Road_traffic_density'].isin( traffic_options ), :]

# ===========================
# Título
# ===========================
#st.set_page_config(layout="wide")
st.markdown("# Marketplace - Entregadores")

# ===========================
# Layout
# ===========================
# Tabs
tab1, tab2 = st.tabs( ['Visão Gerencial', '_'] )


# A maior idade dos entregadores
older_age = df.loc[:, 'Delivery_person_Age'].max()
younger_age = df.loc[:, 'Delivery_person_Age'].min()

# A melhor e a pior condicao
best_vehicle  = df.loc[:, 'Vehicle_condition'].max()
worst_vehicle = df.loc[:, 'Vehicle_condition'].min()

# Avaliacao media por entregador
df_avg_ratings_per_deliver = ( df.loc[:, ['Delivery_person_Ratings', 'Delivery_person_ID']]
                                 .groupby( 'Delivery_person_ID' )
                                 .mean()
                                 .reset_index() )
with tab1:

    with st.container():
        st.title("Overall Metrics")
        col1, col2, col3, col4 = st.columns( 4, gap="large" )
        # Display Number - 
        col1.metric("Older Delivery Age", older_age )
        col2.metric("Younger Delivery Age", younger_age )
        
        col3.metric("Best Vehicle Condition", best_vehicle )
        col4.metric("Worst Vehicle Condition", worst_vehicle )

    with st.container():
        st.markdown("""---""")
        st.title("Ratings")

        col1, col2 = st.columns( 2 )

        with col1:
            st.subheader( "Average Ratings per Deliver" )
            st.dataframe( df_avg_ratings_per_deliver )

        with col2:
            st.subheader( "Average Ratings per Traffic" )
            st.dataframe( get_avg_rating_by_traffic( df ) )

            st.subheader( "Average Ratings per Weather" )
            st.dataframe( get_avg_rating_by_weather( df ) )

    with st.container():
        st.markdown("""---""")
        st.title( 'Speed of Delivery' )

        col1, col2 = st.columns( 2 )

        with col1:
            st.subheader( 'Faster Delivery by City' )
            st.dataframe( get_faster_delivery( df ) )

        with col2:
            st.subheader( 'Faster Delivery by City' )
            st.dataframe( get_slower_delivery( df ) )