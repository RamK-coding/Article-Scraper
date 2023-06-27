import numpy as np
import pandas as pd
import requests
import math
import plotly.express as px
import streamlit as st
import collections
import networkx as nx
from pyvis.network import Network

st.set_page_config(layout="wide", initial_sidebar_state='expanded')
st.title("Scientific-Article Dashboard")
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
    num = st.number_input("How many most cited articles, and latest articles do you want?", value=25, min_value=0)
    date_start = st.text_input("Choose date from which to collect articles in YYYY-MM-DD format", value="2020-01-01")
    search_choice = st.selectbox("Search in", ("Title", "Abstract"))
    graph_gen = st.radio("Generate social network graphs?", ("No", "Yes"))
    graph_path = st.text_input("Enter path to save graph")
    submit = st.form_submit_button("Find articles!")

if submit:
    st.session_state.sc_choice = choice2
    st.session_state.run += 1
    search_unit = search_choice

    def data(cho):
        df = pd.DataFrame(columns=["titles","first-author","authors", "institutes","doi", "publication date", "citations", "journal"])

        if search_unit == "Title":
            url = f"https://api.openalex.org/works?filter=title.search:{cho},type:journal-article,from_publication_date:{date_start}&select=title"
        elif search_unit == "Abstract":
            url = f"https://api.openalex.org/works?filter=abstract.search:{cho},type:journal-article,from_publication_date:{date_start}&select=title"

        c = requests.get(url=url)
        c = c.json()
        count = c["meta"]["count"]

        pages = math.ceil(count / 200)
        for p in range (1, pages+1):

            if search_unit == "Title":
                url_results = f"https://api.openalex.org/works?filter=title.search:{st.session_state.sc_choice},type:journal-article,from_publication_date:{date_start}&page={p}&per-page=200&select=title, publication_date,doi,primary_location,authorships,cited_by_count"
            elif search_unit == "Abstract":
                url_results = f"https://api.openalex.org/works?filter=abstract.search:{st.session_state.sc_choice},type:journal-article,from_publication_date:{date_start}&page={p}&per-page=200&select=title, publication_date,doi,primary_location,authorships,cited_by_count"

            r = requests.get(url=url_results)
            data = r.json()
            for i in range (0, 200):
                try:
                    authors = []
                    institutes = []
                    for a in range(0, len(data["results"][i]["authorships"])):
                        authors.append(data["results"][i]["authorships"][a]["author"]["display_name"])
                        institutes.append(data["results"][i]["authorships"][a]["institutions"][0]["display_name"].split(',')[0])
                    first_author = data["results"][i]["authorships"][0]["author"]["display_name"]
                    df.loc[str(p)+"-"+str(i)] = [data["results"][i]["title"],
                                                 first_author,
                                                 authors,institutes,
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
    df.set_index("titles", inplace=True)
    df = df[["citations", "doi", "authors","institutes","publication date"]]
    st.dataframe(df,use_container_width=True )
    st.download_button(label="Download list", data=df.to_csv().encode('utf-8'),file_name='Most cited publications.csv')
except:
    pass

try:
    st.markdown(f"**:red[Latest {num} publications]**")
    df = st.session_state.articles.copy()
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True, ascending=False)
    df.set_index("titles", inplace=True)
    df = df[["citations","doi", "authors","institutes","publication date"]]
    st.dataframe(df[0:num],use_container_width=True )
    st.download_button(label="Download list", data=df.to_csv().encode('utf-8'),file_name='Latest publications.csv')
except:
    pass

try:
    st.markdown(f"**:red[All publications since {date_start} (sorted by citations)]**")
    df = st.session_state.articles.sort_values("citations", ascending=False).copy()
    df.set_index("titles", inplace=True)
    df = df[["citations", "doi", "authors","institutes", "publication date"]]
    st.dataframe(df,use_container_width=True )
    st.download_button(label="Download list", data=df.to_csv().encode('utf-8'),file_name='Most cited publications.csv')
except:
    pass

def SNA(sna_series, sna_unit):
    nodes = pd.Series()
    for i in range (0, len(sna_series)):
        nodes_byArticle_list = sna_series[i]
        for x in nodes_byArticle_list:
            list_temp=nodes_byArticle_list[:]
            list_temp.remove(x)
            #print(list_temp)
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

    if graph_gen == "Yes":
        net = Network(height="1000px", width="100%", font_color="black")
        net.repulsion()
        net.from_nx(sn)
        net.show_buttons()  # (filter_=['physics'])
        #local_path = f{graph_path}
        path = f"{graph_path}"
        net.save_graph(f'{path}/{st.session_state.sc_choice}_{sna_unit}_graph.html'.replace("--", ""))

#    if graph_type == "Static":
#        fig, ax = plt.subplots(figsize=(50, 50), dpi=600)
#        pos = nx.spring_layout(sn, k=0.15, iterations=20)  # see different layout types here - https://networkx.org/documentation/latest/reference/drawing.html#module-networkx.drawing.layout
#        nx.draw(sn, pos, node_color='r', edge_color='b', with_labels=True, node_size=[v * 100 for v in degree_centrality])
#        st.pyplot(fig)
#        plt.savefig("graph.png", dpi=600)

    #if graph_type == "Interactive":
    #    net = Network(height="1000px", width="100%", font_color="black")
    #    net.repulsion()
    #    net.from_nx(sn)
    #    net.show_buttons()  # (filter_=['physics'])

        # Save and read graph as HTML file (on Streamlit Sharing)
    #    try:
    #        path = '/tmp'
    #        net.save_graph(f'{path}/pyvis_graph.html')
    #        HtmlFile = open(f'{path}/pyvis_graph.html', 'r', encoding='utf-8')

            # Save and read graph as HTML file (locally)
    #    except:
    #        path = r"C:\Users\Ram.Kamath\Desktop\Article-scraper\Article-Scraper"
    #        net.save_graph(f'{path}/pyvis_graph.html')
    #        HtmlFile = open(f'{path}/pyvis_graph.html', 'r', encoding='utf-8')

        # Load HTML file in HTML component for display on Streamlit page
    #    components.html(HtmlFile.read(), height=700)

st.header(":blue[Social Network analysis]")

try:
    sna_authors_series = st.session_state.articles["authors"].copy()
    SNA(sna_authors_series, "authors")
    sna_insti_series = st.session_state.articles["institutes"].copy()
    SNA(sna_insti_series, "institutes")
except:
    pass
