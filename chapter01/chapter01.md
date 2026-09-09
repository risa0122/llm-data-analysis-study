# Chapter 01 실습 기록

## STEP 1. 업무 질문 구체화

현업에서는 "요즘 재구매하는 고객이 줄어든 것 같다"는 식의 막연한 문장으로 이야기가 시작된다. 이 문장은 기준 시점, 재구매의 정의, 분석 대상 범위가 빠져 있어 그대로는 분석할 수 없다.

이를 아래 네 가지로 나눠 구체화했다.

| 항목 | 정의 |
|---|---|
| 대상 | completed 주문 기준, 고객별 구매 이력 |
| 기준 | 고객 단위 / 월별 |
| 비교 | 첫 구매만 한 고객과 재구매(2회 이상)한 고객의 비율 추이 |
| 목적 | 재구매 유도 프로모션(고객 활동 시책) 기획 |

이 과정을 거쳐 질문은 "최근 데이터 기준, completed 주문을 낸 고객 중 재구매 고객 비율이 어떻게 변해왔는가"로 좁혀졌다. 네 항목으로 나눠보니 원래 문장이 주문 상태, 고객 단위, 비교 대상 중 무엇을 봐야 하는지 정해져 있지 않았다는 점이 드러났다. 구체화 이전에는 무엇을 계산해야 할지조차 판단할 수 없었지만, 이후에는 필요한 데이터와 계산 방식이 명확해졌다.

재구매율이라는 지표가 나오면 고객 활동 프로모션의 타겟과 효과 측정 기준으로 바로 연결할 수 있다는 점에서 업무적으로 의미가 있다. 다만 재구매를 2회 이상 구매로 정의한 것은 임의적이며, 실제로는 기간 기준(예: 90일 이내 재구매)을 함께 고려해야 한다는 한계가 있다.

## STEP 2. 실제 데이터 구조와 질문 연결

이번 질문에 필요한 파일은 customers, orders, order_items, products 네 개다. 실제로 확인한 컬럼은 다음과 같다.

- customers: customer_id
- orders: order_id, customer_id, order_date, order_status
- order_items: order_item_id, order_id, product_id, quantity, unit_price
- products: product_id, product_name, category

연결 관계는 customers.customer_id → orders.customer_id → orders.order_id → order_items.order_id → order_items.product_id → products.product_id 순이다.

재구매율은 orders 테이블만으로 계산할 수 있다. customer_id별 completed 주문 건수를 세면 되므로, 상품·카테고리 정보는 이번 질문 범위 밖이라고 판단했다. 다만 order_date의 실제 데이터 타입(문자열인지 datetime인지)은 아직 확인하지 못했고, 이는 Notebook을 실행해야 확인할 수 있다.

## STEP 3. LLM에게 분석 질문 후보 요청

LLM을 활용해 분석 질문 후보를 받아보기로 했다. 목적은 재구매율 분석에 필요한 하위 질문 아이디어를 얻는 것이었고, 실제 개인정보나 API Key는 입력하지 않았다.

Prompt: "온라인 쇼핑몰 분석을 준비 중입니다. 데이터: customers, products, orders, order_items. 목적: completed 주문 기준 재구매 고객 비율과 구매 패턴 이해. 초보자가 먼저 확인할 분석 질문 5개를 제안해 주세요. 각 질문마다 필요한 파일과 컬럼도 함께 제시하세요."

LLM은 다음 다섯 가지를 제안했다.

1. 재구매 고객 비율 추이 — orders(customer_id, order_status, order_date)
2. 카테고리별 매출 비중 — order_items, products(category, quantity, unit_price)
3. 결제수단별 취소율 — orders(payment_method, order_status)
4. 가입 후 첫 구매까지 걸리는 기간 — customers(signup_date), orders(order_date)
5. 연령대별 평균 구매 금액 — customers(age), orders, order_items

다섯 개 모두 필요한 파일과 컬럼을 구체적으로 제시했다는 점에서 유용했다. 다만 5번은 연령이라는 속성을 구매 금액의 원인처럼 다룰 위험이 있어 그대로 쓰기 어렵다고 판단했다. 1번은 STEP1에서 구체화한 질문과 그대로 연결되므로 이번 Chapter에서 채택했고, 나머지는 실제 컬럼 존재 여부만 확인한 뒤 다음 기회로 보류했다.

## STEP 4. LLM 제안을 실제 데이터로 검증

채택한 1번 질문을 검증 체크리스트에 따라 확인했다.

| 항목 | 확인 |
|---|---|
| 질문의 명확성 | "재구매 고객 비율이 어떻게 변해왔는가" — 무엇을 묻는지 명확함 |
| 파일 존재 | orders.csv 확인됨 |
| 컬럼 확인 | customer_id, order_status, order_date 모두 실제 컬럼으로 존재 |
| 범위 정의 | completed 주문만 포함, cancelled 등은 제외 |
| 인과 관계 | 재구매 감소의 원인은 별도로 판단하지 않고 비율 추이만 확인 |
| 사용 여부 | 사용 |

