import streamlit as st
import altair as alt
import warnings
warnings.filterwarnings("ignore")
st.set_page_config(layout="wide")
import requests
import pandas as pd
import numpy as np
import plotly.express as pxe
import plotly as px
import streamlit as st

from vega_datasets import data


#
# Code to import  the data goes here
# Cache the dataframe so it's only loaded once
@st.cache_data
def load_data():
    job_data = pd.read_csv("job_data.csv", sep=";")

    return job_data

@st.cache_data
def load_geo():
    polygons = requests.get(
    "https://raw.githubusercontent.com/isellsoap/deutschlandGeoJSON/main/4_kreise/2_hoch.geo.json"
    ).json()
    return polygons

@st.cache_data
def load_jobs():
    Jobs = data.iowa_electricity()
    Jobs = Jobs.replace("Fossil Fuels", "Altenpfleger")
    Jobs = Jobs.replace("Nuclear Energy", "Arzt- und Praxishilfe")
    Jobs = Jobs.replace("Renewables", "Human- und Zahnmedizin")
    Jobs = Jobs.rename(columns={"year": "Jahr", "net_generation": "Stellenanzeigen", "source": "job"})
    Jobs["Jahr"] = Jobs['Jahr'] + pd.DateOffset(years=6)
    return Jobs

@st.cache_data
def load_data_isco_komp_data():
    isco_komp_data = pd.read_csv("isco_komp_data.csv", sep=";")

    return isco_komp_data


