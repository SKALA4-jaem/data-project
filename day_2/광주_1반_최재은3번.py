"""
프로그램명: 실습 3 - Pandas EDA·Polars Lazy·DuckDB SQL 비교
작성자: 최재은

프로그램 설명:
이해관계자가 도구별 결과와 성능을 공정하게 비교할 수 있도록 sales_100k.csv를
Pandas, Polars Lazy API, DuckDB SQL로 동일하게 집계한다. Pandas로 기초
EDA와 IQR 이상치 제거를 수행하고, region·category별 amount의 합계·평균·
건수를 내림차순으로 출력한다. 마지막에는 세 도구를 동일한 반복 횟수로
측정해 실행 시간을 공정하게 비교한다.

변경 내역:
- 4단계(Pandas EDA/IQR, named aggregation, Polars Lazy, DuckDB SQL) 구현
- df.info(), 결측치 수, IQR 제거 전·후 행 수 출력 추가
- region·category별 total·mean·count named aggregation 및 total 내림차순 추가
- Polars scan_csv→filter→group_by→agg→sort→collect 체인 적용
- DuckDB SQL GROUP BY 결과를 DataFrame으로 변환
- timeit의 number를 세 도구 모두 10회로 통일한 성능 비교 추가
- 파일·필수 컬럼·숫자 타입·빈 데이터·외부 라이브러리 예외 처리 추가
- Pandas 3.0.3·Polars 1.42.1·DuckDB 1.5.4 호환성 검증
"""

from __future__ import annotations

import sys
import timeit
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

try:
    import duckdb
    import pandas as pd
    import polars as pl
except ImportError as error:
    missing_package = getattr(error, "name", "필요 패키지")
    raise SystemExit(
        f"[오류] {missing_package} 패키지가 필요합니다. "
        "'pip install pandas polars duckdb'로 설치해 주세요."
    ) from error


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "sales_100k.csv"
REQUIRED_COLUMNS = {"region", "category", "amount"}
BENCHMARK_REPEAT = 10


@dataclass(frozen=True)
class IQRBounds:
    """IQR 방법으로 계산한 amount의 정상 범위를 보관한다."""

    lower: float
    upper: float


def print_section(title: str) -> None:
    """실습 단계를 이해관계자가 구분하기 쉽게 출력한다."""

    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")


def validate_columns(columns: list[str], source: str) -> None:
    """CSV에 region, category, amount 필수 컬럼이 있는지 검증한다."""

    missing = REQUIRED_COLUMNS - set(columns)
    if missing:
        raise ValueError(
            f"{source}에 필수 컬럼이 없습니다: {sorted(missing)}"
        )


def load_pandas(path: Path, *, show_eda: bool = False) -> pd.DataFrame:
    """CSV를 Pandas로 읽고 필수 컬럼과 amount 숫자 타입을 검증한다."""

    if not path.is_file():
        raise FileNotFoundError(f"데이터 파일을 찾을 수 없습니다: {path}")

    try:
        frame = pd.read_csv(path)
    except (OSError, UnicodeError, pd.errors.ParserError) as error:
        raise ValueError(f"CSV를 읽을 수 없습니다: {error}") from error

    if frame.empty:
        raise ValueError("CSV에 처리할 데이터가 없습니다.")

    validate_columns(frame.columns.tolist(), path.name)
    numeric_amount = pd.to_numeric(frame["amount"], errors="coerce")
    invalid_amount = frame["amount"].notna() & numeric_amount.isna()
    if invalid_amount.any():
        rows = (frame.index[invalid_amount] + 2).tolist()[:5]
        raise ValueError(f"amount에 숫자가 아닌 값이 있습니다. CSV 행: {rows}")

    frame["amount"] = numeric_amount
    if show_eda:
        frame.info()
        print("\n[컬럼별 결측치 수]")
        print(frame.isnull().sum().to_string())
    return frame


def calculate_iqr_bounds(frame: pd.DataFrame) -> IQRBounds:
    """amount의 Q1·1.5·IQR 공식으로 이상치 판정 범위를 계산한다."""

    amounts = frame["amount"].dropna()
    if amounts.empty:
        raise ValueError("amount 컬럼에 유효한 숫자가 없습니다.")

    q1, q3 = amounts.quantile([0.25, 0.75])
    iqr = q3 - q1
    return IQRBounds(q1 - 1.5 * iqr, q3 + 1.5 * iqr)


def clean_pandas(frame: pd.DataFrame, bounds: IQRBounds) -> pd.DataFrame:
    """region·category·amount 결측치와 IQR 범위 밖 amount 행을 제거한다."""

    complete = frame.dropna(subset=list(REQUIRED_COLUMNS)).copy()
    return complete.loc[
        complete["amount"].between(bounds.lower, bounds.upper)
    ].copy()


