from datetime import datetime
from io import BytesIO
import pandas as pd
from PIL import Image
from pymysql.err import OperationalError
import requests
import streamlit as st
from sqlalchemy.sql import text

# Streamlit app
st.set_page_config(
    page_title="Generation and Storage Technologies",
    page_icon="sen_icon32.ico",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize connection.
@st.cache_resource
def init_connection():
    try:
        # connect using the connections.mysql parameters from the secrets.toml file
        conn = st.connection('mysql', type='sql', autocommit=True, ttl=60)
    except OperationalError as e:
        st.write("Error connecting to database: {e}")
        exit(1)
    return conn

# Function to fetch data from the database
def fetch_data():
# Fetching data from the MySQL database
    technologies_df = \
        conn.query(f"SELECT * FROM senas316_pmdata.Technologies t" +
            f" LEFT JOIN senas316_pmdata.StorageAttributes s ON t.technology_id = s.technology_id AND t.category = 'storage'" +
            f" LEFT JOIN senas316_pmdata.GeneratorAttributes g ON t.technology_id = g.technology_id AND t.category = 'generator';", ttl=60)
    return technologies_df

conn = st.session_state.conn = init_connection()
conn.reset()
fetch_data()

def main():
    # Path to the SEN logo PNG file
    file_path = 'sen_logo_2.png'

    # Display the PNG file using st.image()
    st.image(file_path, caption='', use_column_width=False)

    st.markdown(
        """
        These are the technologies that are relevent to modelling the decarbonisation of the SWIS.
        """
    )
    # Fetch data from the database and create DataFrame
    data = fetch_data()

    # Allow user to select a technolgy to display
    technology_names = data['technology_name'].unique()
    st.subheader(f"**Select a technology:**")
    selected_technology = st.selectbox("Select a technology:", technology_names, label_visibility = "hidden")

    # Filter data for selected coluumns
    technology_details = data[data['technology_name'] == selected_technology].iloc[0]
    attribute_explain = {
        'capacity': 'The maxiumum storage capacity in mWhs.',
        'capacity_max':'The maximum capacity of the technology.',
        'capacity_min':'The minimum capacity of the technology.',
        'category':'The role it plays in the grid.',
        'capex':'The initial capital expenditure for the technology.',
        'discharge_loss':'The percentage capacity that is lost in discharging.',
        'discharge_max':'The maxiumum percentage of storage capacity that can be discharged..',
        'discount_rate':'The discount rate applied to the technology.',
        'dispatchable':'The technology can be dispatched at any time when required.',
        'emissions':'CO2 emmissions in kg/mWh',
        'fuel': 'The type of fuel consumed by the technology.',
        'FOM':'The fixed operating cost of the technology.',
        'initial': 'The initial value.',
        'lifetime':'The operational lifetime of the technology.',
        'mult':'The capacity multiplier.',
        'order':'The merit order in which the technology is dispatched to meet load.',
        'parasitic_loss':'The percentage of storage capacity lost other than by charging or discharging.',
        'rampdown_max':'The maximum rampdown rate of the technology.',
        'rampup_max':'The maximum rampup rate of the technology.',
        'recharge_loss':'The percentage capacity that is lost in recharging.',
        'recharge_max':'The maximum recharge rate of the technology.',
        'renewable':'Whether the technology can be renewed.',
        'VOM':'The variable operating cost of the technology.',
        'year':'The year of reference.',
        }
    exclude_attributes = [
        'description', 'dispatchable', 'generator_attribute_id', 'image', 'renewable', 'storage_attribute_id', 'technology_name', 'technology_id',
        ]
    if not technology_details.empty:
        # Display technology details
        st.subheader(f"{technology_details.technology_name}")
        if technology_details.image:
            image_url = 'https://sen.asn.au/wp-content/uploads/' + technology_details.image
            image = Image.open(BytesIO(requests.get(image_url).content))
            st.image(image, caption="Technology Image", use_column_width=False)
        else:
            st.warning("No image available for this technology.")
        st.write(f"**Description:** {technology_details.description}")
        col1, col2= st.columns([1, 4])
        for column, value in technology_details.items():
            if (pd.notna(value)):
                with col1:
                    if column not in exclude_attributes:
                        st.write(f"**{column}**: {value}")
                    if (column == 'renewable' or column == 'dispatchable'):
                        st.write(f"**{column}**: {bool(value)}")
                with col2:
                    if (column not in exclude_attributes) or (column == 'renewable' or column == 'dispatchable'):
                        st.markdown(f'<p style="color:blue;">{attribute_explain[column]}</p>', unsafe_allow_html=True)
    else:
        st.warning("Selected technology not found in the database.")

if __name__ == "__main__":
    main()