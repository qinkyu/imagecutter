import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

class ImageCutterApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Batch Square Image Cutter")
        self.image_list = []
        self.current_index = 0
        self.rect = None
        self.start_x = None
        self.start_y = None
        self.crop_box = None
        self.output_size = tk.IntVar(value=512)
        self.default_image_folder = r"C:\work\ai\start"
        self.default_save_folder = r"C:\work\ai\startOut"
        self.image_folder = self.default_image_folder
        self.save_folder = self.default_save_folder
        self.img = None
        self.tk_img = None
        self.handle_size = 8
        self.handles = []
        self.center_handle = None
        self.active_handle = None
        self.active_center = False
        self.info_label = None
        self.move_start = None
        self.image_listbox = None
        self.cut_log = {}
        self.cut_log_path = None
        self.status_label = None

        # UI setup
        self.setup_ui()
        self.master.bind('w', lambda e: self.prev_image())
        self.master.bind('e', lambda e: self.next_image())

    def setup_ui(self):
        # 전체 프레임 좌우 분할
        main_frame = tk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 왼쪽: 폴더 선택/이미지 목록
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        # 이미지 폴더 선택 + Entry (위)
        img_folder_frame = tk.Frame(left_frame)
        img_folder_frame.pack(fill=tk.X)
        tk.Button(img_folder_frame, text="이미지 폴더 선택", command=self.select_image_folder).pack(side=tk.TOP, fill=tk.X)
        self.image_folder_entry = tk.Entry(img_folder_frame, width=40)
        self.image_folder_entry.pack(side=tk.TOP, fill=tk.X, pady=2)
        self.image_folder_entry.insert(0, self.image_folder)
        self.image_folder_entry.bind("<FocusOut>", self.on_image_folder_entry)
        self.image_folder_entry.bind("<Return>", self.on_image_folder_entry)

        # 이미지 목록 Listbox
        tk.Label(left_frame, text="이미지 목록:").pack(anchor=tk.W, pady=(10,0))
        self.image_listbox = tk.Listbox(left_frame, width=40, height=30)
        self.image_listbox.pack(fill=tk.BOTH, expand=True)
        self.image_listbox.bind("<<ListboxSelect>>", self.on_image_select)

        # 저장 폴더 선택 + Entry (아래)
        save_folder_frame = tk.Frame(left_frame)
        save_folder_frame.pack(fill=tk.X, pady=(10,0))
        tk.Button(save_folder_frame, text="저장 폴더 선택", command=self.select_save_folder).pack(side=tk.TOP, fill=tk.X)
        self.save_folder_entry = tk.Entry(save_folder_frame, width=40)
        self.save_folder_entry.pack(side=tk.TOP, fill=tk.X, pady=2)
        self.save_folder_entry.insert(0, self.save_folder)
        self.save_folder_entry.bind("<FocusOut>", self.on_save_folder_entry)
        self.save_folder_entry.bind("<Return>", self.on_save_folder_entry)

        # 오른쪽: 캔버스/컨트롤
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 상단 컨트롤
        ctrl_frame = tk.Frame(right_frame)
        ctrl_frame.pack(side=tk.TOP, fill=tk.X)
        tk.Label(ctrl_frame, text="출력 해상도:").pack(side=tk.LEFT)
        tk.Entry(ctrl_frame, textvariable=self.output_size, width=5).pack(side=tk.LEFT)
        tk.Button(ctrl_frame, text="저장", command=self.save_crop).pack(side=tk.LEFT)
        tk.Button(ctrl_frame, text="다음", command=self.next_image).pack(side=tk.LEFT)
        tk.Button(ctrl_frame, text="이전", command=self.prev_image).pack(side=tk.LEFT)
        tk.Button(ctrl_frame, text="배치실행", command=self.batch_cut).pack(side=tk.LEFT)

        # 캔버스
        self.canvas = tk.Canvas(right_frame, width=600, height=600, cursor="cross", bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        self.info_label = tk.Label(right_frame, text="영역 좌표: 없음 [해상도: -]")
        self.info_label.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_label = tk.Label(self.master, text="", fg="green", anchor="w")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

        # 이미지 목록 초기화 및 자동 로드
        self.on_image_folder_entry(None)

    def select_image_folder(self):
        folder = filedialog.askdirectory(initialdir=self.image_folder)
        if folder:
            self.image_folder = folder
            self.image_folder_entry.delete(0, tk.END)
            self.image_folder_entry.insert(0, folder)
            self.image_list = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
            self.current_index = 0
            self.cut_log_path = os.path.join(self.image_folder, "cut.log")
            self.load_cut_log()
            self.update_image_listbox()
            self.load_image()

    def select_save_folder(self):
        folder = filedialog.askdirectory(initialdir=self.save_folder)
        if folder:
            self.save_folder = folder
            self.save_folder_entry.delete(0, tk.END)
            self.save_folder_entry.insert(0, folder)

    def on_image_folder_entry(self, event):
        folder = self.image_folder_entry.get()
        if os.path.isdir(folder):
            self.image_folder = folder
            self.image_list = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
            self.current_index = 0
            self.cut_log_path = os.path.join(self.image_folder, "cut.log")
            self.load_cut_log()
            self.update_image_listbox()
            self.load_image()
        else:
            messagebox.showerror("오류", "유효한 이미지 폴더 경로를 입력하세요.")

    def on_save_folder_entry(self, event):
        folder = self.save_folder_entry.get()
        if os.path.isdir(folder):
            self.save_folder = folder
        else:
            messagebox.showerror("오류", "유효한 저장 폴더 경로를 입력하세요.")

    def on_image_select(self, event):
        if not self.image_listbox.curselection():
            return
        idx = self.image_listbox.curselection()[0]
        self.current_index = idx
        self.load_image()

    def load_cut_log(self):
        self.cut_log = {}
        if self.cut_log_path and os.path.exists(self.cut_log_path):
            with open(self.cut_log_path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split(",")
                    if len(parts) == 5:
                        fname, x1, y1, x2, y2 = parts
                        self.cut_log[fname] = (int(x1), int(y1), int(x2), int(y2))

    def save_cut_log(self):
        if not self.cut_log_path:
            return
        with open(self.cut_log_path, "w", encoding="utf-8") as f:
            for fname, (x1, y1, x2, y2) in self.cut_log.items():
                f.write(f"{fname},{x1},{y1},{x2},{y2}\n")

    def update_image_listbox(self):
        self.image_listbox.delete(0, tk.END)
        for idx, fname in enumerate(self.image_list):
            self.image_listbox.insert(tk.END, fname)
            if fname in self.cut_log:
                self.image_listbox.itemconfig(idx, {'fg': 'blue'})
            else:
                self.image_listbox.itemconfig(idx, {'fg': 'black'})
        # 현재 선택된 이미지 표시
        if self.image_list:
            self.image_listbox.select_clear(0, tk.END)
            self.image_listbox.select_set(self.current_index)
            self.image_listbox.see(self.current_index)

    def load_image(self):
        if not self.image_list:
            return
        img_path = os.path.join(self.image_folder, self.image_list[self.current_index])
        self.img = Image.open(img_path)
        self.display_image()
        # 사각형 정보가 있으면 표시
        fname = self.image_list[self.current_index]
        if fname in self.cut_log:
            x1, y1, x2, y2 = self.cut_log[fname]
            # 사각형 및 핸들/중앙 핸들 표시
            if self.rect:
                self.canvas.delete(self.rect)
            for handle in self.handles:
                self.canvas.delete(handle)
            self.handles = []
            if self.center_handle:
                self.canvas.delete(self.center_handle)
                self.center_handle = None
            self.rect = self.canvas.create_rectangle(x1, y1, x2, y2, outline='red', width=2)
            self.update_handles()
            self.crop_box = (x1, y1, x2, y2)
            self.update_info_label()

    def display_image(self):
        img = self.img.copy()
        img.thumbnail((600, 600))
        self.thumb_w, self.thumb_h = img.size  # 썸네일 크기 저장
        bg = Image.new("RGB", (600, 600), "black")
        offset = ((600 - self.thumb_w) // 2, (600 - self.thumb_h) // 2)
        self.thumb_offset = offset  # 썸네일 offset 저장
        bg.paste(img, offset)
        self.tk_img = ImageTk.PhotoImage(bg)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)
        self.rect = None
        self.crop_box = None
        self.handles = []
        self.center_handle = None
        self.active_handle = None
        self.active_center = False
        self.update_info_label()

    def on_press(self, event):
        # 핸들 클릭 여부 확인
        for idx, handle in enumerate(self.handles):
            hx1, hy1, hx2, hy2 = self.canvas.coords(handle)
            if hx1 <= event.x <= hx2 and hy1 <= event.y <= hy2:
                self.active_handle = idx
                return
        # 중앙 핸들 클릭 여부 확인
        if self.center_handle:
            cx1, cy1, cx2, cy2 = self.canvas.coords(self.center_handle)
            if cx1 <= event.x <= cx2 and cy1 <= event.y <= cy2:
                self.active_center = True
                self.move_start = (event.x, event.y)
                return
        # 새 사각형 시작: 이전 사각형/핸들 삭제
        if self.rect:
            self.canvas.delete(self.rect)
            self.rect = None
        for handle in self.handles:
            self.canvas.delete(handle)
        self.handles = []
        if self.center_handle:
            self.canvas.delete(self.center_handle)
            self.center_handle = None
        self.active_handle = None
        self.active_center = False
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=2)
        self.handles = []
        self.center_handle = None
        self.active_handle = None
        self.active_center = False

    def on_drag(self, event):
        if self.active_handle is not None and self.rect:
            # 꼭짓점 핸들 이동 (다른 꼭짓점은 고정)
            coords = list(self.canvas.coords(self.rect))
            x1, y1, x2, y2 = coords
            # 네 꼭짓점 중 어느 핸들인지에 따라 좌표 조정
            if self.active_handle == 0:  # 좌상
                new_x, new_y = event.x, event.y
                # 정사각형 유지
                side = min(abs(x2 - new_x), abs(y2 - new_y))
                if x2 > new_x:
                    x1 = x2 - side
                else:
                    x1 = x2 + side
                if y2 > new_y:
                    y1 = y2 - side
                else:
                    y1 = y2 + side
            elif self.active_handle == 1:  # 우상
                new_x, new_y = event.x, event.y
                side = min(abs(new_x - x1), abs(y2 - new_y))
                if new_x > x1:
                    x2 = x1 + side
                else:
                    x2 = x1 - side
                if y2 > new_y:
                    y1 = y2 - side
                else:
                    y1 = y2 + side
            elif self.active_handle == 2:  # 우하
                new_x, new_y = event.x, event.y
                side = min(abs(new_x - x1), abs(new_y - y1))
                if new_x > x1:
                    x2 = x1 + side
                else:
                    x2 = x1 - side
                if new_y > y1:
                    y2 = y1 + side
                else:
                    y2 = y1 - side
            elif self.active_handle == 3:  # 좌하
                new_x, new_y = event.x, event.y
                side = min(abs(x2 - new_x), abs(new_y - y1))
                if x2 > new_x:
                    x1 = x2 - side
                else:
                    x1 = x2 + side
                if new_y > y1:
                    y2 = y1 + side
                else:
                    y2 = y1 - side
            self.canvas.coords(self.rect, x1, y1, x2, y2)
            self.update_handles()
            self.update_info_label()
        elif self.active_center and self.rect:
            # 중앙 핸들 이동: 사각형 전체 이동
            x1, y1, x2, y2 = self.canvas.coords(self.rect)
            dx = event.x - self.move_start[0]
            dy = event.y - self.move_start[1]
            self.move_start = (event.x, event.y)
            self.canvas.coords(self.rect, x1 + dx, y1 + dy, x2 + dx, y2 + dy)
            self.update_handles()
            self.update_info_label()
        elif self.rect:
            # 새 사각형 드래그
            dx = event.x - self.start_x
            dy = event.y - self.start_y
            side = min(abs(dx), abs(dy))
            end_x = self.start_x + side if dx >= 0 else self.start_x - side
            end_y = self.start_y + side if dy >= 0 else self.start_y - side
            self.canvas.coords(self.rect, self.start_x, self.start_y, end_x, end_y)
            self.update_handles()
            self.update_info_label()

    def on_release(self, event):
        if self.rect:
            coords = self.canvas.coords(self.rect)
            self.crop_box = tuple(map(int, coords))
            self.update_handles()
            self.active_handle = None
            self.active_center = False
            self.update_info_label()
            # 사각형 정보 저장
            if self.image_list:
                fname = self.image_list[self.current_index]
                self.cut_log[fname] = tuple(map(int, coords))
                self.save_cut_log()
                self.update_image_listbox()

    def update_handles(self):
        # 사각형 꼭짓점에 핸들 생성/이동, 중앙 핸들 생성/이동
        if not self.rect:
            return
        x1, y1, x2, y2 = self.canvas.coords(self.rect)
        points = [
            (x1, y1),  # 좌상
            (x2, y1),  # 우상
            (x2, y2),  # 우하
            (x1, y2),  # 좌하
        ]
        # 꼭짓점 핸들
        for i, (px, py) in enumerate(points):
            if len(self.handles) < 4:
                handle = self.canvas.create_rectangle(
                    px - self.handle_size, py - self.handle_size,
                    px + self.handle_size, py + self.handle_size,
                    outline='blue', fill='white', width=2
                )
                self.handles.append(handle)
            else:
                self.canvas.coords(
                    self.handles[i],
                    px - self.handle_size, py - self.handle_size,
                    px + self.handle_size, py + self.handle_size
                )
        # 중앙 핸들
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        if not self.center_handle:
            self.center_handle = self.canvas.create_oval(
                cx - self.handle_size, cy - self.handle_size,
                cx + self.handle_size, cy + self.handle_size,
                outline='green', fill='yellow', width=2
            )
        else:
            self.canvas.coords(
                self.center_handle,
                cx - self.handle_size, cy - self.handle_size,
                cx + self.handle_size, cy + self.handle_size
            )

    def update_info_label(self):
        res_info = ""
        if self.img:
            img_w, img_h = self.img.size
            res_info = f" [해상도: {img_w}x{img_h}]"

            if self.rect:
                x1, y1, x2, y2 = map(int, self.canvas.coords(self.rect))
                thumb_w, thumb_h = self.thumb_w, self.thumb_h
                offset_x, offset_y = self.thumb_offset
                
                scale_x, scale_y = img_w / thumb_w, img_h / thumb_h
                ix1 = int((min(x1, x2) - offset_x) * scale_x)
                iy1 = int((min(y1, y2) - offset_y) * scale_y)
                ix2 = int((max(x1, x2) - offset_x) * scale_x)
                iy2 = int((max(y1, y2) - offset_y) * scale_y)
                
                self.info_label.config(text=f"영역 좌표: ({ix1}, {iy1}) ~ ({ix2}, {iy2}){res_info}")
                return

        self.info_label.config(text=f"영역 좌표: 없음{res_info}")

    def set_status(self, msg):
        self.status_label.config(text=msg)

    def save_crop(self):
        if not self.crop_box or not self.save_folder:
            self.set_status("영역을 선택하고 저장 폴더를 지정하세요.")
            return

        img_w, img_h = self.img.size
        thumb_w, thumb_h = self.thumb_w, self.thumb_h
        offset_x, offset_y = self.thumb_offset
        x1, y1, x2, y2 = self.crop_box
        
        # 썸네일 기준 좌표 (정규화)
        tx1, ty1 = min(x1, x2) - offset_x, min(y1, y2) - offset_y
        tx2, ty2 = max(x1, x2) - offset_x, max(y1, y2) - offset_y
        
        # 원본 이미지 기준 좌표 변환
        scale_x, scale_y = img_w / thumb_w, img_h / thumb_h
        ix1, iy1 = int(tx1 * scale_x), int(ty1 * scale_y)
        ix2, iy2 = int(tx2 * scale_x), int(ty2 * scale_y)
        
        crop_w, crop_h = ix2 - ix1, iy2 - iy1
        if crop_w <= 0 or crop_h <= 0: return

        # 블랙 배경 생성 및 유효 영역 복사
        result_img = Image.new("RGB", (crop_w, crop_h), "black")
        sx1, sy1 = max(0, ix1), max(0, iy1)
        sx2, sy2 = min(img_w, ix2), min(img_h, iy2)
        
        if sx2 > sx1 and sy2 > sy1:
            cropped_part = self.img.crop((sx1, sy1, sx2, sy2))
            result_img.paste(cropped_part, (sx1 - ix1, sy1 - iy1))
            
        size = self.output_size.get()
        result_img = result_img.resize((size, size), Image.LANCZOS)
        save_name = f"square_{os.path.splitext(self.image_list[self.current_index])[0]}.png"
        save_path = os.path.join(self.save_folder, save_name)
        result_img.save(save_path, format="PNG")
        self.set_status(f"{save_name} 저장됨.")

    def batch_cut(self):
        if not self.save_folder:
            self.set_status("저장 폴더를 지정하세요.")
            return
        count = 0
        for fname in self.image_list:
            if fname in self.cut_log:
                img_path = os.path.join(self.image_folder, fname)
                img = Image.open(img_path)
                img_w, img_h = img.size
                # 썸네일 생성 및 크기/offset 계산
                thumb = img.copy()
                thumb.thumbnail((600, 600))
                thumb_w, thumb_h = thumb.size
                offset_x = (600 - thumb_w) // 2
                offset_y = (600 - thumb_h) // 2
                x1, y1, x2, y2 = self.cut_log[fname]
                tx1, ty1 = min(x1, x2) - offset_x, min(y1, y2) - offset_y
                tx2, ty2 = max(x1, x2) - offset_x, max(y1, y2) - offset_y
                
                scale_x, scale_y = img_w / thumb_w, img_h / thumb_h
                ix1, iy1 = int(tx1 * scale_x), int(ty1 * scale_y)
                ix2, iy2 = int(tx2 * scale_x), int(ty2 * scale_y)
                
                crop_w, crop_h = ix2 - ix1, iy2 - iy1
                if crop_w > 0 and crop_h > 0:
                    result_img = Image.new("RGB", (crop_w, crop_h), "black")
                    sx1, sy1 = max(0, ix1), max(0, iy1)
                    sx2, sy2 = min(img_w, ix2), min(img_h, iy2)
                    
                    if sx2 > sx1 and sy2 > sy1:
                        cropped_part = img.crop((sx1, sy1, sx2, sy2))
                        result_img.paste(cropped_part, (sx1 - ix1, sy1 - iy1))
                        
                    size = self.output_size.get()
                    result_img = result_img.resize((size, size), Image.LANCZOS)
                    save_name = f"square_{os.path.splitext(fname)[0]}.png"
                    save_path = os.path.join(self.save_folder, save_name)
                    result_img.save(save_path, format="PNG")
                    count += 1
        self.set_status(f"{count}개 이미지 저장됨.")

    def next_image(self):
        if self.image_list and self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self.load_image()
            self.update_image_listbox()

    def prev_image(self):
        if self.image_list and self.current_index > 0:
            self.current_index -= 1
            self.load_image()
            self.update_image_listbox()

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageCutterApp(root)
    root.mainloop()
