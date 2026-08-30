import streamlit as st
import pickle
import pandas as pd
import requests

import auth

# ---------------- PAGE CONFIG ---------------- #

st.set_page_config(
    page_title="Netflix Movie Recommender",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- API KEY ---------------- #

from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("API_KEY")

# ---------------- INIT AUTH DB ---------------- #

auth.init_db()

# ---------------- SESSION STATE DEFAULTS ---------------- #

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = None

# ---------------- GLOBAL / MOBILE-FRIENDLY CSS ---------------- #
# Applied on every page (auth screen + main app) so it works before login too.

st.markdown("""
<style>

/* Make the main content area comfortable on small screens */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    padding-left: 1rem;
    padding-right: 1rem;
    max-width: 1100px;
}

/* Buttons */
.stButton>button {
    background-color: #E50914;
    color: white;
    border-radius: 10px;
    height: 3em;
    width: 100%;
    font-size: 18px;
    border: none;
}

.stButton>button:hover {
    background-color: #ff1f1f;
    color: white;
}

div[data-baseweb="select"] > div {
    background-color: #262730;
    color: white;
}

/* --- Responsive poster grid (used instead of st.columns for recommendations) --- */
.poster-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 16px;
    margin-top: 10px;
}

.poster-card {
    text-align: center;
}

.poster-card img {
    width: 100%;
    border-radius: 10px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
}

.poster-card p {
    margin-top: 8px;
    font-size: 15px;
    font-weight: 600;
    color: white;
}

/* --- Mobile breakpoint --- */
@media (max-width: 768px) {

    h1 {
        font-size: 32px !important;
    }

    /* Poster grid: 2 columns on phones instead of 5 */
    .poster-grid {
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
    }

    /* Stack the movie-detail poster + info columns vertically on phones */
    div[data-testid="stHorizontalBlock"] {
        flex-direction: column;
    }

    div[data-testid="stHorizontalBlock"] > div {
        width: 100% !important;
    }

    .block-container {
        padding-left: 0.6rem;
        padding-right: 0.6rem;
    }
}

@media (max-width: 480px) {
    .poster-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

</style>
""", unsafe_allow_html=True)


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

    details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
    data = requests.get(details_url).json()

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

    poster_path = data.get("poster_path")

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
        "poster": ("https://image.tmdb.org/t/p/w500/" + poster_path) if poster_path else ""
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

        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_posters.append(fetch_poster(movie_id))

    return recommended_movies, recommended_posters


# =========================================================
#                     AUTH SCREEN
# =========================================================

def show_auth_screen():

    st.markdown(
        "<h1 style='text-align:center; color:#E50914;'>🎬 Netflix Movie Recommender</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align:center; color:#bbb;'>Log in or create an account to continue</p>",
        unsafe_allow_html=True
    )

    left, mid, right = st.columns([1, 2, 1])

    with mid:

        login_tab, signup_tab = st.tabs(["🔑 Login", "📝 Sign Up"])

        # ---------------- LOGIN ---------------- #
        with login_tab:

            with st.form("login_form"):

                login_username = st.text_input("Username", key="login_username")
                login_password = st.text_input("Password", type="password", key="login_password")

                login_submitted = st.form_submit_button("Log In")

                if login_submitted:

                    if auth.verify_user(login_username, login_password):
                        st.session_state.logged_in = True
                        st.session_state.username = login_username.strip()
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")

        # ---------------- SIGN UP ---------------- #
        with signup_tab:

            with st.form("signup_form"):

                new_username = st.text_input("Choose a username", key="signup_username")
                new_password = st.text_input("Choose a password", type="password", key="signup_password")
                confirm_password = st.text_input("Confirm password", type="password", key="signup_confirm")

                signup_submitted = st.form_submit_button("Create Account")

                if signup_submitted:

                    if new_password != confirm_password:
                        st.error("Passwords do not match.")
                    else:
                        success, message = auth.create_user(new_username, new_password)

                        if success:
                            st.success(message + " Switch to the Login tab.")
                        else:
                            st.error(message)


# =========================================================
#                     MAIN APP
# =========================================================

def show_main_app():

    # ---------------- LOAD DATA ---------------- #

    movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
    global movies, similarity

    movies = pd.DataFrame(movies_dict)
    similarity = pickle.load(open('similarity_compressed.pkl', 'rb'))

    # ---------------- SIDEBAR ---------------- #

    st.sidebar.title("🎥 About")
    st.sidebar.write(f"Logged in as **{st.session_state.username}**")

    st.sidebar.write("""
    Netflix Style Movie Recommendation System
    built using:
    - Machine Learning
    - Streamlit
    - TMDB API
    """)

    if st.sidebar.button("🚪 Log Out"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()

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

    selected_movie_id = movies[
        movies['title'] == selected_movie_name
    ].iloc[0].movie_id

    # ---------------- BACKGROUND ---------------- #

    background_image = fetch_backdrop(selected_movie_id)

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
    </style>
    """, unsafe_allow_html=True)

    # ---------------- BUTTON ---------------- #

    if st.button('🍿 Recommend Movies'):

        with st.spinner('Loading movie details... 🍿'):

            movie_details = fetch_movie_details(selected_movie_id)
            names, posters = recommend(selected_movie_name)
            trailer = fetch_trailer(selected_movie_id)

        st.markdown("---")

        # ---------------- MOVIE DETAILS ---------------- #

        col1, col2 = st.columns([1, 2])

        with col1:
            if movie_details['poster']:
                st.image(movie_details['poster'], use_container_width=True)

        with col2:
            st.markdown(f"# {movie_details['title']}")
            st.markdown(f"⭐ IMDB Rating: {movie_details['rating']}")
            st.markdown(f"🎬 Director: {movie_details['director']}")
            st.markdown(f"🎥 Producer: {movie_details['producer']}")
            st.markdown(f"📅 Release Date: {movie_details['release_date']}")
            st.markdown(f"⏳ Runtime: {movie_details['runtime']} minutes")
            st.markdown(f"🎭 Genres: {', '.join(movie_details['genres'])}")
            st.markdown(f"🗣 Language: {movie_details['language'].upper()}")
            st.markdown(f"💰 Budget: ${movie_details['budget']:,}")
            st.markdown(f"💵 Revenue: ${movie_details['revenue']:,}")
            st.markdown(f"🎞 Tagline: *{movie_details['tagline']}*")
            st.markdown(f"🎭 Cast: {', '.join(movie_details['cast'])}")

            st.markdown("### Overview")
            st.write(movie_details['overview'])

            if trailer:
                st.markdown(f"[▶️ Watch Trailer]({trailer})")

        st.markdown("---")
        st.subheader(f"Movies similar to {selected_movie_name}")

        # ---------------- RECOMMENDATIONS (responsive CSS grid) ---------------- #
        # Using a raw HTML/CSS grid instead of st.columns so it reflows
        # from 5 -> 2 columns automatically on phone-width screens.

        cards = []

        for name, poster in zip(names, posters):
            cards.append(
                f'<div class="poster-card"><img src="{poster}" /><p>{name}</p></div>'
            )

        cards_html = '<div class="poster-grid">' + "".join(cards) + '</div>'

        st.markdown(cards_html, unsafe_allow_html=True)


# =========================================================
#                     ROUTER
# =========================================================

if st.session_state.logged_in:
    show_main_app()
else:
    show_auth_screen()
