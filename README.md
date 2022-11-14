# README

## TODO
* requirements.txt 추가 예정

## Middle-End
* 구동 방법
    - `python main.py`
    - Flask 서버 구동 확인 후, http://127.0.0.1:5000 접속
## Git 주요 절차 개념 설명
* 모든 작업은 본 repo로부터 최소한 한번의 `git clone`이 된 local directory에서 수행합니다.
* local directory에서 작업을 하기 전 반드시 `git pull`을 실행하여 remote repo의 최신 형상(버전)을 받아 오도록 합니다.
* local directory에 작업을 한 후, `git status`를 실행하면 어떤 파일에 변동분이 생겼는지 확인할 수 있습니다.
* `git add`를 통해 변동분을 staging할 수 있습니다. staging은 임시기록이며 `git add`로 쌓인 여러 변동분들을 모아 `git commit`으로 형상 기록합니다. 이때의 형상 기록은 local 형상이며, remote repo에 형상 기록을 해야 협업자들에게 공식적으로 공유됩니다.
* remote repo에 형상 기록은 `git push`로 합니다.

## 우리 프로젝트 Git Routine Cheatsheet
* 처음 1회, 또는 형상 꼬이는 문제 발생해 새로 시작할 때
    - `git clone https://...`
        - local directory가 생기며 그곳에서 개발을 시작
* local 작업 전
    - `git pull`
        - remote repo와 local directory의 형상을 일치
* local 작업 완료
    - `git status`
        - 작업에 의해 발생한 변동분을 육안 확인
    - `git add .`
        - `git status`로 인식된 모든 변동분을 staging
    - `git commit -m "..."`
        - staging된 변동분을 반영한 형상 기록
    - `git push origin master`
        - local directory에 기록된 형상을 remote repo에 반영
* `git push` 실패 시(형상 버전 충돌)
    - local 작업 전 `git pull`로 remote repo와 형상을 맞추고 시작했음에도 불구하고, 그 사이 다른 협업자가 remote repo에 형상 기록을 한 경우 형상 버전 충돌이 일어나 `git push origin master`가 실패함.
    - 이때는 `git pull`을 추가 수행해 형상을 다시 일치시킨 후 재시도해야 함.
    - 1차 시도
        - `git pull`
        - `git push origin master`
    - 2차 시도(1차 시도 `git pull` 실패 시)
        - `git pull --rebase`
        - `git push origin master`
* 협업 개발 시 형상 버전 충돌이 수시로 일어나고 매번 해결해야 하므로, `git pull`을 자주 실행해 주는 것이 좋은 습관임. 그리고, `git commit` 전에 `git pull`을 한번씩 해 주는 것도 좋은 습관임.
* local directory와 remote repo 간 형상 버전 충돌이 끝까지 해결되지 않을 때는 architect와 상의 바람.