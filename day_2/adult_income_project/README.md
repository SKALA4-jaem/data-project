# Adult Census Income 분석 프로젝트

인구조사 데이터를 이용해 **연 소득 5만 달러 초과 여부와 관련된 특징을 분석하고,
새로운 사람의 소득 그룹을 예측하는 머신러닝 모델을 만든 프로젝트**입니다.

## 프로젝트에서 한 일

1. **데이터 준비**: Pandas와 Polars로 데이터를 읽고 크기를 비교했습니다.
   결측치와 중복 행을 제거해 정제 데이터를 만들었습니다.
2. **시각화**: Seaborn으로 소득 인원·나이 분포·근무시간·상관관계 정적 차트를,
   Plotly로 교육 수준별 고소득자 비율 인터랙티브 차트를 만들었습니다.
3. **통계 분석**: 기술통계와 상관계수를 계산하고, 소득 그룹의 평균 근무시간을
   독립표본 t-test로 비교했습니다.
4. **머신러닝**: 전처리와 Logistic Regression을 Pipeline으로 묶어 학습·평가하고
   모델을 joblib 파일로 저장했습니다.
5. **자동화**: 주요 결과를 `report.md`로 자동 생성하도록 구성했습니다.

## 실행 순서

가상환경이 활성화된 프로젝트 폴더에서 다음 파일을 순서대로 실행합니다.

```bash
python 01_data_preparation.py
python 02_visualization.py
python 03_statistical_tests.py
python 04_model_pipeline.py
python 05_generate_report.py
```

`02_visualization.py` 실행 중 나타나는 그래프 창을 닫으면 Plotly 파일 저장이 계속됩니다.

## 핵심 결과

- 정제 데이터: **30,139행**
- 소득 5만 달러 초과 비율: **24.9%**
- 평균 주당 근무시간: 저소득 그룹 **39.35시간**, 고소득 그룹 **45.71시간**
- t-test: **p < 0.000001**, 두 그룹의 평균 근무시간 차이가 통계적으로 유의미함
- 고소득 여부와 가장 큰 상관계수: `education_num` **0.335**
- 머신러닝 정확도: **80.5%**
- 고소득 그룹 F1 점수: **0.6778**

## 프로젝트 결론

고소득자는 전체 데이터의 약 4분의 1이었습니다. 교육 수준, 나이, 주당 근무시간은
고소득 여부와 양의 관계를 보였고, 고소득 그룹의 평균 근무시간은 더 길었습니다.
머신러닝 모델은 평가 데이터에서 80.5%의 정확도를 기록했습니다.

다만 이 분석은 변수들이 소득과 **관련되어 있음**을 보여주는 것이며,
특정 변수가 고소득의 직접적인 원인이라는 뜻은 아닙니다.

## 파일 구성

| 파일 | 역할 |
|---|---|
| `01_data_preparation.py` | 데이터 로딩·Pandas/Polars 비교·정제·기본 EDA |
| `02_visualization.py` | Seaborn 및 Plotly 시각화 |
| `03_statistical_tests.py` | 기술통계·상관계수·t-test·카이제곱 검정 |
| `04_model_pipeline.py` | Pipeline 학습·평가·모델 저장 |
| `05_generate_report.py` | `report.md` 자동 생성 |
| `data/processed/adult_clean.csv` | 정제 데이터 |
| `output/adult_income_eda.png` | 정적 시각화 |
| `output/education_income_rate.html` | 인터랙티브 시각화 |
| `output/adult_income_pipeline.joblib` | 학습된 Pipeline |
| `report.md` | 자동 생성 분석 보고서 |

## 필요 라이브러리

```text
pandas, polars, matplotlib, seaborn, plotly, scipy, scikit-learn, joblib
```
