import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import subprocess
from pathlib import Path

project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

from forex_scraper.realtime_manager import RealtimeDataManager
from forex_scraper.event_analyzer import EventOutcomeAnalyzer
from forex_scraper.market_news_analyzer import MarketNewsAnalyzer

st.set_page_config(page_title="Forex Dashboard", page_icon="📊", layout="wide")

if 'data_manager' not in st.session_state:
    st.session_state.data_manager = RealtimeDataManager(data_dir='data')
if 'event_analyzer' not in st.session_state:
    st.session_state.event_analyzer = EventOutcomeAnalyzer()
if 'market_analyzer' not in st.session_state:
    st.session_state.market_analyzer = MarketNewsAnalyzer()
if 'selected_pair' not in st.session_state:
    st.session_state.selected_pair = 'GOLDUSD'

data_mgr = st.session_state.data_manager
analyzer = st.session_state.event_analyzer
market_analyzer = st.session_state.market_analyzer

st.sidebar.title("📊 Forex Dashboard")

available_pairs = data_mgr.get_currency_pairs()
selected_pair = st.sidebar.selectbox("🔗 Select Pair", options=available_pairs, index=available_pairs.index('GOLDUSD') if 'GOLDUSD' in available_pairs else 0)
st.session_state.selected_pair = selected_pair

pair_urls = {'EURUSD': 'eurusd', 'GBPUSD': 'gbpusd', 'USDJPY': 'usdjpy', 'GOLDUSD': 'goldusd', 'AUDUSD': 'audusd'}
pair_url = pair_urls.get(selected_pair, selected_pair.lower())
forexfactory_url = f"https://www.forexfactory.com/market/{pair_url}"
st.sidebar.markdown(f"**Market:** [{selected_pair}]({forexfactory_url})")

if st.sidebar.button("📰 Fetch latest news for this pair", use_container_width=True):
    with st.spinner(f"Scraping latest news for {selected_pair}..."):
        try:
            cmd = [
                sys.executable,
                "-m", "scrapy", "crawl", "market_news",
                "-a", f"pair={selected_pair}",
                "-O", f"data/market_news_{selected_pair.lower()}.jsonl",  # overwrite instead of append
            ]
            result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                st.success(f"Updated news for {selected_pair}")
                # Clear cache so new file will be loaded
                data_mgr.news_cache = None
            else:
                st.error("News refresh failed. See logs for details.")
                st.code(result.stderr[-400:])
        except Exception as e:
            st.error(f"Error while scraping news: {e}")
    st.rerun()

if st.sidebar.button("🔄 Refresh dashboard", use_container_width=True):
    st.rerun()

st.sidebar.markdown("---")
impact_filter = st.sidebar.multiselect(
    "Impact",
    ["High Impact Expected", "Medium Impact Expected", "Low Impact Expected"],
    default=["High Impact Expected"],
)
currency_filter = st.sidebar.multiselect(
    "Currencies",
    ["USD", "EUR", "GBP", "JPY", "AUD", "CHF"],
    default=["USD", "EUR", "GBP"],
)
watch_pairs = st.sidebar.multiselect(
    "Pairs",
    data_mgr.get_currency_pairs(),
    default=['EURUSD', 'GBPUSD', 'GOLDUSD', 'USDJPY'],
)
# Always include the currently selected pair in the Signals section
if selected_pair not in watch_pairs:
    watch_pairs = [selected_pair] + list(watch_pairs)

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(f"# 📈 {selected_pair} Analysis")
with col2:
    st.caption(f"Updated: {datetime.now().strftime('%H:%M:%S')}")

st.markdown(f"## 📰 News for {selected_pair}")
pair_news = data_mgr.load_pair_specific_news(selected_pair)

if pair_news:
    # High-level stats
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Articles", len(pair_news))
    col2.metric("Bullish", sum(1 for a in pair_news[:20] if a.get('sentiment') == 'BULLISH'))
    col3.metric("Bearish", sum(1 for a in pair_news[:20] if a.get('sentiment') == 'BEARISH'))
    col4.metric("High Impact", sum(1 for a in pair_news[:20] if a.get('impact') == 'HIGH'))

    # News-based market outcome analysis
    analysis = market_analyzer.analyze_batch(pair_news[:20])
    if analysis:
        st.markdown("### 🧠 News-based Market Outlook")
        a1, a2, a3, a4 = st.columns(4)
        a1.metric("Recommendation", analysis.get('recommendation', 'HOLD'))
        a2.metric("Probable Direction", analysis.get('probable_direction', 'NEUTRAL'))
        a3.metric("Avg Confidence", f"{analysis.get('average_confidence', 0.0) * 100:.1f}%")
        a4.metric("High-Impact News", analysis.get('high_impact_articles', 0))

    st.markdown("---")
    # Group stories by section so that "Hottest Stories" and
    # "Latest Stories" are displayed like on ForexFactory
    grouped = {}
    for article in pair_news:
        section = article.get('section') or 'Stories'
        grouped.setdefault(section, []).append(article)

    for section, articles in grouped.items():
        st.markdown(f"### {section}")
        # Show up to 5 stories per section
        for article in articles[:5]:
            sentiment = article.get('sentiment', 'NEUTRAL')
            emoji = '🟢' if sentiment == 'BULLISH' else ('🔴' if sentiment == 'BEARISH' else '🟡')
            title = article.get('title', 'N/A')
            source = article.get('source')
            time_label = article.get('date')

            meta_parts = []
            if source:
                meta_parts.append(f"From {source}")
            if time_label:
                meta_parts.append(time_label)

            meta = f" ({' | '.join(meta_parts)})" if meta_parts else ""
            st.markdown(f"- {title}  ")
            st.caption(f"{emoji} {sentiment}{meta}")

        st.divider()
else:
    st.warning(f"No news for {selected_pair}. Use the button in the sidebar to fetch latest news.")

st.markdown("## 💡 Signals")
signals = []
for pair in watch_pairs:
    # Use the same news-based analyzer for signals so they align with the outlook above
    pair_news_for_signal = data_mgr.load_pair_specific_news(pair)
    if pair_news_for_signal:
        pair_analysis = market_analyzer.analyze_batch(pair_news_for_signal[:20])
    else:
        pair_analysis = None

    if pair_analysis:
        recommendation = pair_analysis.get('recommendation', 'HOLD')
        direction = pair_analysis.get('probable_direction', 'NEUTRAL')
        confidence = pair_analysis.get('average_confidence', 0.0)
    else:
        recommendation = 'HOLD'
        direction = 'NO DATA'
        confidence = 0.0

    if recommendation == 'BUY':
        emoji = '🟢'
    elif recommendation == 'SELL':
        emoji = '🔴'
    else:
        emoji = '🟡'

    signals.append({
        'Pair': pair,
        'Signal': f"{emoji} {recommendation}",
        'Direction': direction,
        'Confidence': f"{confidence * 100:.1f}%",
    })

df = pd.DataFrame(signals)
st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown("## 📅 Events")
events = data_mgr.load_latest_calendar_events()
upcoming = data_mgr.get_upcoming_events(hours_ahead=48)
filtered = [e for e in upcoming if e.get('importance') in impact_filter and e.get('currency') in currency_filter]

if filtered:
    rows = []
    for e in filtered[:10]:
        rows.append({'Time': e.get('time', 'TBD'), 'Event': e.get('event', '?'), 'Currency': e.get('currency', '?'), 'Impact': e.get('importance', '').replace(' Impact Expected', '')})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("Forex Dashboard | ForexFactory + Reuters | Real-time Market News | Educational Use Only")
