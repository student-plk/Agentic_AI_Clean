import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import google.generativeai as genai


genai.configure(api_key="AIzaSyA00cuzjd1OwhyWaL7B-SQmWOMmz8G56Ew")
model = genai.GenerativeModel("gemini-1.5-flash")


CATEGORY_URLS = {
    "National": "https://www.thehindu.com/news/national/",
    "International": "https://www.thehindu.com/news/international/",
    "Politics": "https://www.thehindu.com/news/national/politics/",
    "Business": "https://www.thehindu.com/business/",
    "Sports": "https://www.thehindu.com/sport/",
    "Technology": "https://www.thehindu.com/sci-tech/technology/"
}


@st.cache_data(show_spinner=True)
def scrape_category_news(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        articles = []
        for link in soup.find_all("a", href=True):
            title = link.get_text(strip=True)
            href = link['href']
            full_url = href if href.startswith("http") else f"https://www.thehindu.com{href}"

            if title and "/news/" in href:
                articles.append({"title": title, "url": full_url})

        return articles
    except Exception as e:
        return []


def generate_summary(category, news_list, user_prompt, date_text):
    if not news_list:
        return "No news articles found."

    combined_titles = "\n".join([f"- {item['title']}" for item in news_list])
    prompt = f"""
    You are a journalist summarizing the latest {category} news.

    🗓️ Date: {date_text}
    🗂️ Category: {category}
    📰 Headlines:
    {combined_titles}

    User question: {user_prompt}

    Please summarize the top news items and answer the query in a formal tone.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Gemini API Error: {e}"


st.set_page_config(page_title="News by Date & Category", page_icon="🗞️")
st.title("🗞️ AI News Generator")
st.markdown("Get news from *The Hindu* based on category and date.")


category = st.selectbox("Select News Category:", list(CATEGORY_URLS.keys()))
selected_date = st.date_input("Pick a date (for reference only):", value=datetime.today())
user_prompt = st.text_input("Ask something about the selected category/date:", placeholder="e.g., What happened in sports today?")


if st.button("Generate News"):
    with st.spinner(f"Scraping {category} news..."):
        news_items = scrape_category_news(CATEGORY_URLS[category])

    if news_items:
        st.success(f"Fetched {len(news_items)} news articles.")
        with st.expander("📰 Click to preview headlines"):
            for item in news_items:
                st.markdown(f"- [{item['title']}]({item['url']})")

        if user_prompt:
            with st.spinner("Asking Gemini..."):
                summary = generate_summary(category, news_items, user_prompt, selected_date.strftime('%B %d, %Y'))
                st.markdown("Gemini's Summary")
                st.write(summary)
        else:
            st.warning("Please enter a question to ask Gemini.")
    else:
        st.error("No news articles found in this category. Try another.")
