# 📦 수입상품 단가 비교 플랫폼

자영업자를 위한 수입상품 국가별 단가 비교 및 대체 수입국가 추천 플랫폼입니다.  
관세청 Open API를 활용해 월별 수입 데이터를 분석하고 시각화합니다.

![Streamlit UI](https://user-images.githubusercontent.com/your_screenshot.png) <!-- 필요 시 캡처 이미지 추가 -->

---

## 🚀 주요 기능

### 1. 📦 국가 추천 (품목 기준)
- 품목을 선택하면 주요 국가들의 수입단가 및 총중량 정보를 제공
- 국가별 평균 단가와 그래프를 통해 한눈에 비교 가능

### 2. 🔄 대체국가 추천 (기준 국가 기반)
- 특정 국가를 기준으로, 평균 수입단가가 더 낮고 충분한 물량이 있는 국가를 자동 추천
- 단가 차이(%)와 중량을 기반으로 직관적인 의사결정 지원

---

## 🛠️ 사용 기술

- **Python**
- **Streamlit** - 프론트엔드 및 웹 배포
- **Altair** - 인터랙티브 그래프
- **관세청 수출입통계 Open API**
- **Pandas, Requests** - 데이터 처리 및 API 호출

---

## 📁 프로젝트 구조

```bash
.
├── app.py                          # Streamlit 메인 앱
├── data_loader.py                 # 관세청 API 데이터 수집 및 전처리
├── cleaned_hs_code_lookup.csv     # 품목명 ↔ HS코드 매핑 파일
├── .streamlit/
│   └── secrets.toml               # API Key 저장 (배포용)
├── requirements.txt               # 필요한 패키지 목록
├── README.md                      # 프로젝트 설명서
