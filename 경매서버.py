import random
import threading
import time
import os
from flask import Flask, jsonify, request
from flask_cors import CORS  # ✨ CORS 추가


app = Flask(__name__)
CORS(app)  # 🔹 모든 도메인에서 API 호출 가능하도록 허용

# ✅ 환경 변수에서 포트 가져오기 (Fly.io는 기본적으로 8080 포트를 사용함)
PORT = int(os.environ.get("PORT", 8080))

# ✅ 팀 목록 불러오기
def load_teams():
    team_file = "team_list.txt"
    try:
        with open(team_file, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        return ["팀 1", "팀 2", "팀 3", "팀 4", "팀 5"]

# ✅ 대기 선수 목록 불러오기
def load_waiting_players():
    player_file = "waiting_players.txt"
    try:
        with open(player_file, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        return []

# ✅ 서버에서 관리할 경매 상태 (초기화)
auction_state = {}

timer_running = False  # 🔹 타이머 실행 여부 확인

def start_timer():
    """ 타이머 스레드 실행 (1초마다 감소) """
    global timer_running

    if timer_running:  
        print("[디버깅] 타이머가 이미 실행 중입니다. 중복 실행 방지.")
        return

    print("[디버깅] 타이머 시작됨!")
    timer_running = True
    auction_state["remaining_time"] = 10  # 타이머 10초로 초기화

    while auction_state["remaining_time"] > 0:
        time.sleep(1)
        auction_state["remaining_time"] -= 1  # 타이머 감소

        # ✅ **남은 시간 UI에 반영 (log_message 제거)**
        print(f"[디버깅] 현재 남은 시간: {auction_state['remaining_time']}초")

    timer_running = False
    print("[디버깅] 타이머가 0초가 되어 종료됨.")
    finalize_auction_internal()




def finalize_auction_internal():
    """ 유찰/낙찰 처리 함수 """
    global auction_state

    # ✅ 이미 실행 중이면 중복 실행 방지
    if auction_state.get("auction_completed", False):
        print("[디버깅] finalize_auction_internal()가 이미 실행됨! 중복 방지")
        return

    print("[디버깅] finalize_auction_internal() 실행!")
    auction_state["auction_completed"] = True  # ✅ 실행 완료 플래그 설정

    current_player = auction_state.get("current_player", "???")

    if auction_state["highest_bidder"]:
        winning_team = auction_state["highest_bidder"]
        bid_amount = auction_state["current_bid"]

        # ✅ 포인트 차감 (낙찰 후 즉시 반영)
        auction_state["teams"][winning_team]["points"] -= bid_amount

        # ✅ 낙찰된 선수 추가
        auction_state["teams"][winning_team]["members"].append(current_player)

        # ✅ 대기 목록에서 낙찰된 선수 제거
        if current_player in auction_state["waiting_players"]:
            auction_state["waiting_players"].remove(current_player)

        # ✅ **낙찰 로그 추가**
        message = f"✔ ({winning_team}) 팀이 ({current_player}) 님을 {bid_amount} 포인트로 낙찰되었습니다."
        if message not in auction_state["logs"]:
            auction_state["logs"].append(message)

    else:
        # ✅ 유찰된 선수 대기 목록에서 제거
        if current_player in auction_state["waiting_players"]:
            auction_state["waiting_players"].remove(current_player)
        auction_state["unsold_players"].append(current_player)

        message = f"⚠ ({current_player}) 님이 유찰되었습니다."
        if message not in auction_state["logs"]:
            auction_state["logs"].append(message)

    # ✅ **입찰 관련 상태 초기화 (여기가 중요!)**
    auction_state["highest_bidder"] = None
    auction_state["current_bid"] = 0
    auction_state["remaining_time"] = 10

    # ✅ **다음 경매 시작 로그 추가**
    if auction_state["auction_queue"]:
        auction_state["current_player"] = auction_state["auction_queue"].pop(0)
        next_message = f"📢 다음 경매 시작: ({auction_state['current_player']}) 님"
        if next_message not in auction_state["logs"]:
            auction_state["logs"].append(next_message)
    else:
        auction_state["current_player"] = "플레이어 없음"
        next_message = "🏁 모든 경매가 완료되었습니다."
        if next_message not in auction_state["logs"]:
            auction_state["logs"].append(next_message)

    # ✅ **중복 로그 제거**
    auction_state["logs"] = list(dict.fromkeys(auction_state["logs"]))

    # ✅ **경매 종료 후 실행 플래그 해제**
    auction_state["auction_completed"] = False





@app.route("/retry_unsold_players", methods=["POST"])
def retry_unsold_players():
    """ 유찰된 선수들을 다시 경매 목록에 추가 """
    global auction_state

    if not auction_state["unsold_players"]:
        response = jsonify({"message": "유찰된 선수가 없습니다!"}), 400
    else:
        auction_state["auction_queue"].extend(auction_state["unsold_players"])
        auction_state["waiting_players"].extend(auction_state["unsold_players"])  # 🔹 추가
        auction_state["unsold_players"] = []  # 유찰 목록 초기화
        response = jsonify({"message": "유찰된 선수들이 다시 경매 목록에 추가되었습니다!"})

    response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response





@app.route("/start_auction", methods=["POST"])
def start_auction():
    """ 경매 시작 """
    global auction_state

    auction_state = {
        "current_player": "플레이어 없음",
        "current_bid": 0,
        "highest_bidder": None,
        "remaining_time": 10,
        "teams": {team: {"points": 500, "members": []} for team in load_teams()},
        "waiting_players": load_waiting_players(),
        "auction_queue": [],
        "unsold_players": [],
        "logs": []
    }

    auction_state["auction_queue"] = auction_state["waiting_players"][:]
    random.shuffle(auction_state["auction_queue"])

    if auction_state["auction_queue"]:
        auction_state["current_player"] = auction_state["auction_queue"].pop(0)
        response = jsonify({"message": "경매가 시작되었습니다!", "current_player": auction_state["current_player"]})
    else:
        response = jsonify({"message": "대기 선수가 없습니다. 경매를 시작할 수 없습니다."}), 400

    response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response


@app.route("/get_auction_status", methods=["GET"])
def get_auction_status():
    """ 현재 경매 상태 반환 (경매 시작 전에도 기본값 유지) """
    global auction_state

    if not auction_state or "teams" not in auction_state:
        response = jsonify({
            "message": "경매가 아직 시작되지 않았습니다.",
            "current_player": "경매 대기 중",
            "current_bid": 0,
            "highest_bidder": None,
            "remaining_time": 10,
            "teams": {team: {"points": 500, "members": []} for team in load_teams()},
            "waiting_players": load_waiting_players(),
            "unsold_players": [],
            "logs": []
        })
    else:
        # ✅ 중복 제거된 로그를 포함하여 응답
        unique_logs = list(dict.fromkeys(auction_state["logs"]))

        response = jsonify({**auction_state, "logs": unique_logs})

    # ✅ UTF-8 인코딩 적용
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response


@app.route("/start_timer", methods=["POST"])
def start_timer_api():
    """ 타이머 시작 API """
    global timer_running

    if timer_running:
        return jsonify({"message": "타이머가 이미 실행 중입니다!"}), 400

    print("[디버깅] 타이머 실행 시작")  
    auction_state["remaining_time"] = 10  # 타이머 10초로 초기화
    timer_thread = threading.Thread(target=start_timer, daemon=True)
    timer_thread.start()

    return jsonify({"message": "타이머가 시작되었습니다!"})


@app.route("/reset_auction", methods=["POST"])
def reset_auction():
    """ 경매를 강제로 초기화하고 처음부터 다시 시작 """
    global auction_state, timer_running

    timer_running = False  # 기존 타이머 중지
    auction_state = {"logs": []}  # ✅ 로그 초기화

    response = jsonify({"message": "✔ 경매가 초기화되었습니다. '경매 시작' 버튼을 눌러주세요!", "logs": auction_state["logs"]})
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response


@app.route("/place_bid", methods=["POST"])
def place_bid():
    global auction_state, timer_running
    data = request.json
    team_name = data.get("team")
    bid_amount = data.get("bid")

    if not timer_running:
        response = jsonify({"error": "타이머가 시작되지 않았습니다. '시작' 버튼을 눌러주세요!"}), 400
    elif team_name not in auction_state["teams"]:
        response = jsonify({"error": "잘못된 팀 이름"}), 400
    elif auction_state["teams"][team_name]["points"] < bid_amount:
        response = jsonify({"error": "잔여 포인트 부족"}), 400
    elif bid_amount <= auction_state["current_bid"]:
        response = jsonify({"error": "현재 입찰가보다 높아야 합니다."}), 400
    elif len(auction_state["teams"][team_name]["members"]) >= 4:
        response = jsonify({"error": "이 팀은 이미 4명을 영입했습니다!"}), 400
    elif auction_state["highest_bidder"] == team_name:
        response = jsonify({"error": "같은 팀은 연속으로 입찰할 수 없습니다!"}), 400
    else:
        if auction_state["highest_bidder"]:
            previous_bidder = auction_state["highest_bidder"]
            auction_state["teams"][previous_bidder]["points"] += auction_state["current_bid"]

        auction_state["current_bid"] = bid_amount
        auction_state["highest_bidder"] = team_name
        auction_state["teams"][team_name]["points"] -= bid_amount
        auction_state["remaining_time"] = 10

        last_bid_log = f"✔ ({team_name}) 팀이 {bid_amount} 포인트로 입찰했습니다."
        auction_state["logs"].append(last_bid_log)

        response = jsonify({"message": "입찰 성공", "new_bid": auction_state["current_bid"], "logs": [last_bid_log]})

    response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response



@app.route("/")
def home():
    return "Auction Server is running!"






if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render가 할당한 포트 사용
    app.run(host="0.0.0.0", port=port)
