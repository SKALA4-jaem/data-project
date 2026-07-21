"""
프로그램명: 실습 4 - 시각화·통계 검정·sklearn Pipeline
작성자: 최재은

프로그램 설명:
실습 3의 sales_100k.csv와 IQR 정제 방법을 이어받아 EDA 시각화 4종을
하나의 2x2 Figure로 저장한다. 서울·부산 매출의 t-test와 지역·카테고리
카이제곱 검정을 수행해 p-value와 해석을 출력한다. 수치·범주형 전처리와
Ridge 회귀를 sklearn Pipeline으로 묶어 학습·예측·평가한 후 joblib 파일로
저장·재로딩한다. 마지막으로 지역·카테고리별 총매출을 Plotly HTML로
저장해 이해관계자가 결과를 쉽게 탐색하도록 한다.

변경 내역:
- 실습 3과 동일한 IQR 공식으로 입력 DataFrame 정제
- 히스토그램+KDE·박스플롯·월별 라인·상관 히트맵을 2x2로 통합
- Welch t-test와 카이제곱 검정의 통계량·p-value·유의성 해석 출력
- ColumnTransformer + Pipeline으로 전처리·Ridge 회귀 통합
- fit·predict·score 실행 및 joblib 저장·재로딩 검증
- Plotly 인터랙티브 막대 차트 HTML 저장
- 파일·필수 컬럼·빈 데이터·숫자·날짜·산출물 오류 처리
"""

from __future__ import annotations

import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import seaborn as sns
from matplotlib import font_manager
from scipy import stats
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "sales_100k.csv"
EDA_IMAGE_FILE = BASE_DIR / "practice4_eda.png"
MODEL_FILE = BASE_DIR / "practice4_model.joblib"
PLOTLY_FILE = BASE_DIR / "practice4_sales.html"
ALPHA = 0.05
RANDOM_STATE = 42
VISUAL_SAMPLE_SIZE = 50_000
MODEL_SAMPLE_SIZE = 100_000

NUMERIC_FEATURES = ["quantity", "unit_price", "customer_age"]
CATEGORICAL_FEATURES = [
    "region",
    "category",
    "payment_method",
    "customer_gender",
]
REQUIRED_COLUMNS = {
    "order_date",
    "amount",
    *NUMERIC_FEATURES,
    *CATEGORICAL_FEATURES,
}


def print_section(title: str) -> None:
    """이해관계자가 4단계 결과를 구분하기 쉽게 제목을 출력한다."""

    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")


def configure_plot_style() -> None:
    """macOS 한글 폰트가 있으면 설정하고, 없으면 기본 폰트를 사용한다."""

    font_path = Path("/System/Library/Fonts/AppleSDGothicNeo.ttc")
    font_name = "sans-serif"
    if font_path.is_file():
        font_name = font_manager.FontProperties(fname=font_path).get_name()

    sns.set_theme(style="whitegrid", font=font_name)
    plt.rcParams["axes.unicode_minus"] = False


def require_columns(frame: pd.DataFrame) -> None:
    """입력 데이터에 시각화·검정·모델링 필수 컬럼이 있는지 검증한다."""

    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"필수 컬럼이 없습니다: {sorted(missing)}")


def load_and_clean_data(path: Path) -> pd.DataFrame:
    """CSV를 읽고 실습 3과 동일한 IQR 방법으로 결측치·이상치를 제거한다."""

    if not path.is_file():
        raise FileNotFoundError(f"데이터 파일을 찾을 수 없습니다: {path}")

    try:
        frame = pd.read_csv(path)
    except (OSError, UnicodeError, pd.errors.ParserError) as error:
        raise ValueError(f"CSV를 읽을 수 없습니다: {error}") from error

    if frame.empty:
        raise ValueError("CSV에 처리할 데이터가 없습니다.")
    require_columns(frame)

    for column in ["amount", *NUMERIC_FEATURES]:
        numeric = pd.to_numeric(frame[column], errors="coerce")
        invalid = frame[column].notna() & numeric.isna()
        if invalid.any():
            rows = (frame.index[invalid] + 2).tolist()[:5]
            raise ValueError(f"{column}에 숫자가 아닌 값이 있습니다. CSV 행: {rows}")
        frame[column] = numeric

    frame["order_date"] = pd.to_datetime(frame["order_date"], errors="coerce")
    if frame["order_date"].notna().sum() == 0:
        raise ValueError("order_date에 올바른 날짜가 없습니다.")

    amounts = frame["amount"].dropna()
    if amounts.empty:
        raise ValueError("amount에 유효한 숫자가 없습니다.")

    q1, q3 = amounts.quantile([0.25, 0.75])
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    clean = frame.dropna(subset=sorted(REQUIRED_COLUMNS)).loc[
        lambda data: data["amount"].between(lower, upper)
    ].copy()

    if clean.empty:
        raise ValueError("결측치·이상치 제거 후 데이터가 없습니다.")

    print(f"원본: {len(frame):,}행 | 정제 후: {len(clean):,}행")
    print(f"IQR 정상 범위: {lower:,.2f} ~ {upper:,.2f}")
    return clean


