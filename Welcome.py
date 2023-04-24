import numpy as np
import pandas as pd
import requests
import math
from datetime import datetime
import plotly.express as px
import streamlit as st
import collections

st.set_page_config(layout="wide", initial_sidebar_state='expanded')
st.title("Scientific-Article scraper (based on a DIPAT component)")
st.caption(":blue[Created by Ram Kamath]")

if "run" not in st.session_state:
    st.session_state.run = 0
if "sc_choice" not in st.session_state:
    st.session_state.sc_choice = ""
if "articles" not in st.session_state:
    st.session_state.articles = pd.DataFrame()
if "article_count" not in st.session_state:
    st.session_state.article_count = pd.DataFrame()
if "cite_count" not in st.session_state:
    st.session_state.cite_count = pd.DataFrame()
if "article_count_comp" not in st.session_state:
    st.session_state.article_count_comp = pd.DataFrame()
if "cum_article" not in st.session_state:
    st.session_state.cum_article = pd.DataFrame()
if "cite_count_comp" not in st.session_state:
    st.session_state.cite_count_comp = pd.DataFrame()
if "cum_cite" not in st.session_state:
    st.session_state.cum_cite = pd.DataFrame()

with st.sidebar.form("Parameters"):
    choice2 = st.text_input("Find articles for:", value="None", placeholder="None")
    num = st.number_input("Get links to these many articles", value=25)
    date_start = st.text_input("Choose date from which to collect articles in YYYY-MM-DD format", value="2020-01-01")
    submit = st.form_submit_button("Find articles!")

if submit:
    st.session_state.sc_choice = choice2
    dict = {f"{st.session_state.sc_choice}": f"{st.session_state.sc_choice}"}
    st.session_state.run += 1

    def data(cho):
        df = pd.DataFrame(columns=["titles","first-author","authors", "doi", "publication date", "citations", "journal"])
        c = requests.get(f"https://api.openalex.org/works?filter=title.search:{dict[cho]},"
                         f"type:journal-article,from_publication_date:{date_start}&select=title")
        c = c.json()
        count = c["meta"]["count"]

        pages = math.ceil(count / 200)
        for p in range (1, pages+1):
            r = requests.get(f"https://api.openalex.org/works?filter=title.search:{dict[st.session_state.sc_choice]},"
                             f"type:journal-article,from_publication_date:{date_start}&page={p}&per-page=200&select=title,"
                             "publication_date,doi,primary_location,authorships,cited_by_count")
            data = r.json()
            for i in range (0, 200):
                try:
                    authors = []
                    for a in range(0, len(data["results"][i]["authorships"])):
                        authors.append(data["results"][i]["authorships"][a]["author"]["display_name"])
                    first_author = data["results"][i]["authorships"][0]["author"]["display_name"]
                    df.loc[str(p)+"-"+str(i)] = [data["results"][i]["title"],
                                                 first_author,
                                                 authors,
                                                 data["results"][i]["doi"],
                                                 data["results"][i]["publication_date"],
                                                 data["results"][i]["cited_by_count"],
                                                 data["results"][i]["primary_location"]["source"]["display_name"]
                                                ]
                except:
                    pass
            p += 1
        return df

    st.session_state.articles = data(st.session_state.sc_choice)
    st.session_state.articles.drop_duplicates(subset='titles',inplace=True)
    st.session_state.articles.set_index(np.arange(0,len(st.session_state.articles)), inplace=True)
    st.session_state.articles.to_csv("Articles.csv")
    st.session_state.article_count = st.session_state.articles.groupby("publication date").count()["titles"]
    st.session_state.cite_count = st.session_state.articles.groupby("publication date").sum()["citations"]

    def date_sort(df):
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
        df.index = df.index.strftime("%b-%Y")
        return df

    st.session_state.article_count = date_sort(st.session_state.article_count)
    st.session_state.cite_count = date_sort(st.session_state.cite_count)

    def comparison(df):
        today = datetime.today()
        start = datetime.strptime(date_start,"%Y-%m-%d")
        index = pd.date_range(start.strftime("%m-%d-%Y"), today.strftime("%m-%d-%Y"), freq='M').strftime("%b-%Y").tolist()
        comp = pd.DataFrame(index=index); comp = pd.concat([df, comp],axis=0)
        comp = comp[~comp.index.duplicated(keep='first')]
        comp.index = pd.to_datetime(comp.index);comp.sort_index(inplace=True);
        comp.index = comp.index.strftime("%b-%Y")
        if st.session_state.run >= 2:
            if comp.index.size > st.session_state.article_count_comp.index.size:
                l = st.session_state.article_count_comp.index.size
                comp = comp.iloc[:l]
            elif comp.index.size < st.session_state.article_count_comp.index.size:
                l = comp.index.size
                st.session_state.article_count_comp = st.session_state.article_count_comp.iloc[:l]
        return comp
    #st.session_state.article_count_comp.index = comp.index
    st.session_state.article_count_comp[f"{st.session_state.sc_choice}".replace("--", "")] = comparison(st.session_state.article_count)
    st.session_state.article_count_comp.fillna(0, inplace=True)
    st.session_state.cum_article[f"{st.session_state.sc_choice}".replace("--", "")] = st.session_state.article_count_comp[f"{st.session_state.sc_choice}".replace("--", "")].cumsum()
    st.session_state.cite_count_comp[f"{st.session_state.sc_choice}".replace("--", "")] = comparison(st.session_state.cite_count)
    st.session_state.cite_count_comp.fillna(0, inplace=True)
    st.session_state.cum_cite[f"{st.session_state.sc_choice}".replace("--", "")] = st.session_state.cite_count_comp[f"{st.session_state.sc_choice}".replace("--", "")].cumsum()

