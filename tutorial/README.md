# 튜토리얼 

## XR 트윈 프로젝트 목표

- 실제 미술공간을 스캔하여 실제 미술공간과 동일한 가상공간을 제작하여 
미술관 전시(동선, 미술품 추천)를 시뮬레이션해보고 고품질로 렌더링하여 시각적으로 확인하는 것을 목표로 함

### XR 트윈 저작도구의 이해

- 

### XR 트윈 저작도구 개발 파이프라인
  1. 


## **blender로 XR트윈 씬을 구성하기 (.blender 파일 만들기)**

- Unity에서 blender 파일 임포트하여 저작도구 및 렌더링에 사용하게 할 수 있도록 하는 일 

### 메쉬 최적화의 목표
  1. 저작도구 및 렌더링에서 활용하기에 적합한 메쉬 만들기
  2. 연구실 내부 혹은 kaist 측의 요구사항 맞추기

### Blender 시작하기
    1. Scene import
        [](./data/scene_import.png)
    2. View Camera


    3. Render Camera

    4. Object mode

        blender에서 collection에 포함된 object 단위의 변경 및 수정을 하는 모드

        modifier: object 단위의 알고리즘 적용


    4. Edit mode

        object 내부의 vertex, edge, face를 수정하기 위해 들어가는 window 창

### 주로 사용하는 기능

- Translation, Scale, Rotation
  - 기본

- Merge (가능한 edit: vertex, edge, face)
  - 단축키: element 선택 후, keyboard m
  - 선택한 vertex, edge, face들을 하나로 만드는 operation, 보통 vertex에 대해 사용하는게 편함

- Smoothing (가능한 edit: vertex)
  - 선택한 local vertex 영역에 대해 vertex position들의 mean 값으로 vertex 들을 움직임
  - 결과적으로 부드러운 vertex connection을 만듬
  - 부분적으로 평탄화시킬 때, mesh에서 vertex가 noise로 나올 때 사용

- Shifting (가능한 edit: vertex, edge, face)
  

