import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from supabase import create_client

# ---------- ПОДКЛЮЧЕНИЕ К SUPABASE ----------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------- ПАРАМЕТРЫ ----------
START_WEIGHT = 114.0
TARGET_WEIGHT = 67.0
TABLE_NAME = "weight_data"

st.set_page_config(page_title="Мой дневник веса", layout="wide")
st.title("📉 Мой дневник веса")


# ---------- ФУНКЦИИ ----------
def load_data():
    response = supabase.table(TABLE_NAME).select("*").order("date").execute()
    if not response.data:
        return pd.DataFrame(columns=['date', 'weight'])
    df = pd.DataFrame(response.data)
    df['date'] = pd.to_datetime(df['date']).dt.date
    return df


def save_data(date_input, weight_input):
    supabase.table(TABLE_NAME).upsert({
        "date": str(date_input),
        "weight": weight_input
    }).execute()


# ---------- ФОРМА ДЛЯ ВВОДА ----------
st.subheader("➕ Добавить новую запись")
with st.form("weight_form"):
    col1, col2 = st.columns(2)
    with col1:
        date_input = st.date_input("Дата", value=date.today())
    with col2:
        weight_input = st.number_input("Вес (кг)", min_value=30.0, max_value=200.0, step=0.1)
    submitted = st.form_submit_button("Сохранить")

    if submitted:
        save_data(date_input, weight_input)
        st.success(f"✅ Данные за {date_input} сохранены!")
        st.rerun()

# ---------- ЗАГРУЗКА ДАННЫХ ----------
df = load_data()

if len(df) == 0:
    st.info("📌 Нет данных. Добавьте первую запись.")
    st.stop()

df = df.sort_values('date')
df['diff_prev'] = df['weight'].diff().round(1)
df['diff_first'] = (df['weight'] - df['weight'].iloc[0]).round(1)

# ---------- ГРАФИК ----------
st.subheader("📈 График динамики веса")
fig = px.line(df, x='date', y='weight', markers=True)
fig.add_hline(y=TARGET_WEIGHT, line_dash="dash", line_color="green", annotation_text=f"Цель: {TARGET_WEIGHT} кг")
st.plotly_chart(fig, use_container_width=True)

# ---------- ТАБЛИЦА ----------
st.subheader("📋 Подробная таблица")
df_display = df.copy()
df_display['date'] = df_display['date'].astype(str)
df_display.columns = ['Дата', 'Вес (кг)', 'Разница с предыдущим днём (кг)', 'Разница с первым днём (кг)']
st.dataframe(df_display, use_container_width=True)

# ---------- СТАТИСТИКА ----------
st.subheader("🎯 Итоговая статистика")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Стартовый вес", f"{START_WEIGHT} кг")

with col2:
    current = df['weight'].iloc[-1]
    st.metric("Текущий вес", f"{current} кг", delta=f"{current - START_WEIGHT:+.1f} кг")

with col3:
    st.metric("Минимальный вес", f"{df['weight'].min()} кг")

with col4:
    st.metric("Максимальный вес", f"{df['weight'].max()} кг")

with col5:
    remaining = current - TARGET_WEIGHT
    if remaining > 0:
        st.metric("🎯 Цель", f"{TARGET_WEIGHT} кг", delta=f"осталось {remaining:.1f} кг", delta_color="off")
    else:
        st.metric("🎯 Цель", f"{TARGET_WEIGHT} кг", delta="✅ Цель достигнута!", delta_color="normal")

# ---------- ПРОГРЕСС ----------
if current > TARGET_WEIGHT:
    total = START_WEIGHT - TARGET_WEIGHT
    lost = START_WEIGHT - current
    progress = min(100, (lost / total) * 100)
else:
    progress = 100
st.progress(progress / 100)
st.caption(f"📊 Прогресс: {progress:.1f}% от цели")