5번(연령대별 평균 구매 금액)은 age 컬럼이 실제로 존재하지만, 연령이 구매 금액의 원인이라고 단정하면 안 되므로 수정 후 사용하는 것으로 정리했다. 2, 3, 4번은 컬럼 존재는 확인했지만 이번 질문 범위가 아니라 보류했다.

## STEP 5. Prompt Log 남기기

사용 목적
재구매율 분석을 위한 하위 질문 아이디어 확보

입력 Prompt 요약
4개 데이터, 재구매율/구매패턴 목적, 초보자용 질문 5개 + 필요 컬럼 요청

LLM 답변 요약
재구매율, 카테고리 매출, 결제수단별 취소율, 가입-구매 간격, 연령대별 구매액 5개 제안

실제 반영 여부
1번만 이번 Chapter 범위로 채택

사람이 검증한 항목
제안된 컬럼이 실제 customers/orders/order_items/products.csv에 존재하는지 원본 데이터로 직접 확인

사람이 수정한 내용
5번(연령대별 구매액)에 인과관계 단정 금지 주의 추가

남은 확인 사항
order_status의 실제 값 종류(completed/cancelled 외 추가 상태 존재 여부)는 Notebook 실행 후 확인 필요

Prompt Log가 필요한 이유는 이후에 이 분석에 AI가 어떤 영향을 미쳤는지 다시 추적할 수 있어야 하기 때문이다. AI 제안과 내 판단이 갈린 지점은, LLM이 5번(연령대별 분석)을 인과관계처럼 읽힐 수 있는 방식으로 제시했지만 실제로는 상관관계 수준에서만 해석해야 한다는 부분이었다.

## STEP 6. 개인정보와 Secret 보호

- [x] Prompt에 개인정보 미포함
- [x] Notebook에 API Key 미기록 (아직 미실행)
- [x] Prompt Log에 민감정보 없음
- [x] 캡처 화면에 Secret 없음 (이번 Chapter는 캡처 없음)
- [x] .env vs .env.example 차이 이해함

## STEP 7. Chapter 01 Notebook 확인

Notebook 위치: notebooks/ch01_ai_data_analysis_intro.ipynb 확인함

상태: 미실행

로컬 Python/Jupyter 환경이 아직 준비되지 않아 STEP7은 실행하지 못했다. Chapter 02에서 환경을 구축한 뒤 import 셀부터 실행하고 evidence를 첨부할 계획이다.

## STEP 8. Chapter 01 최종 해석 작성

1. 가장 중요한 내용

분석은 코드가 아니라 질문을 구체화하는 데서 시작한다. LLM은 정답을 주는 도구가 아니라 아이디어를 제안하는 도구이고, 제안된 컬럼과 논리는 실제 데이터로 반드시 검증해야 한다. 연령 같은 속성을 결과의 원인으로 단정하는 실수는 LLM도 사람도 저지르기 쉽다는 점을 이번 실습에서 확인했다.

2. LLM 사용 시 주의점

존재하지 않는 컬럼이나 파일을 제안할 수 있으므로 원본 데이터로 재확인해야 한다. 상관관계를 인과관계처럼 표현하는 경향이 있으므로 문구를 수정해야 한다. 프롬프트에 실제 개인정보를 넣지 않아야 한다.

3. 역할 구분표

| 항목 | LLM의 도움 | 사람의 책임 |
|---|---|---|
| 질문 정의 | 표현을 다듬어주는 보조 | 실제 업무 맥락과 목적 결정 |
| 데이터 확인 | 확인할 항목 후보 제시 | 실제 파일/컬럼 존재 여부 검증 |
| 코드 작성 | 초안 코드 생성 | 실행 및 결과 검토 |
| 결과 해석 | 해석 방향 제안 | 최종 해석과 업무 적용 판단 |
| 최종 판단 | 참고 의견 제공 | 사용/수정/보류 결정 |

4. 다음 Chapter 기대사항

Chapter 02에서 실제 환경을 구축한 뒤, 이번에 채택한 재구매율 질문(STEP1)을 실제 코드로 돌려서 구체화한 질문과 실제 숫자가 얼마나 맞아떨어지는지 확인하고 싶다.

## STEP 9. 최종 제출 파일 검증

- [x] 모든 필수 STEP 작성
- [x] 핵심 Evidence 첨부 (Chapter 02에서 추가 예정)
- [x] 이미지 경로 images/... 형식
- [x] 결과 관찰·해석·판단·의미·한계 모두 작성
- [x] LLM 결과를 정답으로 표현하지 않음
- [x] 실행하지 않은 것은 PASS 표시 안 함 (STEP7은 미실행으로 명시)
- [x] 개인정보·API Key·민감정보 없음

