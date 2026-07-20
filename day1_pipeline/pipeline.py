"""
Day 1 종합 실습 - 데이터 수집 미니 파이프라인

Open-Meteo, Countries.dev, ip-api의 데이터를
asyncio와 httpx를 이용해 동시에 수집한다.
"""

import asyncio
import time
from datetime import datetime
from typing import Literal
from pathlib import Path

import httpx
import pandas as pd
from pydantic import BaseModel, Field, IPvAnyAddress, ValidationError


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
CSV_FILE = OUTPUT_DIR / "collected_data.csv"
PARQUET_FILE = OUTPUT_DIR / "collected_data.parquet"


# 수집할 3개 API의 이름과 주소
API_URLS = {
    "weather": (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=37.5665"
        "&longitude=126.9780"
        "&hourly=temperature_2m,precipitation_probability"
        "&forecast_days=3"
        "&timezone=Asia/Seoul"
    ),
    "country": "https://countries.dev/alpha/KOR",
    "ip": (
        "http://ip-api.com/json/8.8.8.8"
        "?fields=status,message,country,countryCode,"
        "city,query,lat,lon,timezone"
    ),
}


class WeatherRecord(BaseModel):
    """Open-Meteo 응답에서 추출한 서울 시간별 날씨 한 건."""

    source: Literal["weather"] = "weather"
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    timezone: str = Field(min_length=1)
    observed_at: datetime
    temperature_2m: float = Field(ge=-100, le=70)
    precipitation_probability: int = Field(ge=0, le=100)


class CountryRecord(BaseModel):
    """Countries.dev 응답에서 추출한 대한민국 국가 정보."""

    source: Literal["country"] = "country"
    name: str = Field(min_length=1)
    native_name: str = Field(min_length=1)
    country_code: str = Field(min_length=2, max_length=2)
    region: str = Field(min_length=1)
    capital: str = Field(min_length=1)
    population: int = Field(gt=0)
    area: float = Field(gt=0)
    population_density: float = Field(gt=0)


class IPRecord(BaseModel):
    """ip-api 응답에서 추출한 IP 위치 정보."""

    source: Literal["ip"] = "ip"
    status: Literal["success"]
    ip_address: IPvAnyAddress
    country: str = Field(min_length=1)
    country_code: str = Field(min_length=2, max_length=2)
    city: str = Field(min_length=1)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    timezone: str = Field(min_length=1)


def validate_collected_data(
    collected_data: dict[str, dict],
) -> dict[str, BaseModel]:
    """3개 API 응답에서 필요한 필드를 추출하고 Pydantic으로 검증한다."""

    try:
        # 수집 결과에서 API별 원본 데이터를 꺼낸다.
        weather_raw = collected_data["weather"]
        country_raw = collected_data["country"]
        ip_raw = collected_data["ip"]

        # 날씨 응답의 시간별 데이터 부분을 꺼낸다.
        weather_hourly = weather_raw["hourly"]

        # 각 API 데이터를 해당 Pydantic 검사표에 넣는다.
        validated_data = {
            "weather": WeatherRecord(
                latitude=weather_raw["latitude"],
                longitude=weather_raw["longitude"],
                timezone=weather_raw["timezone"],
                observed_at=weather_hourly["time"][0],
                temperature_2m=weather_hourly["temperature_2m"][0],
                precipitation_probability=(
                    weather_hourly["precipitation_probability"][0]
                ),
            ),
            "country": CountryRecord(
                name=country_raw["name"],
                native_name=country_raw["nativeName"],
                country_code=country_raw["alpha2Code"],
                region=country_raw["region"],
                capital=country_raw["capital"],
                population=country_raw["population"],
                area=country_raw["area"],
                population_density=country_raw["populationDensity"],
            ),
            "ip": IPRecord(
                status=ip_raw["status"],
                ip_address=ip_raw["query"],
                country=ip_raw["country"],
                country_code=ip_raw["countryCode"],
                city=ip_raw["city"],
                latitude=ip_raw["lat"],
                longitude=ip_raw["lon"],
                timezone=ip_raw["timezone"],
            ),
        }

    except ValidationError as error:
        # 값의 타입이나 범위가 Pydantic 규칙에 맞지 않는 경우
        print("\n[Pydantic 검증 실패]")
        print(error)
        raise

    except (KeyError, IndexError, TypeError) as error:
        # API 응답에 필요한 키나 시간별 값이 없는 경우
        print(f"\n[API 응답 구조 오류] {error}")
        raise

    print("\nPydantic 검증 성공: weather, country, ip")
    return validated_data


