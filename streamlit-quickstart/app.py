import streamlit as st

st.set_page_config(page_title= "Review Data Framework ver.1.0")

st.title("Review Data Framework")
st.caption("EDA Dashboard")

import pandas as pd

up = st.file_uploader("CSV file upload", type=['csv'])