import streamlit as st
import altair as alt
import warnings
warnings.filterwarnings("ignore")
st.set_page_config(layout="wide")
import requests
import pandas as pd
import numpy as np
#import plotly.express as px
import plotly as px
import streamlit as st

from vega_datasets import data


#
# Code to import  the data goes here
# Cache the dataframe so it's only loaded once
@st.experimental_memo
def load_data():
    job_data = pd.read_csv("job_data.csv", sep=";")

    return job_data

@st.experimental_memo
def load_geo():
    polygons = requests.get(
    "https://raw.githubusercontent.com/isellsoap/deutschlandGeoJSON/main/4_kreise/2_hoch.geo.json"
    ).json()
    return polygons

@st.experimental_memo
def load_jobs():
    Jobs = data.iowa_electricity()
    Jobs = Jobs.replace("Fossil Fuels", "Altenpfleger")
    Jobs = Jobs.replace("Nuclear Energy", "Arzt- und Praxishilfe")
    Jobs = Jobs.replace("Renewables", "Human- und Zahnmedizin")
    Jobs = Jobs.rename(columns={"year": "Jahr", "net_generation": "Stellenanzeigen", "source": "job"})
    Jobs["Jahr"] = Jobs['Jahr'] + pd.DateOffset(years=6)
    return Jobs







job_data = load_data()
polygons = load_geo()
Jobs = load_jobs()




# The side bar that contains radio buttons for selection of charts
with st.sidebar:
    st.header('Hier die gewünschte Analyse wählen:')
    job = st.selectbox('Wähle Beruf', ["Altenpflege", "Arzt- und Praxishilfe", "Human- und Zahnmedizin"], 0)
    age = st.slider('Bedeutung von Soft- zu Hardskills?', 0, 100, 50)
    ColorMinMax = st.markdown(''' <style> div.stSlider > div[data-baseweb = "slider"] > div[data-testid="stTickBar"] > div {
        background: rgb(1 1 1 / 0%); } </style>''', unsafe_allow_html=True)

    Slider_Cursor = st.markdown(''' <style> div.stSlider > div[data-baseweb="slider"] > div > div > div[role="slider"]{
        background-color: rgb(14, 38, 74); box-shadow: rgb(14 38 74 / 20%) 0px 0px 0px 0.2rem;} </style>''',
                                unsafe_allow_html=True)

    Slider_Number = st.markdown(''' <style> div.stSlider > div[data-baseweb="slider"] > div > div > div > div
                                    { color: rgb(14, 38, 74); } </style>''', unsafe_allow_html=True)

    col = f''' <style> div.stSlider > div[data-baseweb = "slider"] > div > div {{
        background: linear-gradient(to right, rgb(1, 183, 158) 0%, 
                                    rgb(1, 183, 158) {age}%, 
                                    rgba(151, 166, 195, 0.25) {age}%, 
                                    rgba(151, 166, 195, 0.25) 100%); }} </style>'''

    ColorSlider = st.markdown(col, unsafe_allow_html=True)
    age_faktor = age/100
    #st.write("Softskills: " + str(age) + "%")
    datenbasis = st.checkbox('Zeige Datenbasis')

# The main window

st.title("Ein kleines Dashboard zur Visualisierung einer Kompetenzanalyse")
st.subheader("Die wichtigsten 20 Kompetenzen in der " + job + ":")


with st.container():

    if job == 'Altenpflege':
        source = job_data[job_data["Job"] == "Altenpflege"]
    elif job == 'Arzt- und Praxishilfe':
        source = job_data[job_data["Job"] == "Arzt- und Praxishilfe"]
    else:
        source = job_data[job_data["Job"] == "Human- und Zahnmedizin"]

    source = source[["Kompetenz_Begriff", "Relevanz"]]

    if datenbasis:
        st.dataframe(source, use_container_width=True)
    komp_chart = alt.Chart(source).mark_bar().encode(
           # x='sum(yield):Q',
            x='Relevanz:Q',
           # y=alt.Y('site:N', sort='-x')
            y=alt.Y('Kompetenz_Begriff:N', sort='-x')
        )
    st.altair_chart(komp_chart, use_container_width=True)



    st.subheader("Was ist für die " + job +" wichtiger? Soft- oder Hardskills? Und wo werden die Skills gesucht?")
    # generate some data for each region defined in geojson...
    if job == 'Altenpflege':
        df = pd.DataFrame(
            {"Relevanz": range(1, 434, 1), "rel": np.random.uniform(-0.3+age_faktor, 0+age_faktor, 433)}
        )
    elif job == 'Arzt- und Praxishilfe':
        df = pd.DataFrame(
            {"Relevanz": range(1, 434, 1), "rel": np.random.uniform(-0.7+age_faktor, -0.4+age_faktor, 433)}
        )
    else:
        df = pd.DataFrame(
            {"Relevanz": range(1, 434, 1), "rel": np.random.uniform(-1+age_faktor, -0.6+age_faktor, 433)}
        )


    fig = px.express.choropleth(
        df,
        geojson=polygons,
        locations="Relevanz",
        featureidkey="properties.ID_3",
        color="rel",
        color_continuous_scale="blues",
        range_color=(0, 1),
        # scope="europe",
        labels={"rel": "Relevanz"},
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.update_geos(fitbounds="locations", visible=False)
    # fig.show()
    fig.update_layout(height=800)

    st.plotly_chart(fig, use_container_width=True, height=800)
    st.subheader("Stellenanzeigen je Job im Zeitverlauf")
    alt_chart = alt.Chart(Jobs).mark_area(opacity=0.7).encode(
        x="Jahr:T",
        y=alt.Y("Stellenanzeigen:Q", stack=None),
        color="job:N")
    st.altair_chart(alt_chart, theme=None, use_container_width=True)










