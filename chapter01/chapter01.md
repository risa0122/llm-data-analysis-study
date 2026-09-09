# Chapter 01 실습 기록

## STEP 1. 업무 질문 구체화

**원래 질문**: 요즘 재구매하는 고객이 줄어든 것 같다

**모호한 이유**: 기준 시점, 재구매의 정의, 분석 대상 고객 범위가 불명확함

**구체화 요소**

| 항목 | 내용 |
|---|---|
| 대상 | completed 주문 기준, 고객별 구매 이력 |
| 기준 | 고객 단위 / 월별 |
| 비교 | 첫 구매만 한 고객 vs 재구매(2회 이상) 고객 비율 추이 |
| 목적 | 재구매 유도 프로모션(고객 활동 시책) 기획 참고 |

**구체화된 질문**: 최근 데이터 기준, completed 주문을 낸 고객 중 재구매 고객 비율이 어떻게 변해왔는가

**결과 관찰**: 4개 항목으로 나눠보니 "매출이 줄어든 것 같다"는 막연한 문장이 실제로 무엇을 봐야 하는지(주문 상태, 고객 단위, 비교 대상)로 좁혀짐

**해석/판단**: 원래 질문은 분석 불가능한 형태였고, 구체화 후에야 필요한 데이터와 계산 방식이 명확해짐

**업무적 의미**: 재구매율이라는 구체적 지표가 나오면, 고객 활동 프로모션의 타겟과 효과 측정 기준으로 바로 연결 가능

**한계 인식**: 재구매율 정의(2회 이상)가 자의적일 수 있음. 실제 업무에서는 기간 기준(예: 90일 이내 재구매)을 함께 고려해야 함

## STEP 2. 실제 데이터 구조와 질문 연결

**필요한 파일**: customers.csv, orders.csv, order_items.csv, products.csv

**필요한 컬럼**

| 파일 | 컬럼 |
|---|---|
| customers | customer_id |
| orders | order_id, customer_id, order_date, order_status |
| order_items | order_item_id, order_id, product_id, quantity, unit_price |
| products | product_id, product_name, category |

**연결 관계**: customers.customer_id → orders.customer_id → orders.order_id → order_items.order_id → order_items.product_id → products.product_id

**판단**: 재구매율 계산에는 orders만 있으면 충분 (customer_id별 completed 주문 횟수 카운트). 카테고리/상품 정보는 이번 질문에는 불필요 → 보류

**미확인 항목**: 실제 컬럼 타입(order_date가 문자열인지 datetime인지)은 Notebook 실행 후 확인 필요

## STEP 3. LLM에게 분석 질문 후보 요청

**Prompt**:
"온라인 쇼핑몰 분석을 준비 중입니다. 데이터: customers, products, orders, order_items. 목적: completed 주문 기준 재구매 고객 비율과 구매 패턴 이해. 초보자가 먼저 확인할 분석 질문 5개를 제안해 주세요. 각 질문마다 필요한 파일과 컬럼도 함께 제시하세요."

**LLM 답변 요약**:

1. 재구매 고객 비율 추이 — orders(customer_id, order_status, order_date)
2. 카테고리별 매출 비중 — order_items + products(category, quantity, unit_price)
3. 결제수단별 취소율 — orders(payment_method, order_status)
4. 가입 후 첫 구매까지 걸리는 기간 — customers(signup_date), orders(order_date)
5. 연령대별 평균 구매 금액 — customers(age), orders, order_items

## STEP 4. LLM 제안을 실제 데이터로 검증

| # | 파일/컬럼 실제 존재 | 인과관계 리스크 | 판단 |
|---|---|---|---|
| 1 | 존재 확인 (orders 4개 컬럼 모두 실제 존재) | 낮음 | 채택 — STEP1 질문과 직결 |
| 2 | 존재 확인 | 낮음 | 보류 — 이번 범위 아님 |
| 3 | 존재 확인 | 낮음 | 보류 |
| 4 | 존재 확인 (signup_date 실제 컬럼) | 낮음 | 보류 |
| 5 | 존재 확인 (age 실제 컬럼) | 높음 — 연령이 구매액의 원인이라 단정 금지 | 수정 후 사용 — 상관관계 수준으로만 해석 |

