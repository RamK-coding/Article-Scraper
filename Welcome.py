import numpy as np
import pandas as pd
import requests
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import math
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
import collections
import networkx as nx
import networkx.algorithms.community as nxcom
from pyvis.network import Network
import matplotlib.pyplot as plt
import sys

st.set_page_config(layout="wide", initial_sidebar_state='expanded')
st.title("Scientific-publication metrics Dashboard")
st.caption(":blue[Created by Ram Kamath]")

if "sc_choice" not in st.session_state:
    st.session_state.sc_choice = ""
if "articles" not in st.session_state:
    st.session_state.articles = pd.DataFrame()
if "article_count" not in st.session_state:
    st.session_state.article_count = pd.DataFrame()
if "cite_count" not in st.session_state:
    st.session_state.cite_count = pd.DataFrame()
if "cum_article" not in st.session_state:
    st.session_state.cum_article = pd.DataFrame()
if "cum_cite" not in st.session_state:
    st.session_state.cum_cite = pd.DataFrame()

key_IEEE = st.secrets["key"]

with st.sidebar.form("Parameters"):
    api = st.selectbox("Select API to use:", ("Openalex", "IEEE"))
    choice = st.selectbox("Choose to see trends for:", ( "Multimodal transport",
                                                         "Sustainable Aviation Fuels", "--Power to liquid fuels",
                                                         "Hydrogen aircraft", "Hybrid-Electric aircraft", "UAM", "--eVTOL",
                                                         "The Metaverse","Generative AI"))
    choice2 = st.text_input("Or choose to see trends for (free-choice):", value="None")
    st.info('For IEEE, it is possible to use simple boolean search combinations e.g. (intermodal AND transport), in the free-choice search box. '
            'For Openalex, it is possible to use complex boolean search terms, e.g. (intermodal AND transport) OR (multimodal AND transport), in the free-choice search box.',icon="ℹ️")
    st.info('If using the drop-down menu, please leave the free-choice search box blank, or fill it with "None"', icon="ℹ️")
    search_choice = st.selectbox("Search in", ("Title", "Abstract"))
    OA_choice = st.radio("Search only for open access publications", ("No", "Yes"))
    date_start = st.text_input("For Openalex, choose date from which to collect articles in YYYY-MM-DD format( default is date from 12 months ago)", value=str(date.today() + relativedelta(months=-12)))
    year_start = st.text_input("For IEEE, choose year from which to collect articles in YYYY format( default is the peceding year)", value=str(date.today().year - 1))
    type = st.radio("Find",("All", "Only articles","Only conference papers", "Only book-chapters","Only reports (Only with Openalex)", "Only magazines (Only with IEEE)"))
    # graph_gen = st.radio("Generate social network graphs for authors and institutions?", ("No", "Yes"))
    #name = st.text_input("If you have chosen to generate a network graph, please enter your an identifier (e.g. your name)")
    submit = st.form_submit_button("Get trends!")

