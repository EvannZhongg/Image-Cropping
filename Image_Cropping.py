import os
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox

class ConfigWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("配置裁切工具")
        self.crop_width = tk.IntVar(value=200)
        self.crop_height = tk.IntVar(value=200)
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()

        tk.Label(root, text="裁切框宽度（像素）：").grid(row=0, column=0, padx=10, pady=5)
        tk.Entry(root, textvariable=self.crop_width).grid(row=0, column=1, padx=10, pady=5)

        tk.Label(root, text="裁切框高度（像素）：").grid(row=1, column=0, padx=10, pady=5)
        tk.Entry(root, textvariable=self.crop_height).grid(row=1, column=1, padx=10, pady=5)

        tk.Label(root, text="输入文件夹：").grid(row=2, column=0, padx=10, pady=5)
        tk.Entry(root, textvariable=self.input_folder, state="readonly").grid(row=2, column=1, padx=10, pady=5)
        tk.Button(root, text="选择", command=self.select_input_folder).grid(row=2, column=2, padx=10, pady=5)

        tk.Label(root, text="输出文件夹：").grid(row=3, column=0, padx=10, pady=5)
        tk.Entry(root, textvariable=self.output_folder, state="readonly").grid(row=3, column=1, padx=10, pady=5)
        tk.Button(root, text="选择", command=self.select_output_folder).grid(row=3, column=2, padx=10, pady=5)

        tk.Button(root, text="开始", command=self.start).grid(row=4, column=1, pady=10)

    def select_input_folder(self):
        folder = filedialog.askdirectory(title="选择输入文件夹")
        if folder:
            self.input_folder.set(folder)

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="选择输出文件夹")
        if folder:
            self.output_folder.set(folder)

    def start(self):
        if not self.crop_width.get() or not self.crop_height.get():
            messagebox.showerror("错误", "请输入裁切框的宽度和高度！")
            return
        if not self.input_folder.get() or not self.output_folder.get():
            messagebox.showerror("错误", "请选择输入和输出文件夹！")
            return

        self.root.destroy()
        main_window = tk.Tk()
        main_window.title("图片裁切工具")
        CropApp(main_window, self.input_folder.get(), self.output_folder.get(), (self.crop_width.get(), self.crop_height.get()))
        main_window.mainloop()


