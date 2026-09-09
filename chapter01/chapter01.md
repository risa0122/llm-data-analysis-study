# Chapter 01 실습 기록

## 제출 정보

| 항목 | 내용 |
|---|---|
| 이름 | 김종은 |
| GitHub ID | risa0122 |
| 저장소명 | llm-data-analysis-study |
| 작성일 | 2026-09-09 |
| 사용한 LLM | Claude |

## 1. 원래 업무 질문

선택한 막연한 질문: "요즘 재구매하는 고객이 줄어든 것 같다"

모호한 이유: 기준 시점·재구매 정의·대상 범위 미특정으로 분석 불가.

분석 가능한 질문으로 재작성하기 위해 네 항목으로 분해함.

| 항목 | 정의 |
|---|---|
| 대상 | completed 주문 기준, 고객별 구매 이력 |
| 기준 | 고객 단위 / 월별 |
| 비교 | 첫 구매만 한 고객과 재구매(2회 이상)한 고객의 비율 추이 |
| 목적 | 재구매 유도 프로모션(고객 활동 시책) 기획 |

재작성 질문: "최근 데이터 기준, completed 주문을 낸 고객 중 재구매 고객 비율이 어떻게 변해왔는가"

**결과 관찰**
네 항목 분해 과정에서 원 문장이 주문 상태·고객 단위·비교 대상을 특정하지 않았음이 드러남.

**나의 해석과 판단**
구체화 전에는 계산 대상 자체를 정의 불가. 네 항목 분해 후 필요 데이터와 계산 방식이 확정됨.

**업무·분석적 의미**
재구매율은 고객 활동 프로모션의 타겟 선정 및 효과 측정 기준으로 직접 연결 가능.

**한계와 추가 확인 사항**
재구매를 2회 이상 구매로 정의한 것은 임의적. 실무 적용 시 기간 기준(예: 90일 이내 재구매) 병행 검토 필요.

## 2. 질문과 필요한 데이터 연결

필요 파일: customers.csv, products.csv, orders.csv, order_items.csv

컬럼 후보

- customers: customer_id
- orders: order_id, customer_id, order_date, order_status
- order_items: order_item_id, order_id, product_id, quantity, unit_price
- products: product_id, product_name, category

PK/FK 관계: customers.customer_id → orders.customer_id / orders.order_id → order_items.order_id / products.product_id → order_items.product_id

**결과 관찰**
재구매율 산출에 필요한 customer_id, order_status, order_date는 orders에 모두 존재.

**나의 해석과 판단**
재구매율은 orders 단독 산출 가능. customer_id별 completed 주문 건수 집계로 계산되므로 상품·카테고리 정보는 이번 질문 범위 밖으로 판단함.

**업무·분석적 의미**
단일 테이블로 산출 가능하므로 초기 지표로 빠르게 확인 가능.

**한계와 추가 확인 사항**
order_date의 데이터 타입(문자열/datetime) 미확인. Notebook 실행 후 확인 필요.

## 3. LLM에게 분석 질문 후보 요청

사용 목적: 재구매율 분석의 하위 질문 아이디어 확보. 실제 개인정보 및 API Key 미입력.

실제 Prompt

```
온라인 쇼핑몰 데이터 분석을 준비 중입니다.
데이터 파일과 컬럼은 다음과 같습니다.
- customers.csv: customer_id, name, gender, age, city, signup_date
- orders.csv: order_id, customer_id, order_date, payment_method, order_status
- order_items.csv: order_item_id, order_id, product_id, quantity, unit_price
- products.csv: product_id, product_name, category

분석 목적: completed 주문 기준으로 재구매 고객 비율과 구매 패턴을 이해하는 것입니다.
초보자가 먼저 확인할 분석 질문 5개를 제안해 주세요.
각 질문마다 필요한 파일과 컬럼도 함께 제시해 주세요.
```

LLM 답변 요약

1. 재구매 고객 비율 추이 — orders(customer_id, order_status, order_date)
2. 카테고리별 매출 비중 — order_items(quantity, unit_price), products(category)
3. 결제수단별 취소율 — orders(payment_method, order_status)
4. 가입 후 첫 구매까지 걸리는 기간 — customers(signup_date), orders(order_date)
5. 연령대별 평균 구매 금액 — customers(age), orders, order_items

**결과 관찰**
5건 모두 필요 파일과 컬럼을 함께 제시. 존재하지 않는 파일명은 제시되지 않음.

**나의 해석과 판단**
1번은 재작성 질문과 직접 연결되어 채택. 5번은 연령을 구매 금액의 원인으로 다룰 위험이 있어 원안 사용 곤란.

**업무·분석적 의미**
LLM은 분석 착수 시점의 질문 목록 확보에 유효. 단 우선순위 결정은 업무 목적을 아는 사람이 수행해야 함.