def create_eda_visualizations(frame: pd.DataFrame, output: Path) -> None:
    """히스토그램·박스플롯·월별 라인·히트맵을 하나의 2x2 Figure로 저장한다."""

    sample_size = min(len(frame), VISUAL_SAMPLE_SIZE)
    plot_data = frame.sample(sample_size, random_state=RANDOM_STATE)
    monthly = (
        frame.assign(month=frame["order_date"].dt.to_period("M").astype(str))
        .groupby("month", as_index=False)
        .agg(total=("amount", "sum"))
        .sort_values("month")
    )
    correlations = frame[["amount", *NUMERIC_FEATURES]].corr()

    configure_plot_style()
    fig, axes = plt.subplots(2, 2, figsize=(16, 11))

    sns.histplot(plot_data, x="amount", kde=True, bins=40, ax=axes[0, 0])
    axes[0, 0].set_title("Amount Distribution (Histogram + KDE)")

    sns.boxplot(
        plot_data, x="region", y="amount", showfliers=False, ax=axes[0, 1]
    )
    axes[0, 1].set_title("Amount by Region (Boxplot)")
    axes[0, 1].tick_params(axis="x", rotation=30)

    axes[1, 0].plot(monthly["month"], monthly["total"], marker="o")
    axes[1, 0].set_title("Monthly Total Sales (Line)")
    axes[1, 0].tick_params(axis="x", rotation=45)
    axes[1, 0].grid(alpha=0.3)

    sns.heatmap(
        correlations,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        vmin=-1,
        vmax=1,
        ax=axes[1, 1],
    )
    axes[1, 1].set_title("Numeric Correlation Heatmap")

    fig.suptitle("Practice 4 - EDA Visualizations", fontsize=16)
    fig.tight_layout()
    fig.savefig(output, dpi=150, bbox_inches="tight")
    print("그래프 창을 닫으면 2단계 통계 검정이 계속됩니다.")
    plt.show()
    plt.close(fig)

    if not output.is_file():
        raise OSError(f"EDA 이미지 저장에 실패했습니다: {output}")
    print(f"2x2 EDA 이미지 저장: {output}")


def interpret_p_value(
    p_value: float,
    significant_message: str,
    not_significant_message: str,
) -> None:
    """p-value를 0.05와 비교해 검정에 맞는 자연어 해석을 출력한다."""

    if p_value < ALPHA:
        print(f"해석: p < {ALPHA}, {significant_message}")
    else:
        print(f"해석: p >= {ALPHA}, {not_significant_message}")