def save_and_compare_formats(
    validated_data: dict[str, BaseModel],
    csv_path: Path,
    parquet_path: Path,
) -> pd.DataFrame:
    """검증 데이터를 CSV와 Parquet로 저장하고 읽기·쓰기 시간을 비교한다."""

    # Pydantic 객체를 저장 가능한 일반 딕셔너리로 변환한다.
    rows = [record.model_dump(mode="json") for record in validated_data.values()]

    # 딕셔너리 3개를 pandas 표로 변환한다.
    dataframe = pd.DataFrame(rows)

    # output 폴더가 없다면 생성한다.
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    # CSV 쓰기 시간을 측정한다.
    csv_write_started = time.perf_counter()
    dataframe.to_csv(
        csv_path,
        index=False,
        encoding="utf-8-sig",
    )
    csv_write_time = time.perf_counter() - csv_write_started

    # Parquet 쓰기 시간을 측정한다.
    parquet_write_started = time.perf_counter()
    dataframe.to_parquet(
        parquet_path,
        index=False,
        engine="pyarrow",
    )
    parquet_write_time = time.perf_counter() - parquet_write_started

    # CSV 읽기 시간을 측정한다.
    csv_read_started = time.perf_counter()
    csv_reloaded = pd.read_csv(
        csv_path,
        encoding="utf-8-sig",
    )
    csv_read_time = time.perf_counter() - csv_read_started

    # Parquet 읽기 시간을 측정한다.
    parquet_read_started = time.perf_counter()
    parquet_reloaded = pd.read_parquet(
        parquet_path,
        engine="pyarrow",
    )
    parquet_read_time = time.perf_counter() - parquet_read_started

    # 두 형식 모두 원본과 같은 행 수인지 확인한다.
    assert len(csv_reloaded) == len(dataframe)
    assert len(parquet_reloaded) == len(dataframe)

    print("\n===== 저장 및 성능 비교 =====")
    print(f"저장된 데이터: {len(dataframe)}행")
    print(f"CSV 쓰기:     {csv_write_time:.6f}초")
    print(f"Parquet 쓰기: {parquet_write_time:.6f}초")
    print(f"CSV 읽기:     {csv_read_time:.6f}초")
    print(f"Parquet 읽기: {parquet_read_time:.6f}초")
    print(f"CSV 파일:     {csv_path}")
    print(f"Parquet 파일: {parquet_path}")

    return dataframe


async def fetch_api(
    client: httpx.AsyncClient,
    api_name: str,
    url: str,
) -> tuple[str, dict]:
    """API 하나를 비동기로 호출하고 JSON 응답을 반환한다."""

    print(f"[요청 시작] {api_name}")

    response = await client.get(url)
    response.raise_for_status()

    print(f"[응답 완료] {api_name}: HTTP {response.status_code}")
    return api_name, response.json()


async def collect_all() -> dict[str, dict]:
    """3개 API를 asyncio.gather()로 동시에 수집한다."""

    timeout = httpx.Timeout(15.0)

    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True,
    ) as client:
        tasks = [fetch_api(client, api_name, url) for api_name, url in API_URLS.items()]

        # 세 작업을 동시에 실행하고 모든 결과가 끝날 때까지 기다린다.
        results = await asyncio.gather(*tasks)

    return dict(results)


def main() -> None:
    """비동기 데이터 수집을 실행하고 결과를 확인한다."""

    started_at = time.perf_counter()

    collected_data = asyncio.run(collect_all())
    validated_data = validate_collected_data(collected_data)
    save_and_compare_formats(
        validated_data,
        CSV_FILE,
        PARQUET_FILE,
    )

    elapsed = time.perf_counter() - started_at

    print("\n===== 수집 결과 =====")
    for api_name, data in collected_data.items():
        print(f"{api_name}: 정상 수집, 최상위 키 {list(data)[:5]}")

    print(f"\n총 수집 API: {len(collected_data)}개")
    print(f"전체 수집 시간: {elapsed:.4f}초")

    assert len(collected_data) == 3
    print("3개 API 동시 수집 Checkpoint 통과")


if __name__ == "__main__":
    main()
