import streamlit as st
import pandas as pd
import datetime
import altair as alt
from data_loader import fetch_trade_data_by_month_range

# ---------------------------
# CSS 스타일 주입 함수
# ---------------------------
def inject_css():
    st.markdown(
        """
        <style>
        html {
            zoom: 100%;
            /* 또는 */
            /* transform: scale(1); transform-origin: 0 0; */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# ---------------------------
# 기본 설정 및 상수
# ---------------------------
st.set_page_config(page_title="단가탐정", layout="wide")

DEFAULT_MAJOR_COUNTRIES = [
    'CN', 'US', 'JP', 'DE', 'VN', 'TH', 'ID', 'IN', 'IT', 'MY',
    'FR', 'NL', 'CA', 'AU', 'MX', 'CZ', 'PL', 'TR', 'ES', 'GB'
]

COUNTRY_NAME_MAP = {
    'CN': '중국', 'US': '미국', 'JP': '일본', 'DE': '독일', 'VN': '베트남', 'TH': '태국',
    'ID': '인도네시아', 'IN': '인도', 'IT': '이탈리아', 'MY': '말레이시아', 'FR': '프랑스',
    'NL': '네덜란드', 'CA': '캐나다', 'AU': '호주', 'MX': '멕시코', 'CZ': '체코',
    'PL': '폴란드', 'TR': '터키', 'ES': '스페인', 'GB': '영국'
}

# ---------------------------
# 데이터 로딩 및 공통 유틸
# ---------------------------
@st.cache_data(show_spinner=False)
def load_hs_codes(csv_path="cleaned_hs_code_lookup.csv"):
    df = pd.read_csv(csv_path, dtype={'HS코드': str})
    df['HS코드'] = df['HS코드'].str.zfill(10)
    return df[['품목명', 'HS코드']].dropna().drop_duplicates()

def show_country_chart(df, unit):
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('국가명:N', sort='-y', title='국가'),
        y=alt.Y('평균 단가:Q', title=f'평균 수입단가 (USD/{unit})'),
        tooltip=[
            alt.Tooltip('국가명', title='국가'),
            alt.Tooltip('평균 단가', title='평균 단가', format='.2f'),
            alt.Tooltip('총 중량 (kg)', title='총 중량 (kg)', format=',')
        ]
    ).properties(width=700, height=400)
    st.altair_chart(chart, use_container_width=True)

# ---------------------------
# 기능 1: 국가 추천 (품목 기반)
# ---------------------------
def run_country_recommendation(hs_df):
    st.subheader("📦 국가 추천 (품목 기반)")

    with st.form("country_form"):
        product_options = ["-- 품목을 선택하세요 --"] + [
            f"{row['품목명']} ({row['HS코드']})" for _, row in hs_df.iterrows()
        ]
        selected = st.selectbox("📌 수입 품목 선택", product_options)

        current_year = datetime.datetime.now().year
        years = list(range(2018, current_year + 1))
        months = list(range(1, 13))

        st.markdown("#### ⏱️ 시작 날짜")
        col1, col2 = st.columns(2)
        with col1:
            start_year = st.selectbox("연도", years, key="country_start_year")
        with col2:
            start_month = st.selectbox("월", months, format_func=lambda m: f"{m:02d}월", key="country_start_month")

        st.markdown("#### ⏱️ 종료 날짜")
        col3, col4 = st.columns(2)
        with col3:
            end_year = st.selectbox("연도 ", years, index=len(years)-1, key="country_end_year")
        with col4:
            end_month = st.selectbox("월 ", months, format_func=lambda m: f"{m:02d}월", index=11, key="country_end_month")

        submitted = st.form_submit_button("🔍 검색")

    if 'country_results' in st.session_state and st.session_state.get('country_results') is not None:
        st.markdown("### 💡 이전 국가 추천 결과")

        prev_product = st.session_state.get('country_selected_product')
        prev_start = st.session_state.get('country_start_date')
        prev_end = st.session_state.get('country_end_date')

        if prev_product and prev_start and prev_end:
            st.markdown(f"- 🔍 검색 품목: **{prev_product}**")
            st.markdown(f"- 📆 검색 기간: **{prev_start.strftime('%Y-%m')} ~ {prev_end.strftime('%Y-%m')}**")

        df_prev = st.session_state['country_results']
        df_display = df_prev.copy()
        df_display['총 중량 (kg)'] = df_display['총 중량 (kg)'].apply(lambda x: f"{int(x):,} kg")
        df_display['평균 단가'] = df_display['평균 단가'].apply(lambda x: f"{x:.2f} USD/{df_prev['unit'].iloc[0]}")

        st.dataframe(
            df_display[['국가명', '평균 단가', '총 중량 (kg)']].rename(columns={
                '국가명': '국가',
                '평균 단가': '평균 단가',
                '총 중량 (kg)': '총 중량'
            }),
            use_container_width=True,
            hide_index=True
        )

        show_country_chart(df_prev, df_prev['unit'].iloc[0])

    if not submitted:
        return

    if selected == "-- 품목을 선택하세요 --":
        st.warning("⚠️ 먼저 품목을 선택해주세요.")
        return

    try:
        start_date = datetime.date(start_year, start_month, 1)
        end_date = datetime.date(end_year, end_month, 1)
    except:
        st.warning("⚠️ 날짜를 정확히 선택해주세요.")
        return

    if start_date > end_date:
        st.error("❌ 시작일은 종료일 이전이어야 합니다.")
        return

    selected_product = selected.split(" (")[0]
    hs_code = selected.split("(")[-1].replace(")", "")

    start_yyyymm = start_date.strftime('%Y%m')
    end_yyyymm = end_date.strftime('%Y%m')

    with st.spinner("데이터를 불러오는 중입니다. 잠시만 기다려 주세요..."):
        results = []
        for country in DEFAULT_MAJOR_COUNTRIES:
            df, _ = fetch_trade_data_by_month_range(start_yyyymm, end_yyyymm, hs_code, country)
            if df.empty:
                continue
            avg_price = df['unitPrice'].mean()
            total_qty = df['qty'].sum()
            unit = df['unit'].iloc[0]

            results.append({
                '국가': country,
                '국가명': COUNTRY_NAME_MAP.get(country, country),
                '평균 단가': round(avg_price, 2),
                '총 중량 (kg)': total_qty,
                'unit': unit
            })

    if not results:
        st.warning("❌ 데이터가 부족하여 추천이 어렵습니다.")
        st.session_state['country_results'] = None
        return

    df = pd.DataFrame(results).sort_values('총 중량 (kg)', ascending=False)

    st.session_state['country_results'] = df
    st.session_state['country_selected_product'] = selected_product
    st.session_state['country_start_date'] = start_date
    st.session_state['country_end_date'] = end_date

    df_display = df.copy()
    df_display['총 중량 (kg)'] = df_display['총 중량 (kg)'].apply(lambda x: f"{int(x):,} kg")
    df_display['평균 단가'] = df_display['평균 단가'].apply(lambda x: f"{x:.2f} USD/{df['unit'].iloc[0]}")

    st.markdown("### 📊 주요 국가별 평균 수입단가 및 수입중량")
    st.dataframe(df_display[['국가명', '평균 단가', '총 중량 (kg)']].rename(columns={
        '국가명': '국가',
        '평균 단가': '평균 단가',
        '총 중량 (kg)': '총 중량'
    }), use_container_width=True, hide_index=True)

    show_country_chart(df, df['unit'].iloc[0])

# ---------------------------
# 기능 2: 대체국가 추천
# ---------------------------
def run_alternative_recommendation(hs_df):
    st.subheader("🔄 대체국가 추천 (기준 국가 기반)")

    with st.form("alternative_form"):
        product_options = ["-- 품목을 선택하세요 --"] + hs_df['품목명'].tolist()
        selected_product = st.selectbox("📌 수입 품목 선택", product_options)

        base_country_options = ["-- 국가를 선택하세요 --"] + DEFAULT_MAJOR_COUNTRIES
        base_country = st.selectbox(
            "🔎 기준 국가 선택",
            base_country_options,
            format_func=lambda x: COUNTRY_NAME_MAP.get(x, x) if x != "-- 국가를 선택하세요 --" else x
        )

        current_year = datetime.datetime.now().year
        years = list(range(2018, current_year + 1))
        months = list(range(1, 13))

        st.markdown("#### ⏱️ 시작 날짜")
        col1, col2 = st.columns(2)
        with col1:
            start_year = st.selectbox("연도", years, key="alt_start_year")
        with col2:
            start_month = st.selectbox("월", months, format_func=lambda m: f"{m:02d}월", key="alt_start_month")

        st.markdown("#### ⏱️ 종료 날짜")
        col3, col4 = st.columns(2)
        with col3:
            end_year = st.selectbox("연도 ", years, index=len(years)-1, key="alt_end_year")
        with col4:
            end_month = st.selectbox("월 ", months, format_func=lambda m: f"{m:02d}월", index=11, key="alt_end_month")

        submitted = st.form_submit_button("🔍 검색")

    if 'alternative_results' in st.session_state and st.session_state.get('alternative_results') is not None:
        st.markdown("### 💡 이전 추천 대체국가 결과")

        prev_product = st.session_state.get('alternative_selected_product')
        prev_start = st.session_state.get('alternative_start_date')
        prev_end = st.session_state.get('alternative_end_date')
        base_price = st.session_state.get('alternative_base_avg_price')

        if prev_product and prev_start and prev_end:
            st.markdown(f"- 🔍 검색 품목: **{prev_product}**")
            st.markdown(f"- 📆 검색 기간: **{prev_start.strftime('%Y-%m')} ~ {prev_end.strftime('%Y-%m')}**")

        if base_price:
            st.markdown(f"- 🏳️ 기준 국가 평균 단가: **{base_price:.2f} USD/kg**")

        df_prev = st.session_state['alternative_results']
        df_display = df_prev.copy()
        df_display['총 중량 (kg)'] = df_display['총 중량 (kg)'].apply(lambda x: f"{int(x):,} kg")
        df_display['평균 단가'] = df_display['평균 단가'].apply(lambda x: f"{x:.2f} USD/{df_prev['unit'].iloc[0]}")
        df_display['단가 차이 (%)'] = df_display['단가 차이 (%)'].apply(lambda x: f"{x:+.1f}%")

        st.dataframe(
            df_display[['국가명', '평균 단가', '단가 차이 (%)', '총 중량 (kg)']].rename(columns={
                '국가명': '국가',
                '평균 단가': '평균 단가',
                '단가 차이 (%)': '단가 차이',
                '총 중량 (kg)': '총 중량'
            }),
            use_container_width=True,
            hide_index=True
        )

    if not submitted:
        return

    if selected_product == "-- 품목을 선택하세요 --":
        st.warning("⚠️ 먼저 품목을 선택해주세요.")
        return
    if base_country == "-- 국가를 선택하세요 --":
        st.warning("⚠️ 기준 국가를 선택해주세요.")
        return

    try:
        start_date = datetime.date(start_year, start_month, 1)
        end_date = datetime.date(end_year, end_month, 1)
    except:
        st.warning("⚠️ 날짜를 정확히 선택해주세요.")
        return

    if start_date > end_date:
        st.error("❌ 시작일은 종료일 이전이어야 합니다.")
        return

    hs_code = hs_df.loc[hs_df['품목명'] == selected_product, 'HS코드'].values[0]
    start_yyyymm = start_date.strftime('%Y%m')
    end_yyyymm = end_date.strftime('%Y%m')

    with st.spinner("데이터를 불러오는 중입니다. 잠시만 기다려 주세요..."):
        base_df, _ = fetch_trade_data_by_month_range(start_yyyymm, end_yyyymm, hs_code, base_country)
        if base_df.empty:
            st.warning("기준 국가 데이터가 없습니다.")
            st.session_state['alternative_results'] = None
            st.session_state['alternative_base_avg_price'] = None
            return

        base_avg_price = base_df['unitPrice'].mean()
        st.session_state['alternative_base_avg_price'] = base_avg_price
        st.session_state['alternative_selected_product'] = selected_product
        st.session_state['alternative_start_date'] = start_date
        st.session_state['alternative_end_date'] = end_date

        st.markdown(f"- 기준 국가 **{COUNTRY_NAME_MAP.get(base_country, base_country)}** 평균 단가: **{base_avg_price:.2f} USD/kg**")

        results = []
        for country in DEFAULT_MAJOR_COUNTRIES:
            if country == base_country:
                continue
            df, _ = fetch_trade_data_by_month_range(start_yyyymm, end_yyyymm, hs_code, country)
            if df.empty:
                continue
            avg_price = df['unitPrice'].mean()
            total_qty = df['qty'].sum()
            price_diff = base_avg_price - avg_price
            price_diff_pct = (price_diff / base_avg_price) * 100

            results.append({
                '국가': country,
                '국가명': COUNTRY_NAME_MAP.get(country, country),
                '평균 단가': round(avg_price, 2),
                '단가 차이 (%)': round(price_diff_pct, 1),
                '총 중량 (kg)': int(total_qty),
                'unit': df['unit'].iloc[0]
            })

    df = pd.DataFrame(results).sort_values('단가 차이 (%)', ascending=False)
    df_filtered = df[(df['단가 차이 (%)'] >= 10) & (df['총 중량 (kg)'] > 1000)]

    if df_filtered.empty:
        st.warning("추천할 대체국가가 충분하지 않습니다.")
        st.session_state['alternative_results'] = None
    else:
        st.session_state['alternative_results'] = df_filtered

        df_display = df_filtered.copy()
        df_display['총 중량 (kg)'] = df_display['총 중량 (kg)'].apply(lambda x: f"{int(x):,} kg")
        df_display['평균 단가'] = df_display['평균 단가'].apply(lambda x: f"{x:.2f} USD/{df_filtered['unit'].iloc[0]}")
        df_display['단가 차이 (%)'] = df_display['단가 차이 (%)'].apply(lambda x: f"{x:+.1f}%")

        st.markdown("### 💡 추천 대체국가")
        st.dataframe(
            df_display[['국가명', '평균 단가', '단가 차이 (%)', '총 중량 (kg)']].rename(columns={
                '국가명': '국가',
                '평균 단가': '평균 단가',
                '단가 차이 (%)': '단가 차이',
                '총 중량 (kg)': '총 중량'
            }),
            use_container_width=True,
            hide_index=True
        )

# ---------------------------
# 메인 실행
# ---------------------------
def main():
    inject_css()  # CSS 스타일 적용

    st.title("📦 수입상품 단가 비교 플랫폼")
    hs_df = load_hs_codes()

    st.sidebar.header("기능 선택")
    feature = st.sidebar.radio("원하는 기능을 선택하세요:", ["📦 국가 추천 (품목 기준)", "🔄 대체국가 추천 (기준 국가 기반)"])

    if feature.startswith("📦"):
        run_country_recommendation(hs_df)
    else:
        run_alternative_recommendation(hs_df)

if __name__ == "__main__":
    main()