def run_statistical_tests(frame: pd.DataFrame) -> None:
    """서울·부산 매출 t-test와 지역·카테고리 카이제곱 독립성 검정을 수행한다."""

    seoul = frame.loc[frame["region"] == "서울", "amount"]
    busan = frame.loc[frame["region"] == "부산", "amount"]
    if seoul.empty or busan.empty:
        raise ValueError("서울 또는 부산 매출 데이터가 없어 t-test를 할 수 없습니다.")

    t_stat, t_p = stats.ttest_ind(seoul, busan, equal_var=False)
    print(f"Welch t-test: t={t_stat:.6f}, p-value={t_p:.6e}")
    interpret_p_value(
        float(t_p),
        "서울·부산의 평균 매출 차이가 통계적으로 유의합니다.",
        "서울·부산의 평균 매출 차이가 유의하다고 볼 증거가 부족합니다.",
    )

    table = pd.crosstab(frame["region"], frame["category"])
    if table.shape[0] < 2 or table.shape[1] < 2:
        raise ValueError("카이제곱 검정에는 각 변수가 2개 이상의 범주를 가져야 합니다.")

    chi2, chi_p, dof, _ = stats.chi2_contingency(table)
    print(f"카이제곱 검정: chi2={chi2:.6f}, dof={dof}, p-value={chi_p:.6e}")
    interpret_p_value(
        float(chi_p),
        "지역과 카테고리는 독립적이지 않으며 관련이 유의합니다.",
        "지역과 카테고리의 관련이 유의하다고 볼 증거가 부족합니다.",
    )


def train_save_pipeline(frame: pd.DataFrame, output: Path) -> None:
    """전처리와 Ridge를 Pipeline으로 묶어 fit·predict·score 후 저장·재로딩한다."""

    sample_size = min(len(frame), MODEL_SAMPLE_SIZE)
    model_data = frame.sample(sample_size, random_state=RANDOM_STATE)
    features = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    x = model_data[features]
    y = model_data["amount"]
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=RANDOM_STATE
    )

    preprocessor = ColumnTransformer(
        [
            ("num", StandardScaler(), NUMERIC_FEATURES),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore"),
                CATEGORICAL_FEATURES,
            ),
        ]
    )
    model = Pipeline(
        [
            ("preprocessor", preprocessor),
            ("regressor", Ridge(alpha=1.0)),
        ]
    )

    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    score = model.score(x_test, y_test)
    print(f"학습: {len(x_train):,}건 | 평가: {len(x_test):,}건")
    print(f"예측값 샘플 5개: {predictions[:5].round(2).tolist()}")
    print(f"R2 score: {score:.6f}")

    joblib.dump(model, output)
    loaded_model = joblib.load(output)
    reloaded_predictions = loaded_model.predict(x_test.iloc[:5])
    print(f"재로딩 예측 5개: {reloaded_predictions.round(2).tolist()}")
    if not output.is_file():
        raise OSError(f"모델 저장에 실패했습니다: {output}")
    print(f"Pipeline 모델 저장: {output}")


def save_plotly_chart(frame: pd.DataFrame, output: Path) -> None:
    """지역·카테고리별 총매출 막대 차트를 인터랙티브 HTML로 저장한다."""

    totals = (
        frame.groupby(["region", "category"], as_index=False)
        .agg(total=("amount", "sum"))
        .sort_values("total", ascending=False)
    )
    figure = px.bar(
        totals,
        x="region",
        y="total",
        color="category",
        barmode="group",
        hover_data={"total": ":,.0f"},
        title="Region and Category Total Sales",
        labels={"region": "Region", "total": "Total Sales", "category": "Category"},
    )
    figure.write_html(output, include_plotlyjs=True)
    if not output.is_file():
        raise OSError(f"Plotly HTML 저장에 실패했습니다: {output}")
    print(f"Plotly HTML 저장: {output}")


def main() -> int:
    """실습 3 연계 후 실습 4의 네 단계를 순서대로 실행한다."""

    try:
        clean = load_and_clean_data(DATA_FILE)

        print_section("1) EDA 시각화 4종 - 2x2 서브플롯")
        create_eda_visualizations(clean, EDA_IMAGE_FILE)

        print_section("2) 통계 검정 - t-test + 카이제곱")
        run_statistical_tests(clean)

        print_section("3) sklearn Pipeline - 학습·예측·평가·저장·재로딩")
        train_save_pipeline(clean, MODEL_FILE)

        print_section("4) Plotly 인터랙티브 차트 - HTML 저장")
        save_plotly_chart(clean, PLOTLY_FILE)

        print("\n모든 Checkpoint를 통과했습니다.")
        return 0
    except (FileNotFoundError, ValueError, OSError) as error:
        print(f"[오류] {error}", file=sys.stderr)
        return 1
    except Exception as error:  # 예상하지 못한 라이브러리·실행 오류도 안내한다.
        print(f"[오류] 예상하지 못한 문제가 발생했습니다: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
