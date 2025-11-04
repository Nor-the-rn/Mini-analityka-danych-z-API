import streamlit as st
import pandas as pd
import requests
import altair as alt

st.set_page_config(page_title="Podstawowa analityka danych", layout="wide")
st.title("Podstawowa analityka danych")

@st.cache_data(ttl=3600)
def get_data():
    base = "https://jsonplaceholder.typicode.com"
    users = requests.get(f"{base}/users").json()
    posts = requests.get(f"{base}/posts").json()
    comments = requests.get(f"{base}/comments").json()
    todos = requests.get(f"{base}/todos").json()
    return pd.DataFrame(users), pd.DataFrame(posts), pd.DataFrame(comments), pd.DataFrame(todos)

df_users, df_posts, df_comments, df_todos = get_data()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Użytkownicy", len(df_users))
col2.metric("Zadania", f"{df_todos['completed'].sum()}/{len(df_todos)}")
col3.metric("Posty", len(df_posts))
col4.metric("Komentarze", len(df_comments))

st.markdown("---")

st.header("Statystyka oraz wykresy")

comments_per_post = df_comments.groupby("postId").size()
avg_comments = comments_per_post.mean()
percent_done = df_todos["completed"].mean() * 100

c1, c2, c3 = st.columns(3)
c1.metric("Średnia komentarzy na post", f"{avg_comments:.2f}")
c2.metric("Średni procent wykonanych zadań", f"{percent_done:.1f}%")
c3.metric("Średnia liczba postów na użytkownika", f"{len(df_posts)/len(df_users):.1f}")

st.subheader("Ilość postów na użytkownika")

posts_per_user = (
    df_posts.groupby("userId")
    .size()
    .reset_index(name="Liczba postów")
    .merge(df_users[["id", "name"]], left_on="userId", right_on="id")
)

bar_chart = (
    alt.Chart(posts_per_user)
    .mark_bar(color="#1f77b4")
    .encode(
        x=alt.X("name:N", sort="-y", title="Użytkownik"),
        y=alt.Y("Liczba postów:Q", title="Liczba postów"),
        tooltip=["name", "Liczba postów"]
    )
    .properties(width=700, height=400, title="Liczba postów na użytkownika")
)

st.altair_chart(bar_chart, use_container_width=True)

st.subheader("Procent wykonanych zadań")

todos_summary = (
    df_todos["completed"]
    .value_counts()
    .reset_index()
    .rename(columns={"count": "Liczba"})
)

todos_summary = todos_summary.rename(columns={"completed": "Status_bool"})
todos_summary["Status"] = todos_summary["Status_bool"].map({True: "Wykonane", False: "Niewykonane"})
todos_summary["Procent"] = (todos_summary["Liczba"] / todos_summary["Liczba"].sum()) * 100

color_scale = alt.Scale(
    domain=["Wykonane", "Niewykonane"],
    range=["#1f77b4", "#ff7f0e"]
)

pie_chart = (
    alt.Chart(todos_summary)
    .mark_arc(innerRadius=60)
    .encode(
        theta=alt.Theta("Liczba:Q"),
        color=alt.Color("Status:N", scale=color_scale, legend=alt.Legend(title="Status zadań")),
        tooltip=["Status", "Liczba", alt.Tooltip("Procent:Q", format=".1f")]
    )
    .properties(width=400, height=400, title="Procent wykonanych zadań")
)

st.altair_chart(pie_chart, use_container_width=False)

st.markdown("---")

st.header("Najpopularniejsze:")

comments_per_user = (
    df_posts.merge(df_comments, left_on="id", right_on="postId")
    .groupby("userId")["id_x"]
    .count()
    .reset_index(name="Liczba komentarzy")
    .merge(df_users[["id", "name"]], left_on="userId", right_on="id")[["name", "Liczba komentarzy"]]
)

top_posts = (
    df_comments.groupby("postId").size().reset_index(name="Komentarze")
    .merge(df_posts[["id", "title", "userId"]], left_on="postId", right_on="id")
    .merge(df_users[["id", "name"]], left_on="userId", right_on="id")
    .rename(columns={"name": "Autor", "title": "Tytuł"})
    .sort_values("Komentarze", ascending=False)
    .head(10)
)[["Tytuł", "Autor", "Komentarze"]]

tabA, tabB = st.tabs(["Komentarze na użytkownika", "Najbardziej komentowane posty"])
with tabA:
    st.dataframe(comments_per_user, hide_index=True, use_container_width=True)
with tabB:
    st.dataframe(top_posts, hide_index=True, use_container_width=True)