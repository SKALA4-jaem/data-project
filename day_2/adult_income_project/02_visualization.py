"""
프로그램명: Adult Census Income EDA 시각화

프로그램 설명:
1단계에서 정제한 adult_clean.csv를 사용해 소득 그룹 비율, 나이 분포,
주당 근무시간, 숫자형 변수 상관관계를 하나의 2x2 그래프로 비교한다.
교육 수준별 고소득자 비율은 Plotly 인터랙티브 차트로도 저장한다.

변경 내역:
- 정적 교육 그래프를 숫자형 변수 상관관계 히트맵으로 변경
- 소득 그룹별 나이 분포를 공정한 비교를 위한 밀도 기준으로 변경
- 교육 수준별 고소득자 비율 계산
- Plotly HTML 저장 추가
- 파일·필수 컬럼·소득 라벨·산출물 예외 처리 추가
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import seaborn as sns
from matplotlib import font_manager


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "processed" / "adult_clean.csv"
STATIC_CHART_FILE = BASE_DIR / "output" / "adult_income_eda.png"
INTERACTIVE_CHART_FILE = BASE_DIR / "output" / "education_income_rate.html"

CORRELATION_COLUMNS = [
    "age",
    "education_num",
    "capital_gain",
    "capital_loss",
    "hours_per_week",
    "high_income",
]
REQUIRED_COLUMNS = {
    "age",
    "education",
    "education_num",
    "capital_gain",
    "capital_loss",
    "hours_per_week",
    "income",
}
INCOME_ORDER = ["<=50K", ">50K"]
INCOME_PALETTE = {"<=50K": "#4C78A8", ">50K": "#F58518"}


def load_clean_data(path: Path) -> pd.DataFrame:
    """정제 CSV를 읽고 필수 컬럼과 소득 라벨을 검증한다."""

    if not path.is_file():
        raise FileNotFoundError(
            "정제 데이터가 없습니다. 01_data_preparation.py를 먼저 실행하세요."
        )

    frame = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"필수 컬럼이 없습니다: {sorted(missing)}")
    if frame.empty:
        raise ValueError("시각화할 데이터가 없습니다.")

    frame["income"] = frame["income"].astype(str).str.strip().str.rstrip(".")
    unknown_labels = set(frame["income"].unique()) - set(INCOME_ORDER)
    if unknown_labels:
        raise ValueError(f"알 수 없는 income 값입니다: {sorted(unknown_labels)}")

    frame["high_income"] = (frame["income"] == ">50K").astype(int)
    return frame


def configure_plot_style() -> None:
    """macOS 한글 폰트를 적용하고 시각화 스타일을 통일한다."""

    font_path = Path("/System/Library/Fonts/AppleSDGothicNeo.ttc")
    font_name = "sans-serif"
    if font_path.is_file():
        font_name = font_manager.FontProperties(fname=font_path).get_name()

    sns.set_theme(style="whitegrid", font=font_name)
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.facecolor"] = "#FAFAFC"
    plt.rcParams["axes.facecolor"] = "#FFFFFF"


def summarize_education(frame: pd.DataFrame) -> pd.DataFrame:
    """교육 수준별 전체 인원·고소득자 수·고소득자 비율을 계산한다."""

    return (
        frame.groupby("education", as_index=False)
        .agg(
            total_people=("income", "size"),
            high_income_people=("high_income", "sum"),
            high_income_rate=("high_income", "mean"),
        )
        .sort_values("high_income_rate")
    )


def save_static_dashboard(
    frame: pd.DataFrame,
    output: Path,
) -> None:
    """소득 비율·나이·근무시간·상관관계를 하나의 2x2 그래프로 저장한다."""

    configure_plot_style()
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    sns.countplot(
        data=frame,
        x="income",
        order=INCOME_ORDER,
        hue="income",
        legend=False,
        palette=INCOME_PALETTE,
        ax=axes[0, 0],
    )
    total = len(frame)
    for container in axes[0, 0].containers:
        axes[0, 0].bar_label(
            container,
            labels=[f"{bar.get_height() / total:.1%}" for bar in container],
            padding=3,
        )
    axes[0, 0].set_title("소득 그룹별 인원 및 비율")
    axes[0, 0].set_xlabel("소득 그룹")
    axes[0, 0].set_ylabel("인원")

    sns.histplot(
        data=frame,
        x="age",
        hue="income",
        hue_order=INCOME_ORDER,
        kde=True,
        element="step",
        stat="density",
        common_norm=False,
        bins=30,
        alpha=0.25,
        palette=INCOME_PALETTE,
        ax=axes[0, 1],
    )
    axes[0, 1].set_title("소득 그룹별 나이 분포(그룹별 밀도)")
    axes[0, 1].set_xlabel("나이")
    axes[0, 1].set_ylabel("밀도")

    sns.boxplot(
        data=frame,
        x="income",
        y="hours_per_week",
        order=INCOME_ORDER,
        hue="income",
        legend=False,
        palette=INCOME_PALETTE,
        showfliers=False,
        ax=axes[1, 0],
    )
    axes[1, 0].set_title("소득 그룹별 주당 근무시간")
    axes[1, 0].set_xlabel("소득 그룹")
    axes[1, 0].set_ylabel("주당 근무시간")

    correlation = frame[CORRELATION_COLUMNS].corr().rename(
        index={
            "age": "나이",
            "education_num": "교육 수준",
            "capital_gain": "자본 이익",
            "capital_loss": "자본 손실",
            "hours_per_week": "주당 근무시간",
            "high_income": "고소득 여부",
        },
        columns={
            "age": "나이",
            "education_num": "교육 수준",
            "capital_gain": "자본 이익",
            "capital_loss": "자본 손실",
            "hours_per_week": "주당 근무시간",
            "high_income": "고소득 여부",
        },
    )
    sns.heatmap(
        correlation,
        annot=True,
        fmt=".2f",
        cmap=sns.diverging_palette(220, 325, s=80, l=55, as_cmap=True),
        center=0,
        vmin=-1,
        vmax=1,
        square=True,
        linewidths=0.7,
        cbar_kws={"label": "상관계수", "shrink": 0.8},
        ax=axes[1, 1],
    )
    axes[1, 1].set_title("숫자형 변수 상관관계")
    axes[1, 1].set_xlabel("")
    axes[1, 1].set_ylabel("")
    axes[1, 1].tick_params(axis="x", rotation=35)
    axes[1, 1].tick_params(axis="y", rotation=0)

    fig.suptitle("Adult Census Income 핵심 EDA", fontsize=18, fontweight="bold")
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160, bbox_inches="tight")
    print("그래프 창을 닫으면 Plotly HTML 저장이 계속됩니다.")
    plt.show()
    plt.close(fig)
    print(f"정적 차트 저장: {output}")


def save_interactive_chart(summary: pd.DataFrame, output: Path) -> None:
    """교육 수준별 고소득자 비율을 Plotly HTML로 저장한다."""

    figure = px.bar(
        summary,
        x="high_income_rate",
        y="education",
        orientation="h",
        color="high_income_rate",
        color_continuous_scale="Tealgrn",
        hover_data={
            "total_people": ":,",
            "high_income_people": ":,",
            "high_income_rate": ":.1%",
        },
        title="교육 수준별 고소득자 비율",
        labels={
            "education": "교육 수준",
            "high_income_rate": "고소득자 비율",
            "total_people": "전체 인원",
            "high_income_people": "고소득자 수",
        },
    )
    figure.update_layout(coloraxis_showscale=False)
    figure.update_xaxes(tickformat=".0%")
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.write_html(output, include_plotlyjs=True)
    print(f"Plotly 차트 저장: {output}")


def main() -> int:
    """정제 데이터 로딩·요약·정적 차트·인터랙티브 차트를 순서대로 실행한다."""

    try:
        frame = load_clean_data(DATA_FILE)
        education_summary = summarize_education(frame)

        print(f"시각화 데이터: {len(frame):,}행")
        print("\n[교육 수준별 고소득자 비율 상위 5개]")
        print(education_summary.tail(5).sort_values("high_income_rate", ascending=False).to_string(index=False))

        save_static_dashboard(frame, STATIC_CHART_FILE)
        save_interactive_chart(education_summary, INTERACTIVE_CHART_FILE)

        print("\n2단계 시각화가 완료됐습니다.")
        return 0
    except (FileNotFoundError, ValueError, OSError) as error:
        print(f"[오류] {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
