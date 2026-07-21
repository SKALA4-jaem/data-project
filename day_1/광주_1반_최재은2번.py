"""
프로그램명: 실습 2 - 파일 I/O, 예외 처리, Pydantic 검증 파이프라인
작성자: 최재은

프로그램 설명:
Python_Practice1_Data.json에서 7건을 가져와 검증 실습용 CSV를 만든다.
CSV의 정상 4건과 의도적으로 잘못 구성한 3건을 SalesRecord로 검증하고,
성공 데이터는 CSV로, 실패 데이터와 오류 내용은 JSON으로 저장한다.

변경 내역:
- 제공 JSON을 활용한 7행 실습 CSV 생성 기능 추가
- safe_load_csv()에 파일 예외 처리와 finally 로깅 적용
- Pydantic v2의 Field, StringConstraints, model_dump() 사용
- 검증 성공(valid)과 실패(errors) 결과 분리
- CSV/JSON 저장 및 재로딩 assert 추가
"""

import csv
import json
import logging
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, ValidationError


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "Python_Practice1_Data.json"
INPUT_FILE = BASE_DIR / "sales_records.csv"
VALID_FILE = BASE_DIR / "valid_sales.csv"
ERROR_FILE = BASE_DIR / "validation_errors.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class SalesRecord(BaseModel):
    """매출 데이터 한 건의 필수 항목과 값 범위를 검증한다."""

    month: NonEmptyText
    region: NonEmptyText
    amount: float = Field(gt=0)
    category: str | None = None


def load_source_json(path: Path) -> list[dict]:
    """제공 JSON에서 매출 데이터 리스트를 읽는다.

    제공 파일은 확장자는 JSON이지만 ``sales = [...]`` 형태이므로 대입문
    접두사를 제거하고 배열 부분을 JSON으로 해석한다.
    """

    try:
        text = path.read_text(encoding="utf-8").strip()
        if text.startswith("sales") and "=" in text:
            text = text.split("=", maxsplit=1)[1].strip()

        source_data = json.loads(text)
        if not isinstance(source_data, list):
            raise TypeError("최상위 데이터는 리스트여야 합니다.")
        if not all(isinstance(row, dict) for row in source_data):
            raise TypeError("각 레코드는 딕셔너리여야 합니다.")

        logger.info("제공 JSON 데이터 %d건을 읽었습니다.", len(source_data))
        return source_data
    except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError) as error:
        logger.error("제공 JSON을 읽을 수 없습니다: %s", error)
        raise


def create_practice_csv(source_data: list[dict], path: Path) -> None:
    """원본 데이터로 정상 4건과 검증 실패 3건인 실습 CSV를 만든다."""

    if len(source_data) < 7:
        raise ValueError("실습 CSV를 만들려면 원본 데이터가 7건 이상 필요합니다.")

    practice_rows = [dict(row) for row in source_data[:7]]

    # Pydantic 검증 실패 사례: region 공백, amount 0, month 공백
    practice_rows[4]["region"] = ""
    practice_rows[5]["amount"] = 0
    practice_rows[6]["month"] = ""

    fieldnames = ["region", "month", "amount", "category"]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(practice_rows)

    logger.info("검증 실습용 CSV 7건을 생성했습니다: %s", path)


def safe_load_csv(path: Path) -> list[dict] | None:
    """CSV를 안전하게 읽어 딕셔너리 리스트로 반환한다.

    파일이 없으면 logger.error를 남기고 None을 반환하며, 성공하면
    dict 리스트를 반환한다. 성공 여부와 무관하게 finally를 실행한다.
    """

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            rows = list(csv.DictReader(file))
        logger.info("CSV 로딩 성공: %s (%d건)", path, len(rows))
        return rows
    except FileNotFoundError:
        logger.error("파일을 찾을 수 없습니다: %s", path)
        return None
    except (OSError, csv.Error) as error:
        logger.error("CSV를 읽을 수 없습니다: %s", error)
        return None
    finally:
        logger.info("로딩 종료: %s", path.name)


def validate_records(
    raw_data: list[dict],
) -> tuple[list[SalesRecord], list[dict]]:
    """원본 레코드를 검증하여 성공 목록과 오류 목록으로 분리한다."""

    valid: list[SalesRecord] = []
    errors: list[dict] = []

    for row_number, row in enumerate(raw_data, start=1):
        try:
            valid.append(SalesRecord.model_validate(row))
        except ValidationError as error:
            error_detail = {
                "row": row_number,
                "data": row,
                "error": error.errors(),
            }
            errors.append(error_detail)
            logger.error(
                "%d번째 행 검증 실패:\n%s",
                row_number,
                error,
            )

    # 모든 원본 행이 valid 또는 errors 중 정확히 한 곳에 들어갔는지 확인한다.
    assert len(valid) + len(errors) == len(raw_data)
    return valid, errors


def save_valid_csv(records: list[SalesRecord], path: Path) -> None:
    """검증을 통과한 레코드를 Pydantic model_dump()로 변환해 저장한다."""

    fieldnames = list(SalesRecord.model_fields)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(record.model_dump() for record in records)

    logger.info("정상 데이터 %d건을 CSV로 저장했습니다: %s", len(records), path)


def save_errors_json(errors: list[dict], path: Path) -> None:
    """검증 실패 행과 상세 오류를 한글이 깨지지 않는 JSON으로 저장한다."""

    with path.open("w", encoding="utf-8") as file:
        json.dump(errors, file, ensure_ascii=False, indent=2)

    logger.info("오류 데이터 %d건을 JSON으로 저장했습니다: %s", len(errors), path)


def main() -> None:
    """읽기, 검증, 저장, 재로딩으로 이어지는 전체 파이프라인을 실행한다."""

    source_data = load_source_json(DATA_FILE)
    create_practice_csv(source_data, INPUT_FILE)

    raw_data = safe_load_csv(INPUT_FILE)
    assert raw_data is not None, "실습 CSV 로딩에 실패했습니다."

    # 없는 파일은 None을 반환해야 한다는 Checkpoint를 확인한다.
    assert safe_load_csv(BASE_DIR / "no_such_file.csv") is None

    valid, errors = validate_records(raw_data)
    print(f"검증 결과: valid {len(valid)}건 / errors {len(errors)}건")

    assert len(valid) == 4
    assert len(errors) == 3

    save_valid_csv(valid, VALID_FILE)
    save_errors_json(errors, ERROR_FILE)

    reloaded = safe_load_csv(VALID_FILE)
    assert reloaded is not None
    assert len(reloaded) == 4

    print(f"재로딩 결과: {len(reloaded)}건")
    print("모든 Checkpoint를 통과했습니다.")


if __name__ == "__main__":
    main()
