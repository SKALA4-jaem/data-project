"""
프로그램명: Adult Census Income 통계 검정

프로그램 설명:
정제된 Adult 데이터를 이용해 소득 그룹별 주당 근무시간 차이는
독립표본 t-검정으로, 교육 수준과 소득 그룹의 관련성은 카이제곱
독립성 검정으로 확인한다. p-value를 기준으로 결과를 쉽게 해석한다.

변경 내역:
- 숫자형 주요 변수의 기술통계와 상관계수 출력 추가
- 소득 그룹별 주당 평균 근무시간과 Welch t-검정 추가
- 교육 수준·소득 그룹 교차표와 카이제곱 검정 추가
- 검정 결과의 유의미 여부 자동 해석 추가
- 입력 파일·필수 열·표본 부족에 대한 예외 처리 추가
"""

from pathlib import Path

import pandas as pd
from scipy.stats import chi2_contingency, ttest_ind


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "processed" / "adult_clean.csv"
NUMERIC_COLUMNS = [
    "age",
    "education_num",
    "capital_gain",
    "capital_loss",
    "hours_per_week",
]
REQUIRED_COLUMNS = set(NUMERIC_COLUMNS) | {"education", "income"}
INCOME_ORDER = ["<=50K", ">50K"]
SIGNIFICANCE_LEVEL = 0.05


def load_clean_data(path: Path) -> pd.DataFrame:
    """정제 데이터를 읽고 통계 검정에 필요한 값을 확인한다."""

    if not path.is_file():
        raise FileNotFoundError(
            "정제 데이터가 없습니다. 01_data_preparation.py를 먼저 실행하세요."
        )

    frame = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"필수 컬럼이 없습니다: {sorted(missing)}")
    if frame.empty:
        raise ValueError("통계 검정에 사용할 데이터가 없습니다.")

    frame["income"] = frame["income"].astype(str).str.strip().str.rstrip(".")
    unknown = set(frame["income"].dropna().unique()) - set(INCOME_ORDER)
    if unknown:
        raise ValueError(f"알 수 없는 income 값입니다: {sorted(unknown)}")

    return frame


def interpret_p_value(p_value: float) -> str:
    """p-value를 0.05와 비교해 검정 결과를 쉬운 문장으로 반환한다."""

    if p_value < SIGNIFICANCE_LEVEL:
        return "통계적으로 유의미합니다(p < 0.05). 우연한 차이로 보기 어렵습니다."
    return "통계적으로 유의미하지 않습니다(p >= 0.05). 우연한 차이일 수 있습니다."


def format_p_value(p_value: float) -> str:
    """매우 작은 p-value가 단순히 0으로 오해되지 않도록 표시한다."""

    if p_value < 0.000001:
        return "< 0.000001"
    return f"{p_value:.6f}"


def print_descriptive_statistics(frame: pd.DataFrame) -> None:
    """주요 숫자형 변수의 기술통계와 고소득 여부를 포함한 상관계수를 출력한다."""

    analysis = frame[NUMERIC_COLUMNS].copy()
    analysis["high_income"] = (frame["income"] == ">50K").astype(int)

    statistics = analysis.describe().loc[["mean", "std", "25%", "50%", "75%"]]
    correlations = analysis.corr(numeric_only=True)

    print("\n" + "=" * 72)
    print("1) 기술통계와 변수 간 상관계수")
    print("=" * 72)
    print("[기술통계: 평균·표준편차·분위수]")
    print(statistics.round(2).to_string())
    print("\n[상관계수: -1부터 1 사이, 절댓값이 클수록 관계가 강함]")
    print(correlations.round(3).to_string())
    print("\n[고소득 여부와의 상관계수]")
    print(
        correlations["high_income"]
        .drop("high_income")
        .sort_values(ascending=False)
        .round(3)
        .to_string()
    )


def test_working_hours(frame: pd.DataFrame) -> None:
    """두 소득 그룹의 평균 주당 근무시간 차이를 Welch t-검정한다."""

    low_income = frame.loc[frame["income"] == "<=50K", "hours_per_week"].dropna()
    high_income = frame.loc[frame["income"] == ">50K", "hours_per_week"].dropna()

    if len(low_income) < 2 or len(high_income) < 2:
        raise ValueError("t-검정에는 각 소득 그룹당 최소 2개의 값이 필요합니다.")

    t_statistic, p_value = ttest_ind(
        low_income,
        high_income,
        equal_var=False,
    )

    print("\n" + "=" * 72)
    print("2) 소득 그룹별 주당 근무시간: 독립표본 t-검정")
    print("=" * 72)
    print(f"<=50K 평균: {low_income.mean():.2f}시간 (n={len(low_income):,})")
    print(f">50K  평균: {high_income.mean():.2f}시간 (n={len(high_income):,})")
    print(f"평균 차이 : {high_income.mean() - low_income.mean():.2f}시간")
    print(f"t통계량   : {t_statistic:.4f}")
    print(f"p-value   : {format_p_value(p_value)}")
    print(f"해석      : {interpret_p_value(p_value)}")


def test_education_and_income(frame: pd.DataFrame) -> None:
    """교육 수준과 소득 그룹의 관련성을 카이제곱 검정한다."""

    contingency_table = pd.crosstab(frame["education"], frame["income"])
    if contingency_table.shape[0] < 2 or contingency_table.shape[1] < 2:
        raise ValueError("카이제곱 검정에는 각 변수에 최소 2개 범주가 필요합니다.")

    chi2_statistic, p_value, degrees_of_freedom, expected = chi2_contingency(
        contingency_table
    )

    if (expected < 5).any():
        print("[주의] 기대빈도가 5보다 작은 칸이 있어 결과 해석에 주의가 필요합니다.")

    print("\n" + "=" * 72)
    print("3) 교육 수준과 소득 그룹: 카이제곱 독립성 검정")
    print("=" * 72)
    print("[교차표: 실제 인원]")
    print(contingency_table.to_string())
    print(f"\n카이제곱 통계량: {chi2_statistic:.4f}")
    print(f"자유도          : {degrees_of_freedom}")
    print(f"p-value         : {format_p_value(p_value)}")
    print(f"해석            : {interpret_p_value(p_value)}")


def main() -> int:
    """데이터를 불러와 두 통계 검정을 순서대로 실행한다."""

    try:
        frame = load_clean_data(DATA_FILE)
        print(f"통계 검정 데이터: {len(frame):,}행")
        print_descriptive_statistics(frame)
        test_working_hours(frame)
        test_education_and_income(frame)
        print("\n3단계 통계 검정이 완료됐습니다.")
        return 0
    except (FileNotFoundError, ValueError, TypeError, OSError) as error:
        print(f"[오류] {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
