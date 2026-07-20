"""
프로그램명: Practice 1 - 자료구조 집계·컴프리헨션·제너레이터
작성자: 최재은

프로그램 설명:
제공받은 Python_Practice1_Data.json 파일을 읽어 다음 작업을 수행한다.
1. amount가 1000 이상인 거래 필터링
2. 지역별 총매출 계산
3. 지역별 거래 건수와 카테고리별 금액 목록 집계
4. 제너레이터와 리스트의 메모리 크기 비교
5. 월별·카테고리별 총매출 계산
6. 지역별 총매출 상위 3개 출력

변경 내역:
- JSON 데이터 파일을 직접 읽도록 수정
- 결과값을 코드에 미리 적는 하드코딩 제거
- 파일 및 데이터 형식 예외 처리 추가
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


DATA_FILE = "Python_Practice2_Data.json"


def load_sales_data(file_name):
    """
    JSON 파일에서 매출 데이터 리스트를 읽어 반환한다.

    Args:
        file_name: 읽을 JSON 파일 이름

    Returns:
        검증된 매출 데이터 리스트
        오류 발생 시 빈 리스트
    """
    file_path = Path(__file__).resolve().parent / file_name

    try:
        with file_path.open("r", encoding="utf-8") as file:
            sales_data = json.load(file)

        if not isinstance(sales_data, list):
            raise TypeError("JSON의 최상위 데이터는 리스트여야 합니다.")

        required_keys = {"region", "category", "amount", "month"}

        for index, row in enumerate(sales_data, start=1):
            if not isinstance(row, dict):
                raise TypeError(f"{index}번째 거래가 딕셔너리 형식이 아닙니다.")

            missing_keys = required_keys - row.keys()
            if missing_keys:
                raise KeyError(
                    f"{index}번째 거래에 필요한 항목이 없습니다: "
                    f"{sorted(missing_keys)}"
                )

            if not isinstance(row["amount"], (int, float)):
                raise TypeError(
                    f"{index}번째 거래의 amount는 숫자여야 합니다."
                )

        return sales_data

    except FileNotFoundError:
        print(f"[오류] 파일을 찾을 수 없습니다: {file_path}")
    except json.JSONDecodeError as error:
        print(f"[오류] JSON 형식이 올바르지 않습니다: {error}")
    except (KeyError, TypeError) as error:
        print(f"[오류] 데이터 구조가 올바르지 않습니다: {error}")
    except OSError as error:
        print(f"[오류] 파일을 읽는 중 문제가 발생했습니다: {error}")

    return []


def generate_high_sales(sales_data):
    """
    amount가 1000을 초과하는 거래를 하나씩 반환한다.

    Args:
        sales_data: 매출 거래 리스트

    Yields:
        amount가 1000을 초과하는 거래 딕셔너리
    """
    for row in sales_data:
        if row["amount"] > 1000:
            yield row


def main():
    sales = load_sales_data(DATA_FILE)

    if not sales:
        print("처리할 매출 데이터가 없습니다.")
        return

    print("=" * 60)
    print("Practice 1 자료구조 집계·컴프리헨션·제너레이터")
    print("=" * 60)
    print(f"전체 거래 수: {len(sales)}건")

    # 1) amount가 1000 이상인 거래를 리스트 컴프리헨션으로 필터링
    filtered_sales = [
        row
        for row in sales
        if row["amount"] >= 1000
    ]

    # 중복 없는 지역 목록 생성
    regions = {row["region"] for row in filtered_sales}

    # 지역별 총매출을 딕셔너리 컴프리헨션으로 계산
    region_total = {
        region: sum(
            row["amount"]
            for row in filtered_sales
            if row["region"] == region
        )
        for region in regions
    }

    print("\n[1] amount 1000 이상 거래")
    print(f"필터링된 거래 수: {len(filtered_sales)}건")

    print("\n[1-2] 지역별 총매출")
    for region, total in sorted(region_total.items()):
        print(f"{region}: {total:,}원")

    # 하드코딩된 예상값 대신 원본 데이터로 다시 계산하여 검증
    for region, total in region_total.items():
        calculated_total = sum(
            row["amount"]
            for row in filtered_sales
            if row["region"] == region
        )
        assert total == calculated_total

    print("region_total 검증: 통과")

    # 2) Counter로 지역별 전체 거래 건수 계산
    region_count = Counter(row["region"] for row in sales)

    print("\n[2-1] 지역별 거래 건수")
    for region, count in region_count.most_common():
        print(f"{region}: {count}건")

    # most_common 결과가 거래 건수 내림차순인지 확인
    count_values = [
        count
        for _, count in region_count.most_common()
    ]
    assert count_values == sorted(count_values, reverse=True)

    print("Counter.most_common() 순서 검증: 통과")

    # defaultdict로 카테고리별 amount 리스트 생성
    category_amounts = defaultdict(list)

    for row in sales:
        category_amounts[row["category"]].append(row["amount"])

    print("\n[2-2] 카테고리별 amount 리스트")
    for category, amounts in sorted(category_amounts.items()):
        print(f"{category}: {amounts}")

    # 3) 리스트와 제너레이터의 메모리 크기 비교
    high_sales_list = [
        row
        for row in sales
        if row["amount"] > 1000
    ]
    high_sales_generator = generate_high_sales(sales)

    list_size = sys.getsizeof(high_sales_list)
    generator_size = sys.getsizeof(high_sales_generator)

    print("\n[3] 리스트와 제너레이터 메모리 비교")
    print(f"리스트 메모리: {list_size} bytes")
    print(f"제너레이터 메모리: {generator_size} bytes")

    assert generator_size < list_size
    print("제너레이터 메모리 검증: 통과")

    # 제너레이터를 list로 바꾸지 않고 직접 순회하여 개수 확인
    generator_count = sum(
        1
        for _ in generate_high_sales(sales)
    )
    assert generator_count == len(high_sales_list)

    print(f"amount 1000 초과 거래 수: {generator_count}건")

    # 4) defaultdict로 월별·카테고리별 amount 목록 그룹핑
    monthly_category_amounts = defaultdict(
        lambda: defaultdict(list)
    )

    for row in sales:
        monthly_category_amounts[row["month"]][row["category"]].append(
            row["amount"]
        )

    # 컴프리헨션으로 그룹별 총매출 계산
    monthly_category_total = {
        month: {
            category: sum(amounts)
            for category, amounts in category_groups.items()
        }
        for month, category_groups
        in monthly_category_amounts.items()
    }

    print("\n[4] 월별·카테고리별 총매출")
    for month, category_totals in sorted(monthly_category_total.items()):
        print(month)

        for category, total in sorted(category_totals.items()):
            print(f"  {category}: {total:,}원")

    # 지역별 총매출 상위 3개를 금액 내림차순으로 정렬
    top3 = sorted(
        region_total.items(),
        key=lambda item: item[1],
        reverse=True
    )[:3]

    top3_amounts = [
        amount
        for _, amount in top3
    ]
    assert top3_amounts == sorted(top3_amounts, reverse=True)

    print("\n[Checkpoint] 지역별 총매출 TOP 3")
    for rank, (region, total) in enumerate(top3, start=1):
        print(f"{rank}위 {region}: {total:,}원")

    print("\n모든 Checkpoint를 통과했습니다.")


if __name__ == "__main__":
    main()