"""
프로그램명: Adult Census Income 예측 Pipeline

프로그램 설명:
정제된 Adult 데이터를 학습용과 평가용으로 분리하고, 숫자형·범주형
변수의 전처리와 로지스틱 회귀 모델을 하나의 sklearn Pipeline으로
구성한다. 소득 그룹을 예측하고 정확도·F1 점수를 평가한 뒤 학습된
Pipeline 전체를 joblib 파일로 저장한다.

변경 내역:
- 분석 목적에 맞는 입력 변수와 목표 변수 선정
- ColumnTransformer 기반 숫자형·범주형 전처리 추가
- LogisticRegression을 포함한 Pipeline 학습·예측 추가
- 정확도·F1 점수·혼동행렬 출력 추가
- 학습된 Pipeline joblib 저장 및 파일·데이터 예외 처리 추가
"""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "processed" / "adult_clean.csv"
MODEL_FILE = BASE_DIR / "output" / "adult_income_pipeline.joblib"

NUMERIC_FEATURES = [
    "age",
    "capital_gain",
    "capital_loss",
    "hours_per_week",
]
CATEGORICAL_FEATURES = [
    "workclass",
    "education",
    "marital_status",
    "occupation",
]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET = "income"
INCOME_LABELS = ["<=50K", ">50K"]
RANDOM_STATE = 42


def load_model_data(path: Path) -> tuple[pd.DataFrame, pd.Series]:
    """정제 데이터를 읽어 모델의 입력 X와 정답 y로 분리한다."""

    if not path.is_file():
        raise FileNotFoundError(
            "정제 데이터가 없습니다. 01_data_preparation.py를 먼저 실행하세요."
        )

    frame = pd.read_csv(path)
    required = set(FEATURES) | {TARGET}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"모델 학습에 필요한 컬럼이 없습니다: {sorted(missing)}")
    if frame.empty:
        raise ValueError("모델 학습에 사용할 데이터가 없습니다.")

    frame[TARGET] = frame[TARGET].astype(str).str.strip().str.rstrip(".")
    unknown = set(frame[TARGET].dropna().unique()) - set(INCOME_LABELS)
    if unknown:
        raise ValueError(f"알 수 없는 income 값입니다: {sorted(unknown)}")

    features = frame[FEATURES].copy()
    target = (frame[TARGET] == ">50K").astype(int)
    return features, target


def build_pipeline() -> Pipeline:
    """숫자·범주형 전처리와 로지스틱 회귀를 하나로 묶는다."""

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "model",
                LogisticRegression(
                    max_iter=1_000,
                    class_weight="balanced",
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def evaluate_model(y_test: pd.Series, predictions: pd.Series) -> None:
    """정확도·F1 점수·혼동행렬과 분류 보고서를 출력한다."""

    accuracy = accuracy_score(y_test, predictions)
    f1 = f1_score(y_test, predictions)
    matrix = confusion_matrix(y_test, predictions)

    print("\n" + "=" * 72)
    print("모델 평가 결과")
    print("=" * 72)
    print(f"정확도  : {accuracy:.4f} ({accuracy:.1%})")
    print(f"F1 점수 : {f1:.4f}")
    print("\n[혼동행렬]")
    print("행=실제값, 열=예측값 / 순서: <=50K, >50K")
    print(matrix)
    print("\n[분류 보고서]")
    print(
        classification_report(
            y_test,
            predictions,
            target_names=INCOME_LABELS,
            digits=4,
            zero_division=0,
        )
    )


def main() -> int:
    """데이터 분리부터 Pipeline 학습·평가·저장까지 실행한다."""

    try:
        features, target = load_model_data(DATA_FILE)
        x_train, x_test, y_train, y_test = train_test_split(
            features,
            target,
            test_size=0.2,
            random_state=RANDOM_STATE,
            stratify=target,
        )

        print(f"전체 데이터: {len(features):,}행")
        print(f"학습 데이터: {len(x_train):,}행 (80%)")
        print(f"평가 데이터: {len(x_test):,}행 (20%)")
        print(f"입력 변수  : {', '.join(FEATURES)}")

        pipeline = build_pipeline()
        pipeline.fit(x_train, y_train)
        predictions = pipeline.predict(x_test)
        evaluate_model(y_test, predictions)

        MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(pipeline, MODEL_FILE)
        print(f"학습 모델 저장: {MODEL_FILE}")
        print("\n4단계 머신러닝 Pipeline이 완료됐습니다.")
        return 0
    except (FileNotFoundError, ValueError, TypeError, OSError) as error:
        print(f"[오류] {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
