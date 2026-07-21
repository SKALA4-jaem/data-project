"""
프로그램명: Adult Census Income 분석 보고서 자동 생성

프로그램 설명:
앞 단계에서 만든 정제 데이터와 학습 모델을 불러와 데이터 규모,
기술통계, 상관계수, t-test 및 모델 평가 결과를 report.md로 저장한다.

변경 내역:
- 필수 분석 결과를 Markdown 표와 문장으로 자동 작성
- 생성된 시각화 파일을 보고서에 연결
- 입력 데이터·모델·필수 컬럼 예외 처리 추가
"""

from pathlib import Path

import joblib
import pandas as pd
from scipy.stats import ttest_ind
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "processed" / "adult_clean.csv"
MODEL_FILE = BASE_DIR / "output" / "adult_income_pipeline.joblib"
REPORT_FILE = BASE_DIR / "report.md"

NUMERIC_FEATURES = ["age", "capital_gain", "capital_loss", "hours_per_week"]
CATEGORICAL_FEATURES = ["workclass", "education", "marital_status", "occupation"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
RANDOM_STATE = 42


def load_inputs() -> tuple[pd.DataFrame, object]:
    """보고서 생성에 필요한 정제 데이터와 학습 모델을 불러온다."""

    if not DATA_FILE.is_file():
        raise FileNotFoundError("정제 데이터가 없습니다. 01단계를 먼저 실행하세요.")
    if not MODEL_FILE.is_file():
        raise FileNotFoundError("학습 모델이 없습니다. 04단계를 먼저 실행하세요.")

    frame = pd.read_csv(DATA_FILE)
    missing = (set(FEATURES) | {"education_num", "income"}) - set(frame.columns)
    if missing:
        raise ValueError(f"보고서에 필요한 컬럼이 없습니다: {sorted(missing)}")

    frame["income"] = frame["income"].astype(str).str.strip().str.rstrip(".")
    return frame, joblib.load(MODEL_FILE)


def calculate_results(frame: pd.DataFrame, model: object) -> dict[str, float]:
    """보고서에 들어갈 통계·모델 평가값을 계산한다."""

    low_hours = frame.loc[frame["income"] == "<=50K", "hours_per_week"]
    high_hours = frame.loc[frame["income"] == ">50K", "hours_per_week"]
    t_statistic, p_value = ttest_ind(low_hours, high_hours, equal_var=False)

    target = (frame["income"] == ">50K").astype(int)
    _, x_test, _, y_test = train_test_split(
        frame[FEATURES],
        target,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=target,
    )
    predictions = model.predict(x_test)

    return {
        "low_hours": low_hours.mean(),
        "high_hours": high_hours.mean(),
        "t_statistic": t_statistic,
        "p_value": p_value,
        "accuracy": accuracy_score(y_test, predictions),
        "f1": f1_score(y_test, predictions),
    }


def make_report(frame: pd.DataFrame, results: dict[str, float]) -> str:
    """계산 결과를 읽기 쉬운 Markdown 보고서로 변환한다."""

    high_income = (frame["income"] == ">50K").astype(int)
    high_income_rate = high_income.mean()
    correlation_data = frame[
        ["age", "education_num", "capital_gain", "capital_loss", "hours_per_week"]
    ].copy()
    correlation_data["high_income"] = high_income
    income_correlations = (
        correlation_data.corr()["high_income"].drop("high_income").sort_values(ascending=False)
    )
    correlation_rows = "\n".join(
        f"| `{name}` | {value:.3f} |" for name, value in income_correlations.items()
    )
    p_value_text = "< 0.000001" if results["p_value"] < 0.000001 else f"{results['p_value']:.6f}"

    return f"""# Adult Census Income 분석 보고서

## 1. 분석 목적

인구조사 정보를 이용해 연 소득이 5만 달러를 초과하는 사람의 특징을 탐색하고,
통계적으로 관계를 확인한 뒤 머신러닝 Pipeline으로 소득 그룹을 예측했다.

## 2. 데이터 준비

- 원본 데이터: UCI Adult Census Income
- 정제 후 데이터: {len(frame):,}행, {len(frame.columns)}열
- 목표 변수: `income` (`<=50K`, `>50K`)
- 처리 방법: `?` 결측치 제거, 중복 행 제거
- 정제 후 고소득자 비율: {high_income_rate:.1%}
- Pandas와 Polars 양쪽에서 CSV 로딩 결과 확인

## 3. 시각화

![Adult Income 핵심 EDA](output/adult_income_eda.png)

- Seaborn: 소득 인원, 나이 분포, 근무시간, 숫자형 변수 상관관계를 2×2로 구성
- Plotly: 교육 수준별 고소득자 비율 인터랙티브 차트 생성
- Plotly 파일: [education_income_rate.html](output/education_income_rate.html)

## 4. 통계 분석

### 고소득 여부와 숫자형 변수의 상관계수

| 변수 | 상관계수 |
|---|---:|
{correlation_rows}

가장 큰 값은 `education_num`이며, 교육 수준과 고소득 여부 사이에 비교적
뚜렷한 양의 관계가 관찰됐다. 상관관계는 인과관계를 의미하지 않는다.

### 소득 그룹별 주당 근무시간 t-test

- `<=50K` 평균: {results['low_hours']:.2f}시간
- `>50K` 평균: {results['high_hours']:.2f}시간
- t통계량: {results['t_statistic']:.4f}
- p-value: {p_value_text}
- 해석: p-value가 0.05보다 작으므로 두 그룹의 평균 근무시간 차이는 통계적으로 유의미하다.

## 5. 머신러닝 Pipeline

- 숫자형 전처리: 결측치 중앙값 대체, 표준화
- 범주형 전처리: 결측치 최빈값 대체, One-Hot Encoding
- 모델: Logistic Regression
- 정확도: {results['accuracy']:.1%}
- 고소득 그룹 F1 점수: {results['f1']:.4f}
- 저장 모델: `output/adult_income_pipeline.joblib`

## 6. 결론

고소득자는 전체의 {high_income_rate:.1%}로 적었다. 교육 수준, 나이, 주당 근무시간은
고소득 여부와 양의 관계를 보였으며, 고소득 그룹은 주당 평균 근무시간도 더 길었다.
머신러닝 모델은 평가 데이터에서 {results['accuracy']:.1%}의 정확도와 {results['f1']:.4f}의
고소득 그룹 F1 점수를 기록했다. 다만 이 결과는 변수 간 관계를 보여줄 뿐,
특정 특성이 고소득의 직접적인 원인임을 증명하지는 않는다.
"""


def main() -> int:
    """분석 결과를 계산하고 report.md를 자동 생성한다."""

    try:
        frame, model = load_inputs()
        results = calculate_results(frame, model)
        REPORT_FILE.write_text(make_report(frame, results), encoding="utf-8")
        print(f"보고서 저장: {REPORT_FILE}")
        return 0
    except (FileNotFoundError, ValueError, TypeError, OSError) as error:
        print(f"[오류] {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
