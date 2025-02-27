import tkinter as tk
from tkinter import ttk
import requests  # 서버와 통신하기 위한 모듈
from PIL import Image, ImageTk  # 🔹 선수 사진 표시를 위한 라이브러리
import os

# 🔹 최소 입찰 금액 설정
MIN_BID_AMOUNT = 10

class AuctionApp:
    def __init__(self, root):
        self.teams = self.load_teams()
        self.team_var = tk.StringVar()

        if self.teams:
            self.team_var.set(self.teams[0])

        self.root = root
        self.root.title("또기안또기 롤 리그 경매 프로그램")
        self.root.geometry("1920x1080")
        self.root.configure(bg="#1E1E1E")

        # ✅ 메인 프레임 생성
        self.main_frame = tk.Frame(self.root, bg="#1E1E1E")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # 🔹 대기 선수 목록 불러오기
        self.waiting_players = self.load_waiting_players()

        # ✅ 상단 버튼 프레임 (버튼 3개를 포함할 새로운 프레임)
        self.control_frame = tk.Frame(self.root, bg="#2E2E2E", height=50)
        self.control_frame.pack(fill="x", padx=10, pady=5)  # ← ❗이 코드가 없으면 버튼이 표시되지 않음


        # ✅ '경매 시작' 버튼 (맨 왼쪽)
        self.start_button = tk.Button(
        self.control_frame, text="경매 시작", font=("Arial", 14),
        bg="green", fg="white", width=12, command=self.start_auction
        )
        self.start_button.pack(side="left", padx=10)

        # ✅ '다음 선수' 버튼 (가운데)
        #self.next_button = tk.Button(
        #self.control_frame, text="다음 선수", font=("Arial", 14),
        #bg="blue", fg="white", width=12, command=self.next_player
        #)
        #self.next_button.pack(side="left", padx=10)  # ← ❗ 이거 없으면 안보임

        # ✅ "시작" 버튼 (타이머 수동 실행)
        self.timer_start_button = tk.Button(
        self.control_frame, text="시작", font=("Arial", 14),
        bg="orange", fg="white", width=12, command=self.start_timer
        )
        self.timer_start_button.pack(side="left", padx=10)


        # ✅ 기존 '경매 초기화' 버튼 (오른쪽)
        self.reset_button = tk.Button(
        self.control_frame, text="경매 초기화", font=("Arial", 14),
        bg="red", fg="white", width=12, command=self.reset_auction
        )
        self.reset_button.pack(side="left", padx=10)

        # 🌟 상단 팀 선택 UI
        self.team_select_frame = tk.Frame(self.root, bg="#2E2E2E", height=50)
        self.team_select_frame.pack(fill="x", padx=10, pady=5)

        self.team_select_label = tk.Label(self.team_select_frame, text="자신의 팀을 선택하세요: ",
                                          fg="white", bg="#2E2E2E", font=("Arial", 14))
        self.team_select_label.pack(side="left", padx=10)

        self.team_dropdown = ttk.Combobox(self.team_select_frame, textvariable=self.team_var,
                                          values=self.teams, state="readonly")
        self.team_dropdown.pack(side="left", padx=10)
        self.team_dropdown["values"] = self.teams


        # ✅ 팀 정보 프레임
        self.left_frame = tk.Frame(self.main_frame, bg="#2E2E2E", width=700)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        self.team_labels = []
        for i, team_name in enumerate(self.teams):
            team_section = tk.Frame(self.left_frame, bg="#3A3A3A", pady=10)
            team_section.pack(fill="x", pady=5)

            team_label = tk.Label(team_section, text=f"{team_name} - 포인트: 500",
                                  fg="white", bg="#3A3A3A", font=("Arial", 16))
            team_label.pack(anchor="w", padx=10)

            team_players = tk.Label(team_section, text="팀원: ???, ???, ???, ???",
                                    fg="lightgray", bg="#3A3A3A", font=("Arial", 14))
            team_players.pack(anchor="w", padx=10)

            self.team_labels.append((team_label, team_players))

        # ✅ 중앙 프레임 정의 (경매 관련 UI가 포함될 공간)
        self.center_frame = tk.Frame(self.main_frame, bg="#3E3E3E", width=768)
        self.center_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        # ✅ 중앙 프레임 안에 선수 이미지와 입찰 정보를 포함하는 `self.center_top_frame` 추가
        self.center_top_frame = tk.Frame(self.center_frame, bg="#2E2E2E")
        self.center_top_frame.pack(pady=10)  # 🔹 전체 여백 추가

        # ✅ `grid()`를 사용해 2개 열로 정렬 (이미지 왼쪽, 입찰 정보 오른쪽)
        self.center_top_frame.columnconfigure(0, weight=1)  # 왼쪽: 선수 이미지
        self.center_top_frame.columnconfigure(1, weight=1)  # 오른쪽: 입찰 정보

        # ✅ 선수 이미지 추가 (왼쪽 정렬)
        self.player_image_label = tk.Label(self.center_top_frame, bg="#2E2E2E")
        self.player_image_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")  # 🔹 왼쪽 정렬

        # ✅ 기존 입찰 정보 (오른쪽 정렬)
        self.player_info_frame = tk.Frame(self.center_top_frame, bg="#2E2E2E")
        self.player_info_frame.grid(row=0, column=1, padx=10, pady=5, sticky="e")  # 🔹 오른쪽 정렬

        self.player_label = tk.Label(self.player_info_frame, text="입찰 중: ???",
                                    fg="white", bg="#2E2E2E", font=("Arial", 18))
        self.player_label.pack(anchor="w")

        self.bid_label = tk.Label(self.player_info_frame, text="현재 입찰가: 0 포인트",
                                fg="white", bg="#2E2E2E", font=("Arial", 16))
        self.bid_label.pack(anchor="w")

        self.timer_label = tk.Label(self.player_info_frame, text="남은 시간: 10초",
                                    fg="red", bg="#2E2E2E", font=("Arial", 16))
        self.timer_label.pack(anchor="w")


        # ✅ 경매 로그
        self.log_frame = tk.Frame(self.center_frame, bg="#252525")
        self.log_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.log_text = tk.Text(self.log_frame, bg="#252525", fg="white",
                                font=("Arial", 14), height=8)
        self.log_text.pack(fill="both", expand=True)

        # ✅ 입찰 버튼 및 포인트 정보
        self.bid_frame = tk.Frame(self.center_frame, bg="#1E1E1E")
        self.bid_frame.pack(fill="x", padx=10, pady=10)

        self.point_label = tk.Label(self.bid_frame, text="잔여 포인트: ???",
                                    fg="white", bg="#1E1E1E", font=("Arial", 14))
        self.point_label.pack(side="left", padx=10)

        self.bid_amount_label = tk.Label(self.bid_frame, text="입찰 예정 금액: 0 포인트",
                                         fg="white", bg="#1E1E1E", font=("Arial", 14))
        self.bid_amount_label.pack(side="left", padx=10)

        # ✅ 입찰 금액 버튼
        self.bid_buttons = []
        for amount in [5, 10, 50, 100, 500]:
            btn = tk.Button(self.bid_frame, text=f"+{amount}", font=("Arial", 12),
                            width=6, command=lambda amt=amount: self.update_bid_amount(amt))
            btn.pack(side="left", padx=5)
            self.bid_buttons.append(btn)

        self.bid_button = tk.Button(self.bid_frame, text="입찰", font=("Arial", 12),
                                    bg="gold", width=8, command=self.submit_bid)
        self.bid_button.pack(side="left", padx=10)

        # 🔹 초기화 버튼 추가 (입찰 버튼 옆)
        self.reset_button = tk.Button(self.bid_frame, text="초기화", font=("Arial", 12),
                                      bg="red", fg="white", width=8, command=self.reset_bid_amount)
        self.reset_button.pack(side="left", padx=5)


    


        # ✅ 우측 대기 선수 목록
        self.right_frame = tk.Frame(self.main_frame, bg="#2E2E2E", width=500)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=5)

        self.waiting_label = tk.Label(self.right_frame, text="대기 선수 목록",
                                      fg="white", bg="#2E2E2E", font=("Arial", 16))
        self.waiting_label.pack()

        self.waiting_list = tk.Listbox(self.right_frame, bg="#555555", fg="white",
                                       font=("Arial", 14), height=20)
        self.waiting_list.pack(fill="both", expand=True, pady=5)

        # ✅ 유찰된 선수 목록 추가
        self.unsold_label = tk.Label(self.right_frame, text="유찰된 선수 목록",
                                     fg="white", bg="#2E2E2E", font=("Arial", 16))
        self.unsold_label.pack(pady=10)

        self.unsold_list = tk.Listbox(self.right_frame, bg="#555555", fg="white",
                                      font=("Arial", 14), height=5)
        self.unsold_list.pack(fill="x", pady=5)

        # ✅ "유찰 선수 다시 경매" 버튼 추가
        self.retry_unsold_button = tk.Button(
             self.right_frame, text="유찰 선수 복원", font=("Arial", 12),
              bg="purple", fg="white", width=18, command=self.retry_unsold_players
        )
        self.retry_unsold_button.pack(pady=5)
        

        # 🔹 초기화 버튼 추가
        self.reset_button = tk.Button(self.right_frame, text="목록 새로고침", font=("Arial", 12),
                                      bg="blue", fg="white", width=12, command=self.update_auction_status)
        self.reset_button.pack(pady=10)

        # ✅ "경매 초기화" 버튼 추가
        #self.reset_auction_button = tk.Button(
        #    self.team_select_frame, text="경매 초기화", font=("Arial", 14),
        #    bg="red", fg="white", command=self.reset_auction)
        #self.reset_auction_button.pack(side="right", padx=10)


        # 자동 UI 업데이트 실행
        self.update_auction_status()

    def update_auction_status(self):
        """ 서버에서 최신 경매 상태를 가져와 UI에 반영 """
        try:
            response = requests.get("http://127.0.0.1:5000/get_auction_status")
            if response.status_code == 200:
                data = response.json()

                # ✅ **경매가 시작되지 않았을 경우 메시지 처리 추가**
                if "message" in data and data["message"] == "경매가 아직 시작되지 않았습니다.":
                    self.player_label.config(text="경매 대기 중")
                    self.bid_label.config(text="현재 입찰가: 0 포인트")
                    self.timer_label.config(text="남은 시간: 10초")

                    # ✅ **기존 로그와 비교하여 중복되지 않은 로그만 추가**
                    current_logs = set(self.log_text.get("1.0", tk.END).strip().split("\n"))
                    for log in data["logs"]:
                        if log not in current_logs:
                            self.log_text.insert(tk.END, log + "\n")

                    # 기본 이미지 표시
                    default_img = Image.open("images/안또기.png")
                    default_img = default_img.resize((450, 450))
                    default_photo = ImageTk.PhotoImage(default_img)
                    self.player_image_label.config(image=default_photo)
                    self.player_image_label.image = default_photo  # 참조 유지

                    return  # 경매가 아직 시작되지 않았으므로 추가 업데이트 X
                
                
                # ✅ **경매 상태 업데이트**
                highest_bidder = data.get("highest_bidder", "없음")
                self.player_label.config(
                    text=f"입찰 중: {data.get('current_player', '없음')} (입찰자: {highest_bidder})"
                )
                self.bid_label.config(
                    text=f"현재 입찰가: {data.get('current_bid', 0)} 포인트"
                )
                
                # ✅ **남은 시간 갱신**
                remaining_time = data.get("remaining_time", 10)
                self.timer_label.config(text=f"남은 시간: {remaining_time}초")

                # ✅ **대기 선수 목록 업데이트 추가**
                self.waiting_list.delete(0, tk.END)  # 기존 목록 초기화
                for player in data["waiting_players"]:  # 서버에서 대기 선수 목록 가져오기
                    self.waiting_list.insert(tk.END, player)

                # ✅ **유찰 선수 목록 업데이트 추가**
                self.unsold_list.delete(0, tk.END)  # 기존 목록 초기화
                for player in data["unsold_players"]:  # 서버에서 유찰된 선수 목록 가져오기
                    self.unsold_list.insert(tk.END, player)

                
                # ✅ **중앙 상단 선수 사진 업데이트**
                player_name = data.get("current_player", "없음")
                image_path = f"images/{player_name}.png"  # 🔹 선수 이미지 경로 (폴더에 저장된 선수 사진)

                if os.path.exists(image_path):
                    img = Image.open(image_path)
                else:
                    img = Image.open("images/안또기.png")  # 🔹 기본 이미지 사용

                img = img.resize((450, 450))  # ✅ 크기 조정
                photo = ImageTk.PhotoImage(img)
                self.player_image_label.config(image=photo)
                self.player_image_label.image = photo  # 🔹 참조 유지

                
                # ✅ **중복 로그 방지: 기존 로그와 비교 후 추가**
                current_logs = set(self.log_text.get("1.0", tk.END).strip().split("\n"))
                new_logs = [log for log in data["logs"] if log not in current_logs]

                for log in new_logs:
                    self.log_text.insert(tk.END, log + "\n")
                
                # ✅ 최대 100줄까지만 유지 (오래된 로그 삭제)
                all_logs = self.log_text.get("1.0", tk.END).strip().split("\n")
                if len(all_logs) > 100:
                    self.log_text.delete("1.0", f"{len(all_logs) - 100}.0")

                self.log_text.see(tk.END)  # 스크롤을 아래로 이동

                
                # ✅ **선택한 팀의 잔여 포인트 업데이트**
                selected_team = self.team_var.get()
                if selected_team and selected_team in data.get("teams", {}):
                    self.point_label.config(
                        text=f"잔여 포인트: {data['teams'][selected_team]['points']} 포인트"
                    )
                else:
                    self.point_label.config(text="잔여 포인트: 알 수 없음")



                # ✅ 왼쪽 팀 목록 업데이트 (포인트 및 팀원 목록 포함)
                for team_label, team_players in self.team_labels:
                    team_name = team_label.cget("text").split(" - ")[0]  # 팀명 추출
                    if team_name in data["teams"]:
                        # 🔹 포인트 업데이트
                        team_label.config(
                            text=f"{team_name} - 포인트: {data['teams'][team_name]['points']}")

                        # 🔹 팀원 목록 업데이트
                        members = data["teams"][team_name]["members"]
                        if members:
                            team_players.config(text=f"팀원: {', '.join(members)}")
                        else:
                            team_players.config(text="팀원: ???")  # 기본값 유지






        except requests.exceptions.RequestException:
            print("서버 연결 실패")

        # ✅ **경매가 진행 중일 때만 업데이트 반복**
        if data.get("current_player") != "플레이어 없음":
            self.root.after(1000, self.update_auction_status)


    def update_bid_amount(self, amount):
        """ 입찰 예정 금액을 업데이트하는 함수 """
        text = self.bid_amount_label.cget("text")
        bid_str = ''.join(filter(str.isdigit, text))
        current_bid = int(bid_str) if bid_str else 0

        print(f"[디버깅] 현재 입찰 금액: {current_bid}, 추가할 금액: {amount}")

        # 🔹 보유 포인트 가져오기
        team_name = self.team_var.get()
        team_points = self.get_team_points(team_name)

        new_bid = current_bid + amount

        # 🔹 보유 포인트보다 높으면 초기화 (0 포인트)
        if new_bid > team_points:
            print("[디버깅] 보유 포인트 초과!")
            self.log_text.insert(
                tk.END, f"⚠ 보유 포인트보다 높습니다! (최대 {team_points} 포인트 가능)\n")
            self.bid_amount_label.config(text="입찰 예정 금액: 0 포인트")
        else:
            print(f"[디버깅] 새로운 입찰 금액: {new_bid}")
            self.bid_amount_label.config(
                text=f"입찰 예정 금액: {new_bid} 포인트")

    def submit_bid(self):
        """ 입찰 버튼 클릭 시 서버로 요청을 보내는 함수 """
        team_name = self.team_var.get()
        if not team_name:
            self.log_text.insert(tk.END, "⚠ 팀을 먼저 선택하세요!\n")
            self.log_text.see(tk.END)
            return

        # 🔹 숫자만 추출해서 변환
        text = self.bid_amount_label.cget("text")
        bid_str = ''.join(filter(str.isdigit, text))
        bid_amount = int(bid_str) if bid_str else 0

        if bid_amount < MIN_BID_AMOUNT:
            self.log_text.insert(
                tk.END, f"⚠ 최소 입찰 금액은 {MIN_BID_AMOUNT} 포인트입니다!\n")
            self.log_text.see(tk.END)
            return

        try:
            response = requests.post(
                "http://127.0.0.1:5000/place_bid",
                json={"team": team_name, "bid": bid_amount}
            )
            data = response.json()
            if "error" in data:
                self.log_text.insert(tk.END, f"❌ 입찰 실패: {data['error']}\n")
            else:
                # ✅ 기존 로그와 비교 후 중복 방지
                current_logs = set(self.log_text.get("1.0", tk.END).strip().split("\n"))
                for log in data["logs"]:
                    if log not in current_logs:
                        self.log_text.insert(tk.END, log + "\n")
                
                    # ✅ **입찰 후 즉시 UI 업데이트**
                self.update_auction_status()  

                self.bid_amount_label.config(text="입찰 예정 금액: 0 포인트")


                # ✅ 낙찰된 선수를 팀원 목록에 추가
                self.update_team_members(team_name)

                self.update_auction_status()

        except requests.exceptions.RequestException:
            self.log_text.insert(tk.END, "❌ 서버 연결 실패\n")
            self.log_text.see(tk.END)

    def update_team_members(self, team_name):
        """ 낙찰된 선수를 해당 팀의 팀원 목록에 추가 (최대 4명까지) """
        if self.waiting_list.size() > 0:
            player_name = self.waiting_list.get(0)
            self.waiting_list.delete(0)

            for team_label, team_players in self.team_labels:
                if team_name in team_label.cget("text"):
                    current_players = team_players.cget(
                        "text").replace("팀원: ", "").split(", ")
                    current_players = [
                        p for p in current_players if p != "???" and p != "없음"]

                    if len(current_players) < 4:
                        current_players.append(player_name)
                    else:
                        self.unsold_list.insert(tk.END, player_name)

                    team_players.config(text=f"팀원: {', '.join(current_players)}")
                    break

    def get_team_points(self, team_name):
        """ 현재 팀의 보유 포인트를 가져오는 함수 (서버 데이터 사용) """
        try:
            response = requests.get("http://127.0.0.1:5000/get_auction_status")
            if response.status_code == 200:
                data = response.json()
                return data["teams"].get(team_name, {}).get("points", 0)  # 🔹 딕셔너리에서 포인트 값만 가져오기
        except requests.exceptions.RequestException:
            print("서버 연결 실패")
        return 0  # 기본값  

    def load_teams(self):
        """팀 목록을 파일에서 불러오는 함수"""
        team_file = "team_list.txt"
        if os.path.exists(team_file):  # 파일이 존재하면
            with open(team_file, "r", encoding="utf-8") as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        return ["팀 1", "팀 2", "팀 3", "팀 4", "팀 5"]  # 기본값

    def load_waiting_players(self):
        """대기 선수 목록을 파일에서 불러오는 함수"""
        player_file = "waiting_players.txt"
        if os.path.exists(player_file):  # 파일이 존재하면
            with open(player_file, "r", encoding="utf-8") as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        return []  # 기본값 없음 (대기 선수 없음)

    def reset_bid_amount(self):
        """ 🔹 입찰 금액을 0으로 초기화하는 함수 """
        self.bid_amount_label.config(text="입찰 예정 금액: 0 포인트")

    def reset_auction(self):
        """ 서버에 경매 초기화 요청을 보내는 함수 """
        try:
            response = requests.post("http://127.0.0.1:5000/reset_auction")
            data = response.json()
            # ✅ **로그창 초기화**
            self.log_text.delete("1.0", tk.END)
            # ✅ **새로운 메시지 추가**
            self.log_text.insert(tk.END, f"✔ {data['message']}\n")
            self.update_auction_status()  # ✅ 초기화 후 UI 갱신
            # ✅ 경매 시작 버튼 다시 활성화
            
            self.start_button.config(state=tk.NORMAL)
        except requests.exceptions.RequestException:
            self.log_text.insert(tk.END, "❌ 서버 연결 실패\n")

    def retry_unsold_players(self):
        """ 유찰된 선수를 다시 경매 목록에 추가하는 요청을 서버에 보냄 """
        try:
            response = requests.post("http://127.0.0.1:5000/retry_unsold_players")
            data = response.json()
            self.log_text.insert(tk.END, f"✔ {data['message']}\n")
            self.update_auction_status()
        except requests.exceptions.RequestException:
            self.log_text.insert(tk.END, "❌ 서버 연결 실패\n")

    def start_auction(self):
        """ '경매 시작' 버튼을 눌렀을 때 서버에 경매 시작 요청 """
        try:
            response = requests.post("http://127.0.0.1:5000/start_auction")
            data = response.json()
            self.log_text.insert(tk.END, f"✔ {data['message']}\n")
            self.update_auction_status()  # 상태 업데이트
            # ✅ 경매 시작 버튼 비활성화

            self.start_button.config(state=tk.DISABLED)

        except requests.exceptions.RequestException:
            self.log_text.insert(tk.END, "❌ 서버 연결 실패\n")

    def next_player(self):
        """ '다음 선수' 버튼을 눌렀을 때 서버에서 다음 선수 요청 """
        try:
            response = requests.post("http://127.0.0.1:5000/finalize_auction")
            data = response.json()
            self.log_text.insert(tk.END, f"✔ {data['message']}\n")

        # 🔹 UI 업데이트 (대기 선수, 유찰된 선수, 현재 선수 정보)
            self.update_auction_status()
        except requests.exceptions.RequestException:
            self.log_text.insert(tk.END, "❌ 서버 연결 실패\n")

    def start_timer(self):
        """ '시작' 버튼을 눌렀을 때 서버에서 타이머 실행 """
        try:
            response = requests.post("http://127.0.0.1:5000/start_timer")
            data = response.json()
            self.log_text.insert(tk.END, f"✔ {data['message']}\n")
            self.update_auction_status()
        except requests.exceptions.RequestException:
            self.log_text.insert(tk.END, "❌ 서버 연결 실패\n")






root = tk.Tk()
app = AuctionApp(root)
root.mainloop()
