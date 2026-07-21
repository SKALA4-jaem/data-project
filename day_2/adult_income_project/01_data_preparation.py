"""
프로그램명: Adult Census Income 데이터 준비 및 기초 EDA

프로그램 설명:
UCI Adult Census Income 데이터를 불러와 Pandas와 Polars의
로딩 결과를 비교한다. 결측치와 중복 데이터를 확인·처리하고,
정제된 데이터를 다음 시각화·통계·ML 단계에서 사용할 수 있도록 저장한다.

변경 내역:
- Adult Census Income 데이터 로딩
- Pandas·Polars 로딩 결과 비교
- 결측치·중복 데이터 확인 및 처리
- 정제 데이터 CSV 저장
"""

from pathlib import Path

import pandas as pd
import polars as pl


BASE_DIR = Path(__file__).resolve().parent
RAW_FILE = BASE_DIR / "data" / "raw" / "adult.csv"
CLEAN_FILE = BASE_DIR / "data" / "processed" / "adult_clean.csv"

DATA_URL = (
    "https://archive.ics.uci.edu/ml/"
    "machine-learning-databases/adult/adult.data"
)

COLUMNS = [
    "age",
    "workclass",
    "fnlwgt",
    "education",
    "education_num",
    "marital_status",
    "occupation",
    "relationship",
    "race",
    "sex",
    "capital_gain",
    "capital_loss",
    "hours_per_week",
    "native_country",
    "income",
]


def load_data() -> pd.DataFrame:
    """UCI 데이터를 Pandas로 내려받아 원본 CSV로 저장한다."""

    try:
        frame = pd.read_csv(
            DATA_URL,
            header=None,
            names=COLUMNS,
            na_values="?",
            skipinitialspace=True,
        )
    except Exception as error:
        raise RuntimeError(
            f"데이터를 불러오지 못했습니다: {error}"
        ) from error

    if frame.empty:
        raise ValueError("불러온 데이터가 비어 있습니다.")

    RAW_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    frame.to_csv(
        RAW_FILE,
        index=False,
        encoding="utf-8",
    )

    return frame


def compare_pandas_polars(
    pandas_frame: pd.DataFrame,
) -> None:
    """같은 CSV를 Pandas와 Polars로 읽어 크기와 컬럼을 비교한다."""

    polars_frame = pl.read_csv(
        RAW_FILE,
        null_values=[""],
    )

    print("\n[Pandas]")
    print(f"크기: {pandas_frame.shape}")
    print(f"컬럼 수: {len(pandas_frame.columns)}")

    print("\n[Polars]")
    print(f"크기: {polars_frame.shape}")
    print(f"컬럼 수: {len(polars_frame.columns)}")

    if pandas_frame.shape == polars_frame.shape:
        print("\nPandas와 Polars의 데이터 크기가 같습니다.")
    else:
        print("\n[주의] Pandas와 Polars의 데이터 크기가 다릅니다.")


def clean_data(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """결측치와 중복 데이터를 제거하고 정제 결과를 저장한다."""

    before_rows = len(frame)
    missing_before = frame.isna().sum()
    duplicate_count = frame.duplicated().sum()

    print("\n[컬럼별 결측치]")
    print(missing_before.to_string())

    print(f"\n중복 행: {duplicate_count:,}개")

    clean = (
        frame.dropna()
        .drop_duplicates()
        .reset_index(drop=True)
    )

    CLEAN_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    clean.to_csv(
        CLEAN_FILE,
        index=False,
        encoding="utf-8",
    )

    print(f"\n정제 전: {before_rows:,}행")
    print(f"정제 후: {len(clean):,}행")
    print(f"제거된 행: {before_rows - len(clean):,}행")
    print(f"정제 데이터 저장: {CLEAN_FILE}")

    return clean


def print_basic_eda(
    frame: pd.DataFrame,
) -> None:
    """정제 데이터의 기본 구조와 기술통계를 출력한다."""

    print("\n[데이터 상위 5행]")
    print(frame.head().to_string(index=False))

    print("\n[데이터 정보]")
    frame.info()

    print("\n[숫자형 기술통계]")
    print(frame.describe().round(2).to_string())

    print("\n[소득 그룹별 인원]")
    print(frame["income"].value_counts().to_string())


def main() -> int:
    """데이터 로딩·비교·정제·EDA를 순서대로 실행한다."""

    try:
        raw = load_data()
        compare_pandas_polars(raw)

        clean = clean_data(raw)
        print_basic_eda(clean)

        print("\n1단계 데이터 준비가 완료됐습니다.")
        return 0

    except (
        FileNotFoundError,
        ValueError,
        RuntimeError,
        OSError,
    ) as error:
        print(f"[오류] {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())