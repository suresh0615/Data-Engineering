import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

# Connect to SQLite database
conn = sqlite3.connect("../data/IMDB.db")

# Streamlit Page Configuration
st.set_page_config(page_title="Movie Data Analysis", layout="wide")

# Title
st.title("🎬 Movie Data Analysis Dashboard")

# Load production company list for dropdown
try:
    company_list = pd.read_sql("SELECT DISTINCT production_company FROM production_companies WHERE production_company IS NOT NULL", conn)
    company_list = company_list["production_company"].tolist()
    selected_company = st.selectbox("Select a Production Company", company_list)
except Exception as e:
    st.error(f"Error loading production companies: {e}")
    selected_company = None

# Load years for filtering
try:
    year_range = pd.read_sql("SELECT DISTINCT release_year FROM imdb_movies ORDER BY release_year", conn)
    year_range = year_range["release_year"].astype(int)
    selected_year = st.slider("Select Year Range", min_value=int(year_range.min()), max_value=int(year_range.max()), value=(2000, 2026))
except Exception as e:
    st.error(f"Error loading year range: {e}")
    selected_year = (2000, 2026)

# Fetch data based on filters
if selected_company:
    query = f"""
    SELECT im.release_year, 
           pc.production_company, 
           SUM(im.gross_in_million) AS total_revenue,
           SUM(im.budget) AS total_budget,
           SUM(im.gross_in_million - im.budget) AS total_profit,
           SUM(im.budget - im.gross_in_million) AS total_loss,
           COUNT(im.movie_id) AS movie_count
    FROM imdb_movies im
    JOIN production_companies pc ON im.movie_id = pc.movie_id
    WHERE im.gross_in_million IS NOT NULL AND im.budget IS NOT NULL
    AND im.release_year BETWEEN {selected_year[0]} AND {selected_year[1]}
    AND pc.production_company = '{selected_company}'
    GROUP BY im.release_year, pc.production_company
    ORDER BY im.release_year;
    """

    df = pd.read_sql_query(query, conn)

    # Ensure years are continuous in the dataframe
    all_years = pd.DataFrame({"release_year": list(range(selected_year[0], selected_year[1] + 1))})  
    df = all_years.merge(df, on="release_year", how="left").fillna({"total_revenue": 0, "total_profit": 0, "total_loss": 0, "total_budget": 0, "movie_count": 0})

    # 🎭 **Revenue vs. Budget vs. Loss**
    st.markdown("## 🎬 Revenue vs. Budget vs. Loss Over Time")
    fig1 = px.bar(df, 
                  x="release_year", 
                  y=["total_budget", "total_revenue", "total_loss"], 
                  title="Budget vs. Revenue vs. Loss (Grouped Bar Chart)", 
                  barmode="group")
    st.plotly_chart(fig1, use_container_width=True)

    # 📊 **Pie Chart for Loss Analysis**
    st.markdown("## 💸 Loss Analysis")
    fig2 = px.pie(df, 
                  names="release_year", 
                  values="total_loss", 
                  title="Proportion of Loss by Year", 
                  hole=0.4,
                  color_discrete_sequence=px.colors.sequential.Reds)
    fig2.update_traces(textinfo="label+value")
    st.plotly_chart(fig2, use_container_width=True)

    # 🎭 **Scatter Plot: Year vs. Profit/Loss**
    st.markdown("## 📈 Yearly Profit/Loss Analysis")
    fig3 = px.scatter(df, 
                      x="release_year", 
                      y=["total_profit", "total_loss"], 
                      title="Profit vs. Loss Trends",
                      size="movie_count",
                      color="total_profit",
                      color_continuous_scale="RdYlGn")
    st.plotly_chart(fig3, use_container_width=True)

    # 📈 **Line Chart: Trends Over Time**
    st.markdown("## 🎥 Revenue & Budget Trends")
    fig4 = px.line(df, 
                   x="release_year", 
                   y=["total_revenue", "total_budget"], 
                   title="Revenue vs. Budget Over Time",
                   markers=True)
    st.plotly_chart(fig4, use_container_width=True)

    # 📌 **Display Data Table**
    st.markdown("## 📊 Data Table")
    st.dataframe(df)

# Close connection
conn.close()