if submit:
    st.session_state.articles = pd.DataFrame()
    st.session_state.article_count = pd.DataFrame()
    st.session_state.cite_count = pd.DataFrame()

    # if graph_gen == "Yes":
    #     if st.session_state.id == "":
    #         st.error("Please enter your unique (anonymous) identifier and rerun to be able to generate network graph", icon="🚨")
    #         st.session_state.articles = pd.DataFrame()
    #         st.session_state.article_count = pd.DataFrame()
    #         st.session_state.cite_count = pd.DataFrame()
    #         st.session_state.cum_article = pd.DataFrame()
    #         st.session_state.cum_cite = pd.DataFrame()
    #         sys.exit()

    if choice2 == "None" or choice2 == "":
        dict = {"Multimodal transport": "multimodal AND transport",
                "Sustainable Aviation Fuels": "sustainable aviation fuel",
                "--Power to liquid fuels": "power-to-liquids",
                "Hydrogen aircraft": "hydrogen aircraft",
                "Hybrid-Electric aircraft": "hybrid electric aircraft",
                 "UAM": "urban air mobility",
                "--eVTOL": "eVTOl",
                "The Metaverse": "metaverse",
                "Generative AI": "Generative AI"
                }
        st.session_state.sc_choice = dict[choice]
    elif choice2 != "None":
        st.session_state.sc_choice = choice2

    if api == "Openalex":
        type_dict = {"All": "all",
                     "Only articles":"article",
                     "Only conference papers":"proceedings-article",
                     "Only book-chapters":"book-chapter",
                     "Only reports (Only with Openalex)":"report",
                    }
        type_choice = type_dict[type]

    elif api == "IEEE":
        type_dict = {"All": "all",
                     "Only articles": "Journals",
                     "Only conference papers": "Conferences",
                     "Only book-chapters": "Books",
                     "Only magazines (Only with IEEE)": "Magazines",
                     }
        type_choice = type_dict[type]


    search_unit = search_choice

    if api == "Openalex":
        def data(cho):
            df = pd.DataFrame(columns=["titles", "first-author", "authors", "institutes", "doi", "publication date", "citations",
                                        "journal", "abstract", "concepts","Open access?","type"])

            if search_unit == "Title":
                url = f"https://api.openalex.org/works?filter=title.search:{cho},from_publication_date:{date_start}&select=title"
            elif search_unit == "Abstract":
                url = f"https://api.openalex.org/works?filter=abstract.search:{cho},from_publication_date:{date_start}&select=title"

            c = requests.get(url=url)
            c = c.json()
            count = c["meta"]["count"]

            pages = math.ceil(count / 200)
            for p in range(1, pages + 1):

                if search_unit == "Title":
                    url_results = f"https://api.openalex.org/works?filter=title.search:{cho},from_publication_date:{date_start}&page={p}&per-page=200&select=title,publication_date,doi,primary_location,authorships,cited_by_count,concepts,abstract_inverted_index,open_access,type"
                elif search_unit == "Abstract":
                    url_results = f"https://api.openalex.org/works?filter=abstract.search:{cho},from_publication_date:{date_start}&page={p}&per-page=200&select=title,publication_date,doi,primary_location,authorships,cited_by_count,concepts,abstract_inverted_index,open_access,type"

                r = requests.get(url=url_results)
                data = r.json()
                for i in range(0, 200):
                    try:
                        authors = []
                        institutes = []
                        concepts = []
                        for a in range(0, len(data["results"][i]["authorships"])):
                            authors.append(data["results"][i]["authorships"][a]["author"]["display_name"])
                            institutes.append(data["results"][i]["authorships"][a]["institutions"][0]["display_name"].split(',')[0])
                        first_author = data["results"][i]["authorships"][0]["author"]["display_name"]
                        for con in range(0, len(data["results"][i]["concepts"])):
                            concepts.append(data["results"][i]["concepts"][con]["display_name"])
                        df.loc[str(p) + "-" + str(i)] = [data["results"][i]["title"],
                                                         first_author,
                                                         authors, institutes,
                                                         data["results"][i]["doi"],
                                                         data["results"][i]["publication_date"],
                                                         data["results"][i]["cited_by_count"],
                                                         data["results"][i]["primary_location"]["source"]["display_name"],
                                                         data["results"][i]["abstract_inverted_index"],
                                                         concepts, data["results"][i]["open_access"]["is_oa"],
                                                         data["results"][i]["type"]
                                                         ]
                    except:
                        pass
                p += 1
            return df

        st.session_state.articles = data(st.session_state.sc_choice)
        st.session_state.articles.drop_duplicates(subset='titles', inplace=True)
        if type_choice != "all":
            st.session_state.articles = st.session_state.articles[st.session_state.articles["type"] == type_choice]
        if OA_choice == "Yes":
            st.session_state.articles = st.session_state.articles[st.session_state.articles["Open access?"] == True]
        st.session_state.articles["abstract"] = st.session_state.articles["abstract"].apply(lambda x: list(x.keys()) if x is not None else [])  # getting keys of dictionary (which are the abstract words)

    elif api == "IEEE":
        def data(cho):
            if search_unit == "Title":
                url = f"https://ieeexploreapi.ieee.org/api/v1/search/articles?apikey={key_IEEE}&format=json&max_records=200&start_record=1&sort_order=asc&sort_field=article_number&article_title={cho}&start_year={year_start}"
            elif search_unit == "Abstract":
                url = f"https://ieeexploreapi.ieee.org/api/v1/search/articles?apikey={key_IEEE}&format=json&max_records=200&start_record=1&sort_order=asc&sort_field=article_number&abstract={cho}&start_year={year_start}"

            c = requests.get(url=url)
            c = c.json()
            count = c["total_records"]
            calls = math.ceil(count / 200)

            def data_fill(start_record):
                doi = 0
                df = pd.DataFrame(columns=["titles", "first-author", "authors", "institutes", "doi", "publication date", "citations",
                                            "journal", "abstract", "concepts", "Open access?", "type"])
                if search_unit == "Title":
                    url_results = f"https://ieeexploreapi.ieee.org/api/v1/search/articles?apikey={key_IEEE}&format=json&max_records=200&start_record={start_record}&sort_order=asc&sort_field=article_number&article_title={cho}&start_year={year_start}"
                elif search_unit == "Abstract":
                    url_results = f"https://ieeexploreapi.ieee.org/api/v1/search/articles?apikey={key_IEEE}&format=json&max_records=200&start_record={start_record}&sort_order=asc&sort_field=article_number&abstract={cho}&start_year={year_start}"

                r = requests.get(url=url_results)
                data = r.json()
                for i in range(0, len(data["articles"])):
                    authors = []
                    institutes = []
                    concepts = []
                    try:
                        for a in range(0, len(data["articles"][i]["authors"]["authors"])):
                            authors.append(data["articles"][i]["authors"]["authors"][a]["full_name"])
                    except:
                        pass
                    try:
                        for a in range(0, len(data["articles"][i]["authors"]["authors"])):
                            institutes.append(data["articles"][i]["authors"]["authors"][a]["affiliation"])
                    except:
                        pass
                    try:
                        first_author = data["articles"][i]["authors"]["authors"][0]["full_name"]
                    except:
                        pass
                    try:
                        for con in range(0, len(data["articles"][i]["index_terms"]["ieee_terms"]["terms"])):
                            concepts.append(data["articles"][i]["index_terms"]["ieee_terms"]["terms"][con])
                    except:
                        pass
                    try:
                        title = data["articles"][i]["title"]
                    except:
                        pass
                    try:
                        doi = data["articles"][i]["doi"]
                    except:
                        pass
                    try:
                        publication_date = data["articles"][i]["insert_date"]
                    except:
                        pass
                    try:
                        citations = data["articles"][i]["citing_paper_count"]
                    except:
                        pass
                    try:
                        source = data["articles"][i]["publication_title"]
                    except:
                        pass
                    try:
                        abstract = data["articles"][i]["abstract"]
                    except:
                        pass
                    try:
                        access_type = data["articles"][i]["access_type"]
                    except:
                        pass
                    try:
                        content_type = data["articles"][i]["content_type"]
                    except:
                        pass
                    df.loc[str(start_record+i)] = [title,
                                                   first_author,
                                                   authors,
                                                   institutes,
                                                   doi,
                                                   publication_date,
                                                   citations,
                                                   source,
                                                   abstract,
                                                   concepts,
                                                   access_type,
                                                   content_type
                                                 ]
                return df

            df_articles = pd.DataFrame()

            for x in range (1, calls+1):
                df_temp = pd.DataFrame()
                if x == 1:
                    df_temp = data_fill(1)
                elif x > 1:
                    df_temp = data_fill(200)

                df_articles = pd.concat([df_articles,df_temp])

            return df_articles

        date_start = year_start+"-01-01"

        st.session_state.articles = data(st.session_state.sc_choice)
        st.session_state.articles.drop_duplicates(subset='titles', inplace=True)
        if type_choice != "all":
            st.session_state.articles = st.session_state.articles[st.session_state.articles["type"] == type_choice]
        if OA_choice == "Yes":
            st.session_state.articles = st.session_state.articles[st.session_state.articles["Open access?"] == "Open Access"]
        try:
            st.session_state.articles["publication date"] = pd.to_datetime(st.session_state.articles["publication date"], format="%Y%m%d").dt.date
        except:
            st.error('Unfortunately no results found, please try changing the search term', icon="🚨")
            sys.exit()

    try:
        st.session_state.articles.set_index(np.arange(0,len(st.session_state.articles)), inplace=True)
        st.session_state.articles.to_csv("Articles.csv")
        df = st.session_state.articles.copy()
        if api == "Openalex":
            df["publication date"] = pd.to_datetime(df["publication date"])
        df["publication date"] = df["publication date"].apply(lambda x: x.strftime("%b-%Y"))
        df.set_index("publication date", inplace = True)
        st.session_state.article_count = df.groupby(df.index).count()["titles"]
        st.session_state.cite_count = df.groupby(df.index).sum()["citations"]
    except:
        pass

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
        #comp.to_csv("comparison.csv")

        return comp

    #st.session_state.article_count_comp.index = comp.index
    st.session_state.article_count_comp = comparison(st.session_state.article_count)
    st.session_state.article_count_comp.fillna(0, inplace=True)
    st.session_state.cum_article = st.session_state.article_count_comp.cumsum()
    st.session_state.cite_count_comp = comparison(st.session_state.cite_count)
    st.session_state.cite_count_comp.fillna(0, inplace=True)
    st.session_state.cum_cite = st.session_state.cite_count_comp.cumsum()

    st.subheader(f":blue[Publication trends for {choice}]".replace("--", ""))
    st.info("For IEEE results, the publication date refers to IEEE publication/update date. The IEEE date precedes the publication date in some cases", icon="ℹ️")
    fig1, fig2 = st.columns(2)
    with fig1:
        try:
            st.markdown("**:red[Publication count history]**")
            fig = px.bar(st.session_state.article_count, y="titles")
            # fig.update_traces(stackgroup=None, fill='tozeroy')
            fig.update_layout(height=500,showlegend=False,yaxis_title="Number of titles", xaxis_title="Date")
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
            fig.update_layout(height=500,showlegend=False,yaxis_title="Number of titles", xaxis_title="Authors")
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
            fig.update_layout(height=500,showlegend=False,yaxis_title="Number of citations", xaxis_title="Date")
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
            fig.update_layout(height=500,showlegend=False,yaxis_title="Number of citations", xaxis_title="Authors")
            fig.update_xaxes(tickangle=45)
            # fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.7, xanchor="left", x=0.0))
            st.plotly_chart(fig, use_container_width=True)
        except:
            pass

    try:
        st.markdown("**:red[Top 25 most-cited publications]**")
        df = st.session_state.articles.sort_values("citations", ascending=False)[0:25].copy()
        df = df[["titles","citations","doi","publication date","type"]]
        df.set_index("titles", inplace=True)
        st.dataframe(df,use_container_width=True )
        st.download_button(label="Download data-table", data=df.to_csv().encode('utf-8'),file_name='Most cited publications.csv')
    except:
        pass

    try:
        st.markdown(f"**:red[Latest 25 publications with at least one citation]**")
        df = st.session_state.articles.copy()
        df = df.loc[df["citations"] > 0]
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True, ascending=False)
        df = df[0:25]
        df.sort_values("citations", ascending=False, inplace=True)
        df.set_index("titles", inplace=True)
        df = df[["citations", "doi", "publication date","type"]]
        st.dataframe(df, use_container_width=True)
        st.download_button(label="Download data-table", data=df.to_csv().encode('utf-8'), file_name='Latest publications.csv')
    except:
        pass

    try:
        st.markdown(f"**:red[All publications since {date_start} (sorted by citations)]**")
        df = st.session_state.articles.sort_values("citations", ascending=False).copy()
        df.set_index("titles", inplace=True)
        df = df[["citations", "doi", "authors", "institutes", "publication date", "type"]]
        st.dataframe(df, use_container_width=True)
        st.download_button(label="Download data-table", data=df.to_csv().encode('utf-8'),file_name='All publications.csv')
    except:
        pass

    try:
        st.markdown(f"**:red[Cumulative publication-count]**")
        fig = px.area(st.session_state.cum_article)
        fig.update_traces(stackgroup=None, fill='tozeroy')
        fig.update_layout(height=500,yaxis_title="Number of titles", xaxis_title="Date")
        fig.update_xaxes(tickangle=45)
        #fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.7, xanchor="left", x=0.0))
        st.plotly_chart(fig, use_container_width=True)
    except:
        pass

    try:
        st.markdown("**:red[Cumulative citations]**")
        fig = px.area(st.session_state.cum_cite)
        fig.update_traces(stackgroup=None, fill='tozeroy')
        fig.update_layout(height=500,yaxis_title="Number of citations", xaxis_title="Date")
        fig.update_xaxes(tickangle=45)
        #fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.7, xanchor="left", x=0.0))
        st.plotly_chart(fig, use_container_width=True)
    except:
        pass

    try:
        Articles = st.session_state.articles.copy()
        if api == "IEEE":
            Articles["publication date"] = Articles["publication date"].astype(str)
        Articles["Year"] = Articles["publication date"].str.strip().str[:4]
        concepts_by_year = Articles.groupby("Year")["concepts"].sum()
        concepts_by_year.to_csv("concepts_by_year.csv")
        df = pd.DataFrame()

        for x in concepts_by_year.index:
            lst = concepts_by_year[x]
            count = collections.Counter(lst)
            counter_ser = pd.Series(count)[:10]
            counter = pd.DataFrame(columns=["Year", "Concept", "Value"])
            counter["Year"] = [x] * len(counter_ser)
            counter["Concept"] = counter_ser.index
            counter["Value"] = counter_ser.values
            df = pd.concat([df,counter])
    except:
        pass

    # try:
    st.markdown("**:red[Annual evolution of publishing fields]**")
    fig = px.bar(df, x="Year", y="Value", color="Concept")
    fig.update_layout(height=350)
    fig.update_xaxes(tickangle=45)
    #fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.7, xanchor="left", x=0.0))
    st.plotly_chart(fig, use_container_width=True)
    # except:
    #     pass

    def SNA(sna_series, sna_unit):
        nodes = pd.Series()
        for i in range (0, len(sna_series)):
            nodes_byArticle_list = sna_series[i]
            for x in nodes_byArticle_list:
                list_temp=nodes_byArticle_list[:]
                list_temp.remove(x)
                index = [x] * (len(nodes_byArticle_list) - 1)
                ser = pd.Series(data=list_temp, index=index)
                nodes = pd.concat([nodes,ser])

        df_nodes = pd.DataFrame({"Node1":nodes.index,"Node2":nodes.values})
        df_nodes = df_nodes[df_nodes["Node1"] != df_nodes["Node2"]]
        df_nodes.to_csv("node1 and node2.csv")
        sn = nx.from_pandas_edgelist(df_nodes, source = "Node1", target = "Node2")

        degree_centrality = [sn.degree(n) for n in sn.nodes()]  # list of degrees
        node_list = list(sn.nodes())
        eigenvector_degree_centrality = nx.eigenvector_centrality_numpy(sn).values()
        betweenness_centrality= nx.betweenness_centrality(sn,normalized=True).values()
        nodes_degrees = pd.DataFrame(list(zip(degree_centrality, eigenvector_degree_centrality,betweenness_centrality)),columns=["Degree centrality", "Eigenvector centrality", "Betweenness centrality"],index=node_list)

        fig1, fig2 = st.columns(2)
        with fig1:
            try:
                st.markdown(f"**:red[Top 5 most connected {sna_unit}]**")
                fig = px.bar(nodes_degrees.sort_values(["Degree centrality"], ascending=False)["Degree centrality"][:5])
                # fig.update_traces(stackgroup=None, fill='tozeroy')
                fig.update_layout(height=500)
                fig.update_xaxes(tickangle=45)
                # fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.7, xanchor="left", x=0.0))
                st.plotly_chart(fig, use_container_width=True)
                st.info("These are the authors with the most connections to other authors", icon="ℹ️")
            except:
                pass

        with fig2:
            try:
                st.markdown(f"**:red[Top 5 most 'influential' {sna_unit}]**")
                fig = px.bar(
                    nodes_degrees.sort_values(["Eigenvector centrality"], ascending=False)["Eigenvector centrality"][:5])
                # fig.update_traces(stackgroup=None, fill='tozeroy')
                fig.update_layout(height=500)
                fig.update_xaxes(tickangle=45)
                # fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.7, xanchor="left", x=0.0))
                st.plotly_chart(fig, use_container_width=True)
                st.info("These are the authors with the most connections to other very influential authors", icon="ℹ️")
            except:
                pass

        n_degrees = nodes_degrees.copy()
        n_degrees["Degree centrality"] *= 200
        nodes_degrees_dict = nodes_degrees["Degree centrality"].to_dict()
        nx.set_node_attributes(sn, nodes_degrees_dict, 'size')

        # if graph_gen == "Yes":
        #     net = Network(height="1000px", width="100%", font_color="black")
        #     net.repulsion()
        #     net.from_nx(sn)
        #     net.show_buttons()  # (filter_=['physics'])
        #     path = r"C:\Users\Ram.Kamath\Desktop\DIPAT"
        #     net.save_graph(f'{path}/{st.session_state.id}_{st.session_state.sc_choice}_{sna_unit}_graph.html'.replace("--", ""))

    st.subheader(f":blue[Social Network analysis for {choice}]".replace("--", ""))

    try:
        sna_authors_series = st.session_state.articles["authors"].copy()
        SNA(sna_authors_series, "authors")
        sna_insti_series = st.session_state.articles["institutes"].copy()
        SNA(sna_insti_series, "institutes")
    except:
        pass


