import streamlit as st
import os
from dotenv import load_dotenv
from google import genai
import auth
import database
from PIL import Image

# API KEY HANDLING (LOCAL + CLOUD)

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)


# PAGE CONFIG


st.set_page_config(page_title="Companion Fashion Stylist", layout="centered")


# UI STYLE


st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
}
.stButton > button {
    border-radius: 12px;
    padding: 10px 22px;
    font-weight: 600;
    background: linear-gradient(90deg, #6366f1, #8b5cf6);
    color: white;
    border: none;
}
.card {
    padding: 22px;
    border-radius: 16px;
    background: white;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.06);
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)


# SESSION STATE


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""


# LOGIN / REGISTER

if not st.session_state.logged_in:

    st.title("🔐 Login / Register")

    option = st.radio("Choose Option", ["Login", "Register"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Submit"):

        if option == "Register":
            if auth.register(username, password):
                st.success("Registered Successfully! Please Login.")
            else:
                st.error("User already exists.")

        elif option == "Login":
            if auth.login(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid credentials.")

    st.stop()


# IMAGE ANALYSIS FUNCTION


def analyze_uploaded_image(image_file):

    image = Image.open(image_file)

    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=[
            image,
            "Analyze this person's current outfit. Describe what they are wearing, their style vibe, and suggest detailed improvement ideas."
        ]
    )

    return response.text


# FULL OUTFIT GENERATION


def generate_full_outfit(prompt):

    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=prompt
    )

    return response.text


# DISPLAY FUNCTION (FULL MODE)


def display_structured_output(text):

    parts = text.split("Similar Products:")

    outfit_text = parts[0].strip()
    products_text = parts[1].strip() if len(parts) > 1 else ""

    st.markdown("### 🧥 Outfit Details")
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown(outfit_text.replace("\n", "  \n"))
    st.markdown("</div>", unsafe_allow_html=True)

    if products_text:
        st.markdown("### 🛒 Similar Products")
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(products_text.replace("\n", "  \n"))
        st.markdown("</div>", unsafe_allow_html=True)


# NAVIGATION


menu = st.sidebar.radio("Navigation", ["Generate Look", "Dashboard"])


# GENERATE LOOK PAGE


if menu == "Generate Look":

    st.title("👗 AI Fashion Stylist")
    st.write(f"Welcome, **{st.session_state.username}** 🤗")

    mode = st.radio(
        "Choose Styling Mode",
        ["📸 Upload & Improve My Look", "✨ Generate Full Styled Outfit"]
    )

    
    # MODE 1: UPLOAD & IMPROVE
    

    if mode == "📸 Upload & Improve My Look":

        uploaded_file = st.file_uploader("Upload Your Photo", type=["jpg", "png", "jpeg"])

        if uploaded_file:
            st.image(uploaded_file, caption="Your Uploaded Image", use_container_width=True)

        if st.button("✨ Analyze & Improve"):

            if not uploaded_file:
                st.warning("Please upload an image first.")
            else:
                with st.spinner("Analyzing your outfit..."):
                    analysis = analyze_uploaded_image(uploaded_file)

                st.session_state.improvement = analysis

        if "improvement" in st.session_state:
            st.markdown("###  Improvement Suggestions")
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.write(st.session_state.improvement)
            st.markdown("</div>", unsafe_allow_html=True)

    
    # MODE 2: FULL OUTFIT
    

    else:

        gender = st.selectbox("Select Gender", ["Female", "Male"])
        preferred_fit = st.selectbox("Preferred Fit", ["Relaxed", "Regular", "Slim"])
        style_vibe = st.selectbox("Style Vibe", ["Classic", "Streetwear", "Minimal", "Korean", "Chic"])
        favorite_colors = st.multiselect("Favorite Colors", ["Navy", "Pastels", "Beige", "Black", "White", "Pink", "Purple"])
        occasion = st.selectbox("Occasion", ["Casual", "Party", "Office", "Date", "Wedding"])

        if st.button("✨ Generate Full Outfit"):

            prompt = f"""
    You are a professional Indian fashion stylist and shopping assistant.

    Generate a clean structured outfit response.

    IMPORTANT RULES:
    - Use ONLY Indian platforms: Amazon.in, Myntra, Ajio, Flipkart, Tata Cliq
    - Prices must be in Indian Rupees (₹)
    - Budget range: ₹999–₹2000

    User Preferences:
    Gender: {gender}
    Preferred Fit: {preferred_fit}
    Style: {style_vibe}
    Favorite Colors: {favorite_colors}
    Occasion: {occasion}

    Format:

    Gender:
    Style:
    Occasion:

    Top:
    Bottom:
    Footwear:
    Accessories:
    Color Anchor:

    ------------------------------------
    Similar Products:

    1. Product Name:
    Platform:
    Price:
    Description:

    2. Product Name:
    Platform:
    Price:
    Description:

    3. Product Name:
    Platform:
    Price:
    Description:
    """

            with st.spinner("Generating outfit..."):
                result = generate_full_outfit(prompt)

            st.session_state.generated_output = result

        if "generated_output" in st.session_state:

            display_structured_output(st.session_state.generated_output)

            if st.button("⭐ Save Outfit"):

                database.save_design(
                    st.session_state.username,
                    gender,
                    style_vibe,
                    occasion,
                    st.session_state.generated_output,
                    None
                )

                st.success("Outfit saved successfully!")
                

# DASHBOARD


elif menu == "Dashboard":

    st.title("📊 Your Saved Looks")

    designs = database.get_user_designs(st.session_state.username)

    if not designs:
        st.info("No saved looks yet.")
    else:
        for design in designs:
            st.markdown("<div class='card'>", unsafe_allow_html=True)

            st.write(f"**Gender:** {design.get('gender', '-')}")
            st.write(f"**Style:** {design.get('style', '-')}")
            st.write(f"**Occasion:** {design.get('occasion', '-')}")
            st.write(design.get('outfit', '-'))

            st.markdown("</div>", unsafe_allow_html=True)


# LOGOUT

if st.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()