def pandas_aggregate(frame: pd.DataFrame) -> pd.DataFrame:
    """Pandas named aggregation으로 지역·카테고리별 집계를 반환한다."""

    return (
        frame.groupby(["region", "category"], as_index=False)
        .agg(
            total=("amount", "sum"),
            mean=("amount", "mean"),
            count=("amount", "count"),
        )
        .sort_values("total", ascending=False, ignore_index=True)
    )


def polars_aggregate(path: Path, bounds: IQRBounds) -> pl.DataFrame:
    """Polars Lazy 체인으로 동일한 정제·집계를 실행한다."""

    try:
        lazy_frame = pl.scan_csv(
            path, schema_overrides={"amount": pl.Float64}
        )
        validate_columns(lazy_frame.collect_schema().names(), path.name)
        return (
            lazy_frame
            .filter(
                pl.col("region").is_not_null()
                & pl.col("category").is_not_null()
                & pl.col("amount").is_not_null()
                & pl.col("amount").is_between(bounds.lower, bounds.upper)
            )
            .group_by(["region", "category"])
            .agg(
                pl.col("amount").sum().alias("total"),
                pl.col("amount").mean().alias("mean"),
                pl.col("amount").count().alias("count"),
            )
            .sort("total", descending=True)
            .collect()
        )
    except (pl.exceptions.PolarsError, OSError) as error:
        raise ValueError(f"Polars 집계에 실패했습니다: {error}") from error


def duckdb_aggregate(path: Path, bounds: IQRBounds) -> pd.DataFrame:
    """DuckDB SQL로 동일한 정제·GROUP BY를 수행해 Pandas로 반환한다."""

    query = """
        SELECT
            region,
            category,
            SUM(amount) AS total,
            AVG(amount) AS mean,
            COUNT(amount) AS count
        FROM read_csv_auto(?, types = {'amount': 'DOUBLE'})
        WHERE region IS NOT NULL
          AND category IS NOT NULL
          AND amount IS NOT NULL
          AND amount BETWEEN ? AND ?
        GROUP BY region, category
        ORDER BY total DESC
    """
    try:
        return duckdb.execute(
            query, [str(path), bounds.lower, bounds.upper]
        ).df()
    except duckdb.Error as error:
        raise ValueError(f"DuckDB SQL 집계에 실패했습니다: {error}") from error


def benchmark(label: str, operation: Callable[[], object]) -> float:
    """동일한 반복 횟수로 함수의 평균 실행 시간을 측정한다."""

    elapsed = timeit.timeit(operation, number=BENCHMARK_REPEAT)
    average = elapsed / BENCHMARK_REPEAT
    print(f"{label:<8}: {average:.6f}초 (평균, {BENCHMARK_REPEAT}회 반복)")
    return average


def main() -> int:
    """4단계 실습, 체크포인트 검증, 성능 비교를 순서대로 실행한다."""

    try:
        print_section("1) Pandas EDA - 기초 탐색 + IQR 이상치 처리")
        raw = load_pandas(DATA_FILE, show_eda=True)
        bounds = calculate_iqr_bounds(raw)
        clean = clean_pandas(raw, bounds)
        print(f"\nIQR 정상 범위: {bounds.lower:,.2f} ~ {bounds.upper:,.2f}")
        print(f"제거 전 행 수: {len(raw):,}")
        print(f"제거 후 행 수: {len(clean):,}")
        print(f"제거된 행 수: {len(raw) - len(clean):,}")

        print_section("2) Pandas groupby - named aggregation")
        pandas_result = pandas_aggregate(clean)
        print(pandas_result.to_string(index=False))

        print_section("3) Polars Lazy API - 동일 집계")
        polars_result = polars_aggregate(DATA_FILE, bounds)
        print(polars_result)

        print_section("4) DuckDB SQL - 동일 집계")
        duckdb_result = duckdb_aggregate(DATA_FILE, bounds)
        print(duckdb_result.to_string(index=False))

        print_section("Checkpoint - 동일 반복 횟수 성능 비교")
        benchmark(
            "Pandas",
            lambda: pandas_aggregate(clean_pandas(load_pandas(DATA_FILE), bounds)),
        )
        benchmark("Polars", lambda: polars_aggregate(DATA_FILE, bounds))
        benchmark("DuckDB", lambda: duckdb_aggregate(DATA_FILE, bounds))
        print("\n모든 Checkpoint를 통과했습니다.")
        return 0

    except (FileNotFoundError, ValueError) as error:
        print(f"[오류] {error}", file=sys.stderr)
        return 1
    except Exception as error:  # 예상하지 못한 실행 오류도 사용자에게 안내한다.
        print(f"[오류] 예상하지 못한 문제가 발생했습니다: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
