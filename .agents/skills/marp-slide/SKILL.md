---
name: marp-slide
description: Create or modify high-quality Marp markdown presentations with presenter notes and section dividers. Activate this skill whenever the user requests creating slides, presentations, Marp markdown decks, slide HTML/PDF, or wants to add speaker/presenter scripts to a presentation. Make sure to use this skill for all Marp-related tasks, slide generation, and presentation scripting, even if the user does not explicitly mention 'Marp'.
---

# Marp Slide Generation Skill

이 스킬은 데이터 분석 리포트나 특정 보고서를 바탕으로 고품질의 **Marp(Markdown Presentation Ecosystem)** 프레젠테이션 슬라이드를 설계하고, 정교한 발표자 대본을 탑재할 때 준수해야 하는 표준 가이드라인입니다.

---

## 🎨 1. Marp 기본 설정 및 디자인 테마

Marp 마크다운 파일의 맨 처음에 아래의 YAML 프론트매터(Frontmatter) 설정을 반드시 포함하여 슬라이드의 톤앤매너와 컴포넌트 스타일을 통일성 있게 구성합니다.

```yaml
---
marp: true
theme: default
paginate: false
backgroundColor: #f9fbfd
style: |
  section {
    font-family: 'Arial', sans-serif;
    padding: 50px;
    font-size: 20px;
    color: #333333;
  }
  h1 {
    color: #1F4E78;
    font-size: 32px;
    border-bottom: 3px solid #1F4E78;
    padding-bottom: 10px;
    margin-bottom: 20px;
  }
  h2 {
    color: #2E75B6;
    font-size: 26px;
    margin-bottom: 15px;
  }
  footer {
    font-size: 12px;
    color: #7f7f7f;
    text-align: right;
  }
  .highlight {
    color: #C00000;
    font-weight: bold;
  }
  .accent {
    color: #1F4E78;
    font-weight: bold;
  }
  table {
    font-size: 14px;
    margin-bottom: 10px;
  }
---
```

* **인라인 스타일 강조**: 중요 수치 및 키워드는 `<span class="highlight">` 또는 `<span class="accent">` 클래스 태그로 래핑하여 강조 효과를 부여합니다.

---

## 🖼️ 2. 가로 분할 레이아웃 (이미지 겹침 방지)

* **50% 가로 분할**: 시각화 이미지나 다이어그램이 수록되는 슬라이드는 본문 텍스트와 이미지가 겹치지 않도록 Marp의 가로 분할 레이아웃을 필히 활용합니다.
* **오른쪽 이미지 배치 문법**:
  ```markdown
  ![bg right:50% contain]([이미지 상대/절대 경로])
  ```
* **왼쪽 본문 영역**: 이미지의 정량적 수치 요약(2~3개 글머리 기호) 및 이에 대한 명확한 비즈니스적 해석(인사이트)만을 정제하여 배치합니다.

---

## 📑 3. 간지(Section Divider) 슬라이드 필수 배치

* 슬라이드의 흐름 제어와 청중의 집중도 전환을 위해, 대주제(목차)가 변경되는 분기점마다 **간지 슬라이드**를 배치합니다.
* 간지 슬라이드는 색상을 반전시켜 시각적 대비를 줍니다:
  ```markdown
  ---
  <!-- _class: lead -->
  <!-- _backgroundColor: #1F4E78 -->
  <!-- _color: #ffffff -->
  <style>
    section.lead h1 { color: #ffffff; border-bottom: 3px solid #ffffff; }
    section.lead h2 { color: #D5E8F0; }
  </style>

  # [세션 대제목]
  ## [세션 상세 서브 타이틀]
  ```

---

## 🎤 4. 2분 분량 발표자 노트(Presenter Notes) 규격

* **전체 페이지 적용**: 타이틀 슬라이드, 목차, 간지, 본문, Q&A 등 **모든 슬라이드** 하단에 발표 대본을 HTML 주석(`<!-- ... -->`) 형식으로 삽입합니다.
* **시간 및 글자수 준수**: 각 페이지의 대본은 발표 속도를 기준으로 **약 2분 분량**이 되도록 작성해야 합니다. (공백 포함 **550자 ~ 650자 내외**의 상세하고 완성도 높은 문어/구어 결합체 필수)
* **대본 시나리오 구성 규칙**:
  * **일반 슬라이드**: 장표에 적힌 요약 수치(예: 평균값, 상관계수, 비율 등)를 단순히 읽지 않고, 그 속에 담긴 데이터 분석적 의미와 비즈니스 마케팅 전략 제언을 논리적으로 풀어서 말하듯이 설명해야 합니다. 이전 슬라이드와 다음 슬라이드 간의 매끄러운 링킹(Linking) 멘트를 포함시킵니다.
  * **간지 슬라이드**: 해당 세션이 시작하게 된 배경 맥락을 짚고, 앞선 세션의 주요 성과를 요약한 뒤, 이번 세션의 핵심 안건과 청중의 관전 요소를 우아하고 세련된 비즈니스 톤으로 브리핑합니다.

---

## 🚫 5. 스타일 및 규격 금지 제약 사항

* **슬라이드/시각화 번호 전면 제외**: 슬라이드 하단에 자동으로 생성되는 페이지 번호를 숨겨야 하므로 YAML 설정에 `paginate: false`를 지정하며, 슬라이드 제목이나 대본 내에 **'1.', '2)', '첫째' 등 순서 지칭 및 번호 매기기를 일절 사용하지 않습니다.** (유연한 순서 배치를 위함)
* **한국어 작성 원칙**: 프레젠테이션의 모든 콘텐츠(슬라이드 본문, 발표자 대본, 코드 및 데이터 설명)는 **한국어**로만 완성도 있게 표현합니다.

---

## 📐 6. 추천 프레젠테이션 구조 (30페이지 이상 덱 설계 시)

1. **도입부**: 타이틀 ➡️ 목차 ➡️ [간지: 개요] ➡️ 분석 개요 및 목적
2. **데이터 기초**: 데이터 세트 프로파일링 및 가공 요약 ➡️ [간지: 기술통계] ➡️ 기술통계 수치형 요약 ➡️ 기술통계 범주형 요약
3. **시각화 분석 (가로 분할)**: [간지: 다차원 분석] ➡️ 일변량/이변량/다변량/텍스트 시각화 슬라이드군 배치
4. **인사이트 도출**: [간지: 비즈니스 인사이트] ➡️ 전략적 6대 인사이트 및 마케팅 프라이싱 세부 도표 슬라이드군 배치
5. **결론 및 마무리**: [간지: 결론 및 Action Plan] ➡️ 실행 로드맵 및 단기/중기 액션 플랜 ➡️ Q&A 마무리
