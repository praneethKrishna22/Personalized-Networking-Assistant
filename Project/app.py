"""Streamlit frontend for the Personalized Networking Assistant.

Talks to the FastAPI backend over HTTP. Set the BACKEND_URL environment
variable if the API isn't running on localhost:8000 (e.g. when tunneling
through ngrok in Colab, the backend still stays on localhost since both
processes run in the same VM - only the Streamlit port needs a public URL).
"""
import os

import requests
import streamlit as st

API_BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Personalized Networking Assistant", page_icon="🤝", layout="centered")
st.title("🤝 Personalized Networking Assistant")
st.caption("AI-generated conversation starters, tailored to the event and to you.")

tab1, tab2, tab3 = st.tabs(["✨ Generate Starters", "🔎 Fact Check", "🕘 History"])

# ---------------------------------------------------------------- Tab 1 --
with tab1:
    st.subheader("Generate tailored conversation starters")
    event_description = st.text_area(
        "Event description", placeholder="e.g. AI for Sustainable Cities"
    )
    interests_raw = st.text_input(
        "Your interests (comma-separated)", placeholder="climate change, urban planning"
    )
    num_starters = st.slider("Number of starters", 1, 5, 3)

    if st.button("Generate", type="primary"):
        if not event_description.strip():
            st.warning("Please enter an event description.")
        else:
            interests = [i.strip() for i in interests_raw.split(",") if i.strip()]
            data = None
            with st.spinner("Extracting themes and generating starters..."):
                try:
                    resp = requests.post(
                        f"{API_BASE_URL}/api/generate-starters",
                        json={
                            "event_description": event_description,
                            "interests": interests,
                            "num_starters": num_starters,
                        },
                        timeout=120,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    st.error(f"Request failed: {e}")

            if data:
                st.markdown("**Detected themes:** " + ", ".join(data["themes"]))
                for item in data["starters"]:
                    col1, col2, col3 = st.columns([6, 1, 1])
                    with col1:
                        st.write(f"💬 {item['starter']}")
                    with col2:
                        if st.button("👍", key=f"up_{item['id']}"):
                            requests.post(
                                f"{API_BASE_URL}/api/feedback",
                                json={"history_id": item["id"], "useful": True},
                            )
                            st.success("Thanks!")
                    with col3:
                        if st.button("👎", key=f"down_{item['id']}"):
                            requests.post(
                                f"{API_BASE_URL}/api/feedback",
                                json={"history_id": item["id"], "useful": False},
                            )
                            st.info("Got it.")

# ---------------------------------------------------------------- Tab 2 --
with tab2:
    st.subheader("Quick fact verification")
    query = st.text_input("Topic to fact-check", placeholder="blockchain in healthcare")
    if st.button("Check facts"):
        if not query.strip():
            st.warning("Please enter a topic.")
        else:
            data = None
            with st.spinner("Looking this up on Wikipedia..."):
                try:
                    resp = requests.post(
                        f"{API_BASE_URL}/api/fact-check", json={"query": query}, timeout=60
                    )
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    st.error(f"Request failed: {e}")

            if data:
                if data["found"]:
                    st.write(data["summary"])
                    st.markdown(f"[Read more on Wikipedia]({data['url']})")
                elif data["options"]:
                    st.info("Your query is ambiguous. Did you mean:")
                    for option in data["options"]:
                        st.write(f"- {option}")
                else:
                    st.warning("No reliable reference found for this topic.")

# ---------------------------------------------------------------- Tab 3 --
with tab3:
    st.subheader("Past conversation starters")
    st.button("Refresh history")
    try:
        resp = requests.get(f"{API_BASE_URL}/api/history", timeout=30)
        resp.raise_for_status()
        history = resp.json()
    except Exception as e:
        st.error(f"Could not load history: {e}")
        history = []

    if not history:
        st.caption("No history yet - generate some starters first.")

    for h in history:
        useful_icon = "👍" if h["useful"] is True else ("👎" if h["useful"] is False else "•")
        st.markdown(
            f"**{h['event_description']}** _(themes: {h['themes']})_ {useful_icon}\n\n> {h['starter']}"
        )
        st.divider()
