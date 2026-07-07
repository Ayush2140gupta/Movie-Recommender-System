import streamlit as st
import pickle
import pandas as pd
import requests

# ---------------- PAGE CONFIG ---------------- #

st.set_page_config(
    page_title="Netflix Movie Recommender",
    layout="wide"
)

# ---------------- API KEY ---------------- #

API_KEY = "a357fce11f533b32b7f6bcfa2c6f1bb7"

# ---------------- FETCH POSTER ---------------- #

def fetch_poster(movie_id):

    response = requests.get(
        f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US'
    )

    data = response.json()

    poster_path = data.get('poster_path')

    if poster_path:
        return "https://image.tmdb.org/t/p/w500/" + poster_path

    return ""


# ---------------- FETCH BACKDROP ---------------- #

def fetch_backdrop(movie_id):

    response = requests.get(
        f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US'
    )

    data = response.json()

    backdrop_path = data.get('backdrop_path')

    if backdrop_path:
        return "https://image.tmdb.org/t/p/original/" + backdrop_path

    return ""


# ---------------- FETCH TRAILER ---------------- #

def fetch_trailer(movie_id):

    url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={API_KEY}&language=en-US"

    data = requests.get(url).json()

    for video in data.get("results", []):
        if video["type"] == "Trailer":
            return f"https://www.youtube.com/watch?v={video['key']}"

    return None


# ---------------- FETCH MOVIE DETAILS ---------------- #

def fetch_movie_details(movie_id):

    # Movie details
    details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"

    data = requests.get(details_url).json()

    # Credits
    credits_url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={API_KEY}&language=en-US"

    credits_data = requests.get(credits_url).json()

    director = "Not Available"
    producer = "Not Available"

    for crew in credits_data.get('crew', []):

        if crew['job'] == 'Director':
            director = crew['name']

        if crew['job'] == 'Producer':
            producer = crew['name']

    cast = []

    for actor in credits_data.get('cast', [])[:5]:
        cast.append(actor['name'])

    details = {

        "title": data.get("title"),

        "overview": data.get("overview"),

        "rating": data.get("vote_average"),

        "release_date": data.get("release_date"),

        "runtime": data.get("runtime"),

        "genres": [genre['name'] for genre in data.get("genres", [])],

        "director": director,

        "producer": producer,

        "language": data.get("original_language"),

        "budget": data.get("budget"),

        "revenue": data.get("revenue"),

        "tagline": data.get("tagline"),

        "cast": cast,

        "poster": "https://image.tmdb.org/t/p/w500/" + data.get("poster_path")

    }

    return details


# ---------------- RECOMMEND FUNCTION ---------------- #

def recommend(movie):

    movie_index = movies[movies['title'] == movie].index[0]

    distances = similarity[movie_index]

    movies_list = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x: x[1]
    )[1:6]

    recommended_movies = []
    recommended_posters = []

    for i in movies_list:

        movie_id = movies.iloc[i[0]].movie_id

        recommended_movies.append(
            movies.iloc[i[0]].title
        )

        recommended_posters.append(
            fetch_poster(movie_id)
        )

    return recommended_movies, recommended_posters


# ---------------- LOAD DATA ---------------- #

movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))

movies = pd.DataFrame(movies_dict)

similarity = pickle.load(open('similarity_compressed.pkl', 'rb'))

# ---------------- SIDEBAR ---------------- #

st.sidebar.title("🎥 About")

st.sidebar.write("""
Netflix Style Movie Recommendation System
built using:
- Machine Learning
- Streamlit
- TMDB API
""")

# ---------------- TITLE ---------------- #

st.markdown(
    "<h1 style='text-align:center; color:#E50914;'>🎬 Netflix Movie Recommender</h1>",
    unsafe_allow_html=True
)

# ---------------- SEARCH MOVIE ---------------- #

selected_movie_name = st.selectbox(
    '🎥 Search Movie',
    movies['title'].values
)

# ---------------- SELECTED MOVIE ID ---------------- #

selected_movie_id = movies[
    movies['title'] == selected_movie_name
].iloc[0].movie_id

# ---------------- BACKGROUND ---------------- #

background_image = fetch_backdrop(selected_movie_id)

# ---------------- CUSTOM CSS ---------------- #

st.markdown(f"""
<style>

[data-testid="stAppViewContainer"] {{

    background-image:
    linear-gradient(
        rgba(0,0,0,0.75),
        rgba(0,0,0,0.95)
    ),
    url("{background_image}");

    background-size: cover;
    background-position: center;
    background-attachment: fixed;

}}

.main {{
    background-color: rgba(0,0,0,0);
    color: white;
}}

h1 {{
    color: #E50914;
    text-align: center;
    font-size: 55px;
}}

.stButton>button {{

    background-color: #E50914;
    color: white;
    border-radius: 10px;
    height: 3em;
    width: 100%;
    font-size: 18px;
    border: none;

}}

.stButton>button:hover {{

    background-color: #ff1f1f;
    color: white;

}}

div[data-baseweb="select"] > div {{

    background-color: #262730;
    color: white;

}}

</style>
""", unsafe_allow_html=True)

# ---------------- BUTTON ---------------- #

if st.button('🍿 Recommend Movies'):

    with st.spinner('Loading movie details... 🍿'):

        # Movie details
        movie_details = fetch_movie_details(selected_movie_id)

        # Recommendations
        names, posters = recommend(selected_movie_name)

        # Trailer
        trailer = fetch_trailer(selected_movie_id)

    st.markdown("---")

    # ---------------- MOVIE DETAILS ---------------- #

    col1, col2 = st.columns([1, 2])

    with col1:

        st.image(movie_details['poster'])

    with col2:

        st.markdown(f"# {movie_details['title']}")

        st.markdown(f"⭐ IMDB Rating: {movie_details['rating']}")

        st.markdown(f"🎬 Director: {movie_details['director']}")

        st.markdown(f"🎥 Producer: {movie_details['producer']}")

        st.markdown(f"📅 Release Date: {movie_details['release_date']}")

        st.markdown(f"⏳ Runtime: {movie_details['runtime']} minutes")

        st.markdown(
            f"🎭 Genres: {', '.join(movie_details['genres'])}"
        )

        st.markdown(
            f"🗣 Language: {movie_details['language'].upper()}"
        )

        st.markdown(
            f"💰 Budget: ${movie_details['budget']:,}"
        )

        st.markdown(
            f"💵 Revenue: ${movie_details['revenue']:,}"
        )

        st.markdown(
            f"🎞 Tagline: *{movie_details['tagline']}*"
        )

        st.markdown(
            f"🎭 Cast: {', '.join(movie_details['cast'])}"
        )

        st.markdown("### Overview")

        st.write(movie_details['overview'])

        # Trailer Button
        if trailer:

            st.markdown(
                f"[▶️ Watch Trailer]({trailer})"
            )

    st.markdown("---")

    st.subheader(
        f"Movies similar to {selected_movie_name}"
    )

    # ---------------- RECOMMENDATIONS ---------------- #

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.image(posters[0], use_container_width=True)
        st.markdown(f"### {names[0]}")

    with col2:
        st.image(posters[1], use_container_width=True)
        st.markdown(f"### {names[1]}")

    with col3:
        st.image(posters[2], use_container_width=True)
        st.markdown(f"### {names[2]}")

    with col4:
        st.image(posters[3], use_container_width=True)
        st.markdown(f"### {names[3]}")

    with col5:
        st.image(posters[4], use_container_width=True)
        st.markdown(f"### {names[4]}")