st.subheader(f":blue[Scientific-article trends for {st.session_state.sc_choice}]".replace("--", ""))
fig1, fig2 = st.columns(2)
with fig1:
    try:
        st.markdown("**:red[Article count history]**")
        fig = px.bar(st.session_state.article_count)
        # fig.update_traces(stackgroup=None, fill='tozeroy')
        fig.update_layout(height=500)
        fig.update_xaxes(tickangle=45)
        #fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.7, xanchor="left", x=0.0))
        st.plotly_chart(fig, use_container_width=True)
    except:
        pass

    try:
        st.markdown("**:red[Top 10 published authors]**")
        authors = st.session_state.articles["authors"].sum()
        count = collections.Counter(authors)
        auth_count = pd.Series(count).sort_values(ascending=False)
        fig = px.bar(auth_count[0:10], orientation="h")
        # fig.update_traces(stackgroup=None, fill='tozeroy')
        fig.update_layout(height=500)
        fig.update_xaxes(tickangle=45)
        # fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.7, xanchor="left", x=0.0))
        st.plotly_chart(fig, use_container_width=True)
    except:
        pass

with fig2:
    try:
        st.markdown("**:red[Citation count history]**")
        fig = px.bar(st.session_state.cite_count)
        # fig.update_traces(stackgroup=None, fill='tozeroy')
        fig.update_layout(height=500)
        fig.update_xaxes(tickangle=45)
        #fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.7, xanchor="left", x=0.0))
        st.plotly_chart(fig, use_container_width=True)
    except:
        pass

    try:
        st.markdown("**:red[Top 10 most-cited first-authors]**")
        df = st.session_state.articles.sort_values("citations", ascending=False)[0:10].copy()
        ser = pd.Series(data=df["citations"].values, index=df["first-author"])
        fig = px.bar(ser, orientation="h")
        # fig.update_traces(stackgroup=None, fill='tozeroy')
        fig.update_layout(height=500)
        fig.update_xaxes(tickangle=45)
        # fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.7, xanchor="left", x=0.0))
        st.plotly_chart(fig, use_container_width=True)
    except:
        pass

try:
    st.markdown(f"**:red[Top {num} most-cited publications]**")
    df = st.session_state.articles.sort_values("citations", ascending=False)[0:num].copy()
    df = df[["titles","citations","doi"]]
    df.set_index("titles", inplace=True)
    st.dataframe(df,use_container_width=True )
except:
    pass

try:
    st.markdown(f"**:red[Latest {num} publications]**")
    df = st.session_state.articles.copy()
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True, ascending=False)
    df.set_index("titles", inplace=True)
    df = df[["citations","doi", "publication date"]]
    st.dataframe(df[0:num],use_container_width=True )
except:
    pass