class CropApp:
    def __init__(self, root, input_folder, output_folder, crop_box_size):
        self.root = root
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.crop_box_size = crop_box_size  # 原始裁切框尺寸
        self.image_files = [f for f in os.listdir(input_folder)
                            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
        self.current_image_index = 0
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.crop_box = None

        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

        self.canvas = tk.Canvas(root, width=800, height=600, bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 绑定鼠标事件
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.canvas.bind("<ButtonPress-3>", self.start_pan)
        self.canvas.bind("<B3-Motion>", self.pan_image)

        # 按钮区域：两行布局
        btn_frame = tk.Frame(root)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # 第一行：上一张、下一张居中
        nav_frame = tk.Frame(btn_frame)
        nav_frame.pack(pady=5)
        tk.Button(nav_frame, text="上一张", command=self.previous_image).pack(side=tk.LEFT, padx=10)
        tk.Button(nav_frame, text="下一张", command=self.next_image).pack(side=tk.LEFT, padx=10)

        # 第二行：保存裁切居中
        save_frame = tk.Frame(btn_frame)
        save_frame.pack(pady=5)
        tk.Button(save_frame, text="保存裁切", command=self.save_cropped_image).pack()

        self.load_image()

    def load_image(self):
        self.current_image_path = os.path.join(self.input_folder, self.image_files[self.current_image_index])
        self.image = Image.open(self.current_image_path)
        self.original_size = self.image.size
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.update_canvas_image()

    def update_canvas_image(self):
        image_resized = self.image.resize(
            (int(self.original_size[0] * self.scale_factor),
             int(self.original_size[1] * self.scale_factor)),
            Image.LANCZOS
        )
        self.tk_image = ImageTk.PhotoImage(image_resized)
        self.canvas.delete("all")
        self.canvas.create_image(self.offset_x, self.offset_y, anchor=tk.NW, image=self.tk_image)
        # 如果已有裁切框，重新绘制（这里简单处理，重新创建裁切框）
        if self.crop_box:
            self.canvas.delete(self.crop_box)
            crop_w = int(self.crop_box_size[0] * self.scale_factor)
            crop_h = int(self.crop_box_size[1] * self.scale_factor)
            self.crop_box = self.canvas.create_rectangle(50, 50, 50 + crop_w, 50 + crop_h, outline="red")

    def on_mouse_wheel(self, event):
        """鼠标滚轮缩放图片，以鼠标位置为中心"""
        old_scale = self.scale_factor
        scale_step = 1.1 if event.delta > 0 else 0.9
        new_scale = self.scale_factor * scale_step
        if 0.2 <= new_scale <= 3:
            self.scale_factor = new_scale
            mouse_x, mouse_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            self.offset_x = mouse_x - (mouse_x - self.offset_x) * (self.scale_factor / old_scale)
            self.offset_y = mouse_y - (mouse_y - self.offset_y) * (self.scale_factor / old_scale)
            self.update_canvas_image()

    def on_button_press(self, event):
        """鼠标左键按下，开始绘制裁切框"""
        self.start_x, self.start_y = event.x, event.y
        if self.crop_box:
            self.canvas.delete(self.crop_box)
        crop_w = int(self.crop_box_size[0] * self.scale_factor)
        crop_h = int(self.crop_box_size[1] * self.scale_factor)
        self.crop_box = self.canvas.create_rectangle(self.start_x, self.start_y,
                                                       self.start_x + crop_w, self.start_y + crop_h,
                                                       outline="red")

    def on_mouse_drag(self, event):
        """拖动鼠标调整裁切框"""
        if self.crop_box:
            crop_w = int(self.crop_box_size[0] * self.scale_factor)
            crop_h = int(self.crop_box_size[1] * self.scale_factor)
            self.canvas.coords(self.crop_box, event.x, event.y, event.x + crop_w, event.y + crop_h)

    def on_button_release(self, event):
        """记录裁切框的最终坐标（转换为原图坐标）"""
        self.crop_coords = (
            int((event.x - self.offset_x) / self.scale_factor),
            int((event.y - self.offset_y) / self.scale_factor),
            int((event.x - self.offset_x + self.crop_box_size[0] * self.scale_factor) / self.scale_factor),
            int((event.y - self.offset_y + self.crop_box_size[1] * self.scale_factor) / self.scale_factor)
        )

    def start_pan(self, event):
        """记录右键拖动起始位置"""
        self.start_drag_x = event.x
        self.start_drag_y = event.y

    def pan_image(self, event):
        """右键拖动图片"""
        dx = event.x - self.start_drag_x
        dy = event.y - self.start_drag_y
        self.offset_x += dx
        self.offset_y += dy
        self.start_drag_x = event.x
        self.start_drag_y = event.y
        self.update_canvas_image()

    def save_cropped_image(self):
        """保存裁切后的图片（覆盖同名文件）"""
        if hasattr(self, 'crop_coords'):
            cropped_image = self.image.crop(self.crop_coords)
            output_path = os.path.join(self.output_folder,
                                       f"cropped_{self.image_files[self.current_image_index]}")
            cropped_image.save(output_path)
            print(f"裁切后的图片已保存到: {output_path}")

    def next_image(self):
        if self.current_image_index < len(self.image_files) - 1:
            self.current_image_index += 1
            self.load_image()

    def previous_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.load_image()


if __name__ == "__main__":
    config_root = tk.Tk()
    ConfigWindow(config_root)
    config_root.mainloop()