**판단 요약**: 1번을 채택. LLM이 제안한 컬럼은 모두 실제 데이터에 존재함을 확인했지만, 5번처럼 인과관계로 오독될 수 있는 질문은 주의 문구 없이 쓰지 않기로 함

## STEP 5. Prompt Log

- 사용 목적: 재구매율 분석을 위한 하위 질문 아이디어 확보
- 입력 Prompt 요약: 4개 데이터, 재구매율/구매패턴 목적, 초보자용 질문 5개 + 필요 컬럼 요청
- LLM 답변 요약: 재구매율, 카테고리 매출, 결제수단별 취소율, 가입-구매 간격, 연령대별 구매액 5개 제안
- 실제 반영 여부: 1번만 이번 Chapter 범위로 채택
- 사람이 검증한 항목: 제안된 컬럼이 실제 customers/orders/order_items/products.csv에 존재하는지 원본 데이터 직접 확인
- 사람이 수정한 내용: 5번(연령대별 구매액)에 인과관계 단정 금지 주의 추가
- 남은 확인 사항: order_status의 실제 값 종류(completed/cancelled 외 추가 상태 존재 여부)는 Notebook 실행 후 확인 필요

## STEP 6. 개인정보와 Secret 보호

- [x] Prompt에 개인정보 미포함
- [x] Notebook에 API Key 미기록 (아직 미실행)
- [x] Prompt Log에 민감정보 없음
- [x] 캡처 화면에 Secret 없음 (이번 Chapter는 캡처 없음)
- [x] .env vs .env.example 차이 이해함

## STEP 7. Chapter 01 Notebook 확인

**상태**: 미실행 (로컬 Python/Jupyter 환경 미준비)

**계획**: Chapter 02에서 환경 구축 후 STEP7을 실제로 실행하고 evidence 첨부 예정

## STEP 8. Chapter 01 최종 해석 작성

**가장 중요한 내용**:
분석은 코드가 아니라 질문을 구체화하는 데서 시작한다. LLM은 정답을 주는 도구가 아니라 아이디어를 제안하는 도구이고, 제안된 컬럼과 논리는 실제 데이터로 반드시 검증해야 한다. 특히 연령·성별 같은 속성을 결과의 원인으로 단정하는 실수를 LLM도 사람도 저지르기 쉽다는 점을 확인했다.

**LLM 사용 시 주의점**:

1. 존재하지 않는 컬럼이나 파일을 제안할 수 있음 → 원본 데이터로 재확인 필요
2. 상관관계를 인과관계처럼 표현하는 경향이 있음 → 문구 수정 필요
3. 프롬프트에 실제 개인정보를 넣지 않아야 함

**역할 구분표**:

| 항목 | LLM의 도움 | 사람의 책임 |
|---|---|---|
| 질문 정의 | 표현을 다듬어주는 보조 | 실제 업무 맥락과 목적 결정 |
| 데이터 확인 | 확인할 항목 후보 제시 | 실제 파일/컬럼 존재 여부 검증 |
| 코드 작성 | 초안 코드 생성 | 실행 및 결과 검토 |
| 결과 해석 | 해석 방향 제안 | 최종 해석과 업무 적용 판단 |
| 최종 판단 | 참고 의견 제공 | 사용/수정/보류 결정 |

**다음 Chapter 기대사항**:
Chapter 02에서 실제 환경을 구축한 뒤, 이번에 채택한 재구매율 질문(STEP1)을 실제 코드로 돌려서 구체화한 질문과 실제 숫자가 얼마나 맞아떨어지는지 확인하고 싶다.

## STEP 9. 최종 제출 파일 검증

- [x] 모든 필수 STEP 작성
- [x] 결과 관찰·해석·판단·의미·한계 모두 작성 (STEP1)
- [x] LLM 결과를 정답으로 표현하지 않음 (STEP4에서 검증 후 수정)
- [x] 실행하지 않은 것(STEP7)은 PASS 표시 안 하고 미실행으로 명시
- [x] 개인정보·API Key·민감정보 없음
- [ ] 핵심 Evidence 캡처 이미지 (환경 준비 후 Chapter 02에서 추가 예정)

