import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="La Red de Hispanos – Attendance",
    page_icon="🌐",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
h1, h2, h3 {
    font-family: 'DM Serif Display', serif;
}

/* KPI cards */
.kpi-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border-radius: 16px;
    padding: 24px 20px;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 4px 24px rgba(0,0,0,0.2);
}
.kpi-value {
    font-family: 'DM Serif Display', serif;
    font-size: 2.6rem;
    color: #f0a500;
    line-height: 1;
    margin-bottom: 6px;
}
.kpi-label {
    font-size: 0.78rem;
    color: #a0aec0;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    font-weight: 500;
}

/* Section headers */
.section-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.5rem;
    color: #1a1a2e;
    margin: 32px 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 2px solid #f0a500;
    display: inline-block;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
}
section[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Load Data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv('attendance_clean.csv', parse_dates=['Fecha'])
    return df

df = load_data()

# ── Sidebar Filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌐 La Red de Hispanos")
    st.markdown("---")
    st.markdown("### Filters")

    # Date range
    min_date = df['Fecha'].min()
    max_date = df['Fecha'].max()
    date_range = st.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    # Source filter
    sources = ['All'] + sorted(df['Source'].dropna().unique().tolist())
    selected_source = st.selectbox("Platform", sources)

    st.markdown("---")
    st.markdown("<small style='color:#718096'>Dashboard · La Red de Hispanos</small>", unsafe_allow_html=True)

# ── Apply Filters ─────────────────────────────────────────────────────────────
filtered = df.copy()
if len(date_range) == 2:
    filtered = filtered[
        (filtered['Fecha'] >= pd.Timestamp(date_range[0])) &
        (filtered['Fecha'] <= pd.Timestamp(date_range[1]))
    ]
if selected_source != 'All':
    filtered = filtered[filtered['Source'] == selected_source]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 🌐 La Red de Hispanos")
st.markdown("#### Event Attendance Dashboard")
st.markdown("---")

# ── KPI Cards ─────────────────────────────────────────────────────────────────
total_attendances = int(filtered['Asistencia'].sum())
total_events      = filtered['Evento'].nunique()
unique_members    = filtered['Member Name'].nunique()
heylo_pct         = (
    filtered[filtered['Source'] == 'Heylo']['Asistencia'].sum()
    / filtered['Asistencia'].sum() * 100
    if filtered['Asistencia'].sum() > 0 else 0
)

k1, k2, k3, k4 = st.columns(4)
for col, value, label in [
    (k1, f"{total_attendances:,}", "Total Attendances"),
    (k2, str(total_events),        "Events Held"),
    (k3, f"{unique_members:,}",    "Unique Members"),
    (k4, f"{heylo_pct:.0f}%",      "From Heylo"),
]:
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{value}</div>
            <div class="kpi-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Colors ────────────────────────────────────────────────────────────────────
COLOR_HEYLO      = "#f0a500"
COLOR_EVENTBRITE = "#1a1a2e"
COLOR_TOTAL      = "#e05c3a"

# ── 1. Top Events ─────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">🏆 Event Performance</p>', unsafe_allow_html=True)

top_n = st.slider("Show top N events", 5, 30, 15)

by_event = (
    filtered.groupby(['Evento', 'Source'])['Asistencia']
    .sum()
    .reset_index()
)
totals = by_event.groupby('Evento')['Asistencia'].sum().reset_index()
totals.columns = ['Evento', 'Total']
top_events = totals.nlargest(top_n, 'Total')['Evento']
by_event_top = by_event[by_event['Evento'].isin(top_events)]
by_event_top = by_event_top.merge(totals, on='Evento').sort_values('Total', ascending=True)

fig_events = px.bar(
    by_event_top,
    x='Asistencia',
    y='Evento',
    color='Source',
    orientation='h',
    color_discrete_map={'Heylo': COLOR_HEYLO, 'Eventbrite': COLOR_EVENTBRITE},
    title=f'Top {top_n} Events by Attendance (Heylo vs Eventbrite)',
    labels={'Asistencia': 'Attendees', 'Evento': ''},
)
fig_events.update_layout(
    height=500,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    legend_title='Platform',
    font_family='DM Sans',
    title_font_family='DM Serif Display',
)
fig_events.update_xaxes(showgrid=True, gridcolor='rgba(0,0,0,0.06)')
fig_events.update_yaxes(showgrid=False)
st.plotly_chart(fig_events, use_container_width=True)

# ── 2. Growth Over Time ───────────────────────────────────────────────────────
st.markdown('<p class="section-title">📈 Growth Over Time</p>', unsafe_allow_html=True)

col_left, col_right = st.columns([2, 1])

with col_left:
    by_month = (
        filtered.copy()
        .assign(Month=filtered['Fecha'].dt.to_period('M').dt.to_timestamp())
        .groupby(['Month', 'Source'])['Asistencia']
        .sum()
        .reset_index()
    )

    fig_time = px.line(
        by_month,
        x='Month',
        y='Asistencia',
        color='Source',
        markers=True,
        color_discrete_map={'Heylo': COLOR_HEYLO, 'Eventbrite': COLOR_EVENTBRITE},
        title='Monthly Attendance by Platform',
        labels={'Asistencia': 'Attendees', 'Month': ''},
    )
    fig_time.update_layout(
        height=350,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_family='DM Sans',
        title_font_family='DM Serif Display',
    )
    fig_time.update_xaxes(showgrid=False)
    fig_time.update_yaxes(showgrid=True, gridcolor='rgba(0,0,0,0.06)')
    st.plotly_chart(fig_time, use_container_width=True)

with col_right:
    # Events per month
    events_per_month = (
        filtered.copy()
        .assign(Month=filtered['Fecha'].dt.to_period('M').dt.to_timestamp())
        .groupby('Month')['Evento']
        .nunique()
        .reset_index()
    )
    events_per_month.columns = ['Month', 'Events']

    fig_epm = px.bar(
        events_per_month,
        x='Month',
        y='Events',
        title='Events per Month',
        color_discrete_sequence=[COLOR_TOTAL],
        labels={'Events': 'Nº Events', 'Month': ''},
    )
    fig_epm.update_layout(
        height=350,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_family='DM Sans',
        title_font_family='DM Serif Display',
    )
    fig_epm.update_xaxes(showgrid=False)
    fig_epm.update_yaxes(showgrid=True, gridcolor='rgba(0,0,0,0.06)')
    st.plotly_chart(fig_epm, use_container_width=True)

# ── 3. Heylo vs Eventbrite ────────────────────────────────────────────────────
st.markdown('<p class="section-title">⚖️ Heylo vs Eventbrite</p>', unsafe_allow_html=True)

c1, c2 = st.columns(2)

with c1:
    source_totals = filtered.groupby('Source')['Asistencia'].sum().reset_index()
    fig_pie = px.pie(
        source_totals,
        names='Source',
        values='Asistencia',
        color='Source',
        color_discrete_map={'Heylo': COLOR_HEYLO, 'Eventbrite': COLOR_EVENTBRITE},
        title='Total Attendance Share',
        hole=0.45,
    )
    fig_pie.update_layout(
        height=320,
        font_family='DM Sans',
        title_font_family='DM Serif Display',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with c2:
    source_events = filtered.groupby('Source')['Evento'].nunique().reset_index()
    source_events.columns = ['Source', 'Unique Events']
    fig_se = px.bar(
        source_events,
        x='Source',
        y='Unique Events',
        color='Source',
        color_discrete_map={'Heylo': COLOR_HEYLO, 'Eventbrite': COLOR_EVENTBRITE},
        title='Unique Events per Platform',
        labels={'Unique Events': 'Nº Events'},
    )
    fig_se.update_layout(
        height=320,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        font_family='DM Sans',
        title_font_family='DM Serif Display',
    )
    fig_se.update_yaxes(showgrid=True, gridcolor='rgba(0,0,0,0.06)')
    st.plotly_chart(fig_se, use_container_width=True)

# ── 4. Member Engagement ──────────────────────────────────────────────────────
st.markdown('<p class="section-title">👥 Member Engagement</p>', unsafe_allow_html=True)

top_members = (
    filtered.groupby('Member Name')['Asistencia']
    .sum()
    .reset_index()
    .sort_values('Asistencia', ascending=False)
    .head(20)
)

fig_members = px.bar(
    top_members,
    x='Asistencia',
    y='Member Name',
    orientation='h',
    color='Asistencia',
    color_continuous_scale=[[0, '#16213e'], [1, '#f0a500']],
    title='Top 20 Most Engaged Members',
    labels={'Asistencia': 'Events Attended', 'Member Name': ''},
)
fig_members.update_layout(
    height=500,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    coloraxis_showscale=False,
    font_family='DM Sans',
    title_font_family='DM Serif Display',
    yaxis={'categoryorder': 'total ascending'},
)
fig_members.update_xaxes(showgrid=True, gridcolor='rgba(0,0,0,0.06)')
st.plotly_chart(fig_members, use_container_width=True)

# ── 5. Raw Data ───────────────────────────────────────────────────────────────
with st.expander("📋 View Raw Data"):
    st.dataframe(filtered, use_container_width=True)
    csv = filtered.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download filtered data", csv, "filtered_attendance.csv", "text/csv")