**한계와 추가 확인 사항**
제시된 컬럼의 실제 존재 여부는 별도 검증 필요. 4번은 가입일 기준 코호트 정의가 추가로 필요함.

## 4. LLM 제안 검증

채택한 1번 질문을 검증 체크리스트로 확인함.

| 항목 | 확인 |
|---|---|
| 질문의 명확성 | "재구매 고객 비율이 어떻게 변해왔는가" — 질의 대상 명확 |
| 파일 존재 | orders.csv 확인 |
| 컬럼 확인 | customer_id, order_status, order_date 실제 존재 |
| 범위 정의 | completed 주문만 포함, cancelled 등 제외 |
| 인과 관계 | 감소 원인은 단정하지 않고 비율 추이만 확인 |
| 사용 여부 | 사용 |

제안별 판단: 1번 사용 / 5번 수정 후 사용 / 2·3·4번 보류

**결과 관찰**
LLM이 제시한 컬럼은 원본 csv에서 모두 실제 존재를 확인함. age, signup_date, payment_method 포함.

**나의 해석과 판단**
컬럼 존재 여부는 문제없었으나, 5번은 연령을 구매 금액의 원인으로 단정할 수 없어 수정 후 사용으로 정리함. 2·3·4번은 이번 질문 범위 밖으로 보류.

**업무·분석적 의미**
LLM 제안을 그대로 쓰지 않고 데이터·범위·인과관계 3개 축으로 거르는 절차가 필요함을 확인.

**한계와 추가 확인 사항**
order_status 실제 값 종류(completed/cancelled 외 추가 상태 여부) 미확인. Notebook 실행 후 확인 필요.

## 5. Prompt Log

사용 목적
재구매율 분석의 하위 질문 아이디어 확보

입력 Prompt 요약
4개 데이터 파일과 컬럼 목록 제시, 재구매율·구매 패턴 목적 명시, 초보자용 질문 5개 및 필요 컬럼 요청

LLM 답변 요약
재구매율, 카테고리 매출, 결제수단별 취소율, 가입-구매 간격, 연령대별 구매액 5건 제안

실제 반영 여부
1번만 이번 Chapter 범위로 채택

사람이 검증한 항목
제안 컬럼의 실제 존재 여부를 원본 csv로 직접 확인

사람이 수정한 내용
5번에 인과관계 단정 금지 주의 추가

남은 확인 사항
order_status 실제 값 종류 — Notebook 실행 후 확인

Prompt Log는 분석에 AI가 미친 영향을 사후 추적하기 위해 필요함. AI 제안과 판단이 갈린 지점은 5번으로, LLM은 인과관계로 읽힐 수 있는 형태로 제시했으나 상관관계 수준으로만 해석해야 함.

## 6. 개인정보와 Secret 보호

- [x] Prompt에 실명·이메일·전화번호·주소 등 개인정보 미포함
- [x] Notebook에 API Key 미기록 (미실행 상태)
- [x] Prompt Log에 민감정보 없음
- [x] 캡처 화면에 Secret 없음
- [x] .env(실제 값)와 .env.example(형식만) 차이 이해

## 7. Chapter 01 Notebook 확인

Notebook 위치: notebooks/ch01_ai_data_analysis_intro.ipynb 확인

상태: 미실행

로컬 Python/Jupyter 환경 미준비로 실행 불가. Chapter 02에서 환경 구축 후 import 셀부터 실행하고 Evidence 첨부 예정.

## 8. 최종 해석

**가장 중요한 내용**

분석은 코드가 아니라 질문 구체화에서 시작됨. LLM은 정답 생성기가 아닌 아이디어 도구이며, 제안된 컬럼과 논리는 실제 데이터 검증이 필수. 연령 등 속성을 결과의 원인으로 단정하는 오류는 LLM과 사람 모두 범하기 쉬움을 확인함.

**LLM 사용 시 주의점**

존재하지 않는 컬럼·파일 제안 가능 → 원본 데이터 재확인 필요. 상관관계를 인과관계로 표현하는 경향 존재 → 문구 수정 필요. 프롬프트에 실제 개인정보 미입력 원칙 준수.

**역할 구분표**

| 항목 | LLM의 도움 | 사람의 책임 |
|---|---|---|
| 질문 정의 | 표현 정리 보조 | 실제 업무 맥락과 목적 결정 |
| 데이터 확인 | 확인 항목 후보 제시 | 실제 파일·컬럼 존재 여부 검증 |
| 코드 작성 | 초안 코드 생성 | 실행 및 결과 검토 |
| 결과 해석 | 해석 방향 제안 | 최종 해석과 업무 적용 판단 |
| 최종 판단 | 참고 의견 제공 | 사용·수정·보류 결정 |

**다음 Chapter 기대사항**

Chapter 02에서 환경 구축 후, 채택한 재구매율 질문을 실제 코드로 실행. 구체화 질문과 실제 수치의 정합성 확인 예정.