def create_chart(df, beruf):
    import matplotlib.pyplot as plt
    import numpy as np
    df = df[df["Beruf"]==beruf]
    import pandas as pd
    # Ensures reproducibility of random numbers
    #rng = np.random.default_rng(123)

    def get_label_rotation(angle, offset):
        # Rotation must be specified in degrees :(
        rotation = np.rad2deg(angle + offset)
        if angle <= np.pi:
            alignment = "right"
            rotation = rotation + 180
        else:
            alignment = "left"
        return rotation, alignment

    def add_labels(angles, values, labels, offset, ax):
        # This is the space between the end of the bar and the label
        padding = 4

        # Iterate over angles, values, and labels, to add all of them.
        for angle, value, label, in zip(angles, values, labels):
            angle = angle

            # Obtain text rotation and alignment
            rotation, alignment = get_label_rotation(angle, offset)

            # And finally add the text
            ax.text(
                x=angle,
                y=value + padding,
                s=label,
                ha=alignment,
                va="center",
                rotation=rotation,
                rotation_mode="anchor",
                fontsize = 18
            )

    ###check
    OFFSET = np.pi / 2

    # All this part is like the code above
    GROUPS_SIZE = df['Kompetenz'].value_counts().tolist()
    df = df.groupby('Kompetenz').apply(lambda x: x.sort_values(by='Kompetenz_Begriff')).reset_index(drop=True)
    df = df.assign(freq=df.groupby('Kompetenz')['Kompetenz'].transform('count')) \
        .sort_values(by=['freq', 'Kompetenz'], ascending=[False, True])


    VALUES = df["Relevanz"].values
    LABELS = df["Kompetenz_Begriff"].values
    GROUP = df["Kompetenz"].values
    KOMPETENZ = df["Kompetenz"].unique().tolist()
    if beruf == "Rank_Total 825_Medizin-_Orthopädie- und Rehatechnik":
        beruf = "Rank_Total 825_Medizin- Orthopädie- und Rehatechnik"
    if beruf == "Rank_Total 816_Psychologie_nichtärztl. Psychotherapie":
        beruf = "_816_Psychologie, nichtärztl. Psychotherapie"
    if beruf == "Rank_Total 813_Gesundh._Krankenpfl._Rettungsd.Geburtsh.":
        beruf = "_813_Gesundh., Krankenpfl., Rettungsd., Geburtsh."
    beruf = beruf.split("_")[2]
    beruf = beruf.replace(" ", "\n")

    PAD = 3
    ANGLES_N = len(VALUES) + PAD * len(np.unique(GROUP))
    ANGLES = np.linspace(0, 2 * np.pi, num=ANGLES_N, endpoint=False)
    WIDTH = (2 * np.pi) / len(ANGLES)

    offset = 0
    IDXS = []

    for size in GROUPS_SIZE:
        IDXS += list(range(offset + PAD, offset + size + PAD))
        offset += size + PAD

    fig, ax = plt.subplots(figsize=(18, 25), subplot_kw={"projection": "polar"})
    ax.set_theta_offset(OFFSET)
    ax.set_ylim(-30, 100)
    ax.set_frame_on(False)
    ax.xaxis.grid(False)
    ax.yaxis.grid(False)
    ax.set_xticks([])
    ax.set_yticks([])

    #COLORS = [f"C{i}" for i, size in enumerate(GROUPS_SIZE) for _ in range(size)]
    index_ueberfachlich = KOMPETENZ.index("überfachlich")
    COLORS = []
    color_ueberfachlich = '#CC3A45'
    colors_fachlich = ["#003663", "#3A8FEC", "#CDDEF2"]
    colors_fachlich.insert(index_ueberfachlich, color_ueberfachlich)
    for i, size in enumerate(GROUPS_SIZE):
        if i == index_ueberfachlich:
            COLORS.extend([color_ueberfachlich for _ in range(size)])
        else:
            COLORS.extend([colors_fachlich[i] for _ in range(size)])


    ax.bar(
        ANGLES[IDXS], VALUES, width=WIDTH, color=COLORS,
        edgecolor="white", linewidth=2, label=GROUP
    )

    add_labels(ANGLES[IDXS], VALUES, LABELS, OFFSET, ax)

    import matplotlib.patches as mpatches
    handle_list = []
    for i in range(len(GROUPS_SIZE)):
        handle_list.append(mpatches.Patch(color=colors_fachlich[i], label="fachlich: "+KOMPETENZ[i] if i != index_ueberfachlich else KOMPETENZ[i]))

    fig.legend(handles=handle_list, loc='lower left', bbox_to_anchor=(1, 0.2), title='Kompetenz', fontsize=18, title_fontsize='20', fancybox=True, edgecolor="#333333")
    # fig.legend(handles=[komp1, komp2, komp3, komp4], loc='lower right', title='Kompetenz')

    # Extra customization below here --------------------

    # This iterates over the sizes of the groups adding reference
    # lines and annotations.

    offset = 0
    for group, size in zip(["A", "B", "C", "D"], GROUPS_SIZE):
        # Add line below bars
        x1 = np.linspace(ANGLES[offset + PAD], ANGLES[offset + size + PAD - 1], num=25)
        ax.plot(x1, [-5] * 25, color="#333333")

        # Add text to indicate group
        # ax.text(
        #     np.mean(x1), -20, group, color="#333333", fontsize=14,
        #     fontweight="bold", ha="center", va="center"
        # )

        # Add reference lines at 20, 40, 60, and 80
        x2 = np.linspace(ANGLES[offset], ANGLES[offset + PAD - 1], num=25)
        ax.plot(x2, [20] * 25, color="#bebebe", lw=0.8)
        ax.plot(x2, [40] * 25, color="#bebebe", lw=0.8)
        ax.plot(x2, [60] * 25, color="#bebebe", lw=0.8)
        ax.plot(x2, [80] * 25, color="#bebebe", lw=0.8)

        offset += size + PAD

    plt.text(0.5, 0.5, beruf, horizontalalignment='center', color="#333333", fontsize=20, fontweight="bold",
             verticalalignment='center', transform=ax.transAxes)

    #plt.tight_layout()
    #plt.show()
    return fig









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


    fig = pxe.choropleth(
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
    
    fig = create_chart(load_data_isco_komp_data(), "Rank_Total 825_Medizin-_Orthopädie- und Rehatechnik")
    st.pyplot(fig)


############test


with st.container():
    create_chart(load_data_isco_komp_data(), "Rank_Total 825_Medizin-_Orthopädie- und Rehatechnik")

