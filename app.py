import streamlit as st

st.set_page_config(
    page_title="TerraSignal",
    page_icon="🌍"
)

st.title("🌍 TerraSignal")
st.subheader("Earth's signal, in simple words.")

st.markdown("---")

location = st.text_input("Your City:", "Colombo")

if st.button("Get Earth's Signal 📻"):
    st.success(f"TerraSignal Report for {location}:")
    st.markdown("### 🌦️ Good morning.")
    st.markdown("### 🌧️ Rain may be expected.")
    st.markdown("### ☔ Please take an umbrella.")
    st.markdown("### 🌡️ Stay comfortable and hydrated.")

st.markdown("---")

st.caption("TerraSignal Prototype")
st.caption("Built by TharidiDev | NASA Space Apps Colombo 2026")
