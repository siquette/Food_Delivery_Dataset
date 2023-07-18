import streamlit as st



import pandas as pd
import numpy as np



from haversine import haversine
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


def get_avg_distance( df ):
    cols = ['Delivery_location_latitude', 'Delivery_location_longitude', 'Restaurant_latitude', 'Restaurant_longitude']
    df['distance'] = df.loc[:, cols].apply( lambda x: haversine(  
                                         (x['Restaurant_latitude'], x['Restaurant_longitude'] ),
                                         (x['Delivery_location_latitude'], x['Delivery_location_longitude'])), axis=1 )

    avg_distance = np.round( df['distance'].mean(), 2 )
    return avg_distance


def get_avg_time_by_city( df ):
    df_aux = df.loc[:, ['City', 'Time_taken(min)']].groupby( 'City' ).agg( {'Time_taken(min)': ['mean', 'std']} )
    df_aux.columns = ['avg_time', 'std_time']
    df_aux = df_aux.reset_index()

    fig = go.Figure() 
    fig.add_trace( go.Bar( name='Control',
                           x=df_aux['City'],
                           y=df_aux['avg_time'],
                           error_y=dict( type='data', array=df_aux['std_time'] ) ) ) 

    fig.update_layout(barmode='group') 
    fig.update_layout( margin=dict(l=40, r=40, t=40, b=40) )
    st.plotly_chart( fig, user_container_width=True  )



def get_distribution_distance( df ):
    cols = ['Delivery_location_latitude', 'Delivery_location_longitude', 'Restaurant_latitude', 'Restaurant_longitude']
    df['distance'] = df.loc[:, cols].apply( lambda x:
                                haversine( (x['Restaurant_latitude'], x['Restaurant_longitude']),
                                           (x['Delivery_location_latitude'], x['Delivery_location_longitude']) ), axis=1 )

    df_aux = df.loc[:, ['City', 'distance']].groupby( 'City' ).mean().reset_index()

    # pull is given as a fraction of the pie radius
    fig = go.Figure( data=[ go.Pie( labels=df_aux['City'], values=df_aux['distance'], pull=[0, 0.1, 0])])
    fig.update_layout( margin=dict(l=40, r=40, t=40, b=40) )
    st.plotly_chart( fig, user_container_width=True )


def get_avg_time_by_order( df ):
    df_aux = ( df.loc[:, ['City', 'Time_taken(min)', 'Type_of_order']]
                 .groupby( ['City', 'Type_of_order'] )
                 .agg( {'Time_taken(min)': ['mean', 'std']} ) )

    df_aux.columns = ['avg_time', 'std_time']
    df_aux = df_aux.reset_index()

    st.dataframe( df_aux )


def get_delivery_time_festival( df, festival=True ):
    df_aux = ( df.loc[:, ['Time_taken(min)', 'Festival']]
                 .groupby( 'Festival' )
                 .agg( {'Time_taken(min)': ['mean', 'std']} ) )

    df_aux.columns = ['avg_time', 'std_time']
    df_aux = df_aux.reset_index()

    if festival == True:
        avg_time = np.round( df_aux.loc[df_aux['Festival'] == 'Yes', 'avg_time'], 2 )
        std_time = np.round( df_aux.loc[df_aux['Festival'] == 'Yes', 'std_time'], 2 )
    else:
        avg_time = np.round( df_aux.loc[df_aux['Festival'] == 'No', 'avg_time'], 2 )
        std_time = np.round( df_aux.loc[df_aux['Festival'] == 'No', 'std_time'], 2 )

    return avg_time, std_time


def get_delivery_time_by_city( df ):
    df_aux = ( df.loc[:, ['City', 'Time_taken(min)', 'Road_traffic_density']]
                 .groupby( ['City', 'Road_traffic_density'] )
                 .agg( {'Time_taken(min)': ['mean', 'std']} ) )

    df_aux.columns = ['avg_time', 'std_time']
    df_aux = df_aux.reset_index()

    fig = px.sunburst(df_aux, path=['City', 'Road_traffic_density'], values='avg_time',
                      color='std_time', color_continuous_scale='RdBu',
                      color_continuous_midpoint=np.average(df_aux['std_time'] ) )

    fig.update_layout( margin=dict(l=40, r=40, t=40, b=40) )

    st.plotly_chart( fig, container_width=True )

# ===========================
# Título
# ===========================
st.header("Marketplace - Visão Restaurantes")  ## Main Title

# ===========================
# Filtros - Side bar
# ===========================


st.sidebar.markdown( "# Curry Company" )
st.sidebar.markdown( "## Fastest Delivery in Town" )

st.sidebar.markdown( """---""" )
st.sidebar.markdown( "## Selecione um data limite" )
date_slider = st.sidebar.slider(
        "Até qual valor?",
        value = pd.datetime( 2022, 4, 13 ),
        min_value=pd.datetime( 2022, 2, 11),
        max_value=pd.datetime( 2022, 5, 6 ), 
        format="DD-MM-YYYY"
    )


st.sidebar.markdown( """---""" )
st.sidebar.markdown( "## Selecione uma condição de trânsito" )
traffic_options = st.sidebar.multiselect(
        'Quais a condições do trânsito?', ['Low', 'Medium', 'High', 'Jam'], 
        default=['Low', 'Medium', 'High', 'Low'] )


st.sidebar.markdown( """---""" )
st.sidebar.markdown( "## Selecione uma cidade" )
city_options = st.sidebar.multiselect(
        'Quais a cidade?', ['Metropolitian', 'Semi-Urban', 'Urban'], 
        default=['Urban', 'Semi-Urban', 'Metropolitian'] )
# ===========================
# ETL
# ===========================
# Extracao


# Limpeza
df = clean_code( df )

# Tranformação
df = df.loc[df['Order_Date'] <= date_slider, :]
df = df.loc[df['Road_traffic_density'].isin( traffic_options ), :]
df = df.loc[df['City'].isin( city_options ), :]

# ===========================
# Layout
# ===========================
# Tabs
tab1, tab2 = st.tabs( ['Visão Gerencial', '_'] )


# A maior idade dos entregadomarkdownres
delivery_unique = len( df.loc[:, 'Delivery_person_ID'].unique() )

with tab1:
    with st.container():
        st.title("Overall Metrics")
        col1, col2, col3, col4, col5, col6 = st.columns( 6 )

        # Display Number - 
        col1.metric( "Unique delivery", delivery_unique )
        col2.metric( "Average Distance (KM)", get_avg_distance( df ) )

        avg_time, std_time = get_delivery_time_festival( df, festival=True )
        col3.metric( "Avg Delivery Time Festival", avg_time  )
        col4.metric( "Std Delivery Time Festival", std_time  )

        avg_time, std_time = get_delivery_time_festival( df, festival=False )
        col5.metric( "Avg Delivery Time No Festival", avg_time  )
        col6.metric( "Std Delivery Time No Festival", std_time  )


    with st.container():
        st.markdown("""---""")
        st.title( "Delivery Average Time by City" )
        get_avg_time_by_city( df )
    
    with st.container():
        st.markdown("""---""")
        st.subheader( "Average Time by Order Type" )
        get_avg_time_by_order( df )

    with st.container():
        st.markdown("""---""")
        st.subheader( "Distribuition of Average Time by City" )
        get_distribution_distance( df )

    with st.container():
        st.markdown("""---""")
        st.subheader( "Average Time by City" )
        get_delivery_time_by_city( df )
