import requests
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import logging
import streamlit as st  # ✅ secrets 사용을 위한 import

# ✅ secrets.toml에 있는 API 키 사용
API_KEY = st.secrets["API_KEY"]

# 관세청 API URL
URL = 'http://apis.data.go.kr/1220000/nitemtrade/getNitemtradeList'

# 로그 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_trade_data(start_yyyymm: str, end_yyyymm: str, hs_code: str, country_code: str = None):
    hs_code = str(hs_code).zfill(10)
    params = {
        'serviceKey': API_KEY,
        'strtYymm': start_yyyymm,
        'endYymm': end_yyyymm,
        'hsSgn': hs_code,
    }
    if country_code:
        params['cntyCd'] = country_code

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(URL, params=params, timeout=10)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            items = root.findall(".//item")
            if not items:
                return pd.DataFrame(), "조회된 데이터가 없습니다."

            data = []
            for item in items:
                try:
                    row = {
                        'hsCd': item.findtext('hsCd'),
                        'year': item.findtext('year'),
                        'balPayments': float(item.findtext('balPayments') or 0),
                        'expDlr': float(item.findtext('expDlr') or 0),
                        'expWgt': float(item.findtext('expWgt') or 0),
                        'impDlr': float(item.findtext('impDlr') or 0),
                        'impWgt': float(item.findtext('impWgt') or 0),
                        'statCd': item.findtext('statCd'),
                    }
                    data.append(row)
                except Exception as e:
                    logging.warning(f"데이터 파싱 오류: {e} - 해당 항목 건너뜀")
                    continue

            df = pd.DataFrame(data)
            return df, None
        except Exception as e:
            logging.warning(f"⚠️ 요청 실패 ({start_yyyymm}), 재시도 {attempt+1}/{max_retries}: {e}")
            time.sleep(1)
    return pd.DataFrame(), f"요청 실패: {start_yyyymm}"

def fetch_trade_data_by_month_range(start_yyyymm: str, end_yyyymm: str, hs_code: str, country_code: str = None):
    start_date = datetime.strptime(start_yyyymm, "%Y%m")
    end_date = datetime.strptime(end_yyyymm, "%Y%m")
    all_data = []

    while start_date <= end_date:
        yyyymm = start_date.strftime("%Y%m")
        logging.info(f"월별 데이터 수집 중: {yyyymm}")
        df, err_msg = fetch_trade_data(yyyymm, yyyymm, hs_code, country_code)
        if err_msg:
            logging.warning(f"❌ {err_msg}")
        if not df.empty:
            df['yyyymm'] = yyyymm
            all_data.append(df)
        start_date += relativedelta(months=1)
        time.sleep(0.5)

    if all_data:
        result_df = pd.concat(all_data, ignore_index=True)

        result_df = result_df[result_df['impWgt'] > 0].copy()
        result_df.rename(columns={'impWgt': 'qty'}, inplace=True)
        result_df['unit'] = 'kg'
        result_df['unitPrice'] = result_df['impDlr'] / result_df['qty']
        result_df.replace([float('inf'), -float('inf')], pd.NA, inplace=True)

        return result_df[['yyyymm', 'impDlr', 'qty', 'unit', 'unitPrice']], None
    else:
        return pd.DataFrame(), "기간 내 데이터가 없습니다."
