import asyncio
import ctypes
import json
import os
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import discord

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_FILES = None
    TkinterDnD = None
    DND_AVAILABLE = False

PINK = "#F4B8D0"
PALE = "#FFF5F9"
WHITE = "#FFFFFF"
TEXT = "#75485D"
MUTED = "#A77B90"
CONFIG_FILE = "config.json"
IMAGE_TYPES = (".png", ".jpg", ".jpeg", ".gif", ".webp")
SHORTCUT_TAG = "LaftelPostShortcuts"


def natural_sort_key(path):
    """Sort filenames as humans expect: 1, 2, 10 instead of 1, 10, 2."""
    name = os.path.basename(path).casefold()
    return [int(part) if part.isdigit() else part
            for part in re.split(r"(\d+)", name)]


class PostSendError(Exception):
    def __init__(self, message, sent, original=None):
        super().__init__(message)
        self.sent = sent
        self.original = original


class LaftelPost:
    def __init__(self, root):
        self.root = root
        self.root.title("Laftel Post")
        self.root.geometry("920x570")
        self.root.minsize(800, 500)
        self.root.configure(bg=PALE)

        self.busy = False
        self.image_paths = []
        self.config = self.load_config()
        self.setup_keyboard_shortcuts()

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        header = tk.Frame(root, bg=PALE)
        header.pack(fill="x", padx=18, pady=(10, 4))

        tk.Label(
            header, text="♡  Laftel Post",
            font=("Segoe UI", 21, "bold"), bg=PALE, fg=TEXT
        ).pack(anchor="w")

        tk.Label(
            header,
            text="FREE EDITION  •  โพสต์หลายรูปแยกข้อความอัตโนมัติ",
            font=("Segoe UI", 10), bg=PALE, fg=MUTED
        ).pack(anchor="w", pady=(2, 0))

        self.settings_card = tk.Frame(
            root, bg=WHITE, highlightbackground="#F5D7E4",
            highlightthickness=1
        )
        self.settings_card.pack(fill="x", padx=18, pady=4)

        tk.Label(
            self.settings_card, text="Bot Token", bg=WHITE, fg=TEXT,
            font=("Segoe UI", 9, "bold")
        ).grid(row=0, column=0, sticky="w", padx=(10, 5), pady=7)

        self.token = tk.Entry(
            self.settings_card, show="•", font=("Segoe UI", 10),
            relief="flat", bg=PALE, fg=TEXT, width=34
        )
        self.token.grid(row=0, column=1, sticky="ew", padx=4, pady=7, ipady=4)
        self.token.insert(0, self.config.get("bot_token", ""))

        tk.Label(
            self.settings_card, text="Channel ID", bg=WHITE, fg=TEXT,
            font=("Segoe UI", 9, "bold")
        ).grid(row=0, column=2, sticky="w", padx=(12, 5), pady=7)

        self.channel = tk.Entry(
            self.settings_card, font=("Segoe UI", 10),
            relief="flat", bg=PALE, fg=TEXT, width=22
        )
        self.channel.grid(row=0, column=3, sticky="ew", padx=(4, 10), pady=7, ipady=4)
        self.channel.insert(0, self.config.get("channel_id", ""))
        self.settings_card.grid_columnconfigure(1, weight=1)
        self.settings_card.grid_columnconfigure(3, weight=1)

        self.bind_shortcuts(self.token)
        self.bind_shortcuts(self.channel)

        top_action = tk.Frame(root, bg=PALE)
        top_action.pack(fill="x", padx=18, pady=(3, 5))

        self.post = tk.Button(
            top_action, text="♡  POST TO DISCORD  ♡", command=self.start,
            bg=PINK, fg=WHITE, activebackground="#E99DBD",
            activeforeground=WHITE, font=("Segoe UI", 11, "bold"),
            relief="flat", bd=0, cursor="hand2", padx=22
        )
        self.post.pack(side="right", ipady=6)

        self.status = tk.Label(
            top_action, text="พร้อมใช้งาน ✿", bg=PALE, fg=TEXT,
            font=("Segoe UI", 9)
        )
        self.status.pack(side="left", pady=5)

        area = tk.Frame(root, bg=PALE)
        area.pack(fill="both", expand=True, padx=18, pady=(3, 4))

        left_panel = tk.Frame(area, bg=PALE)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))

        right_panel = tk.Frame(area, bg=PALE)
        right_panel.pack(side="left", fill="both", expand=True, padx=(8, 0))

        tk.Label(
            left_panel, text="รูปแบบข้อความ",
            font=("Segoe UI", 11, "bold"), bg=PALE, fg=TEXT
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(
            right_panel, text="เพิ่มและจัดการรูปภาพ",
            font=("Segoe UI", 11, "bold"), bg=PALE, fg=TEXT
        ).pack(anchor="w", pady=(0, 4))

        naming_card = tk.Frame(
            left_panel, bg=WHITE, highlightbackground="#F5D7E4",
            highlightthickness=1
        )
        naming_card.pack(fill="x", pady=(0, 8))

        tk.Label(
            naming_card, text="รูปแบบข้อความ (แก้ไขได้หลายบรรทัด)",
            bg=WHITE, fg=TEXT, font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", padx=14, pady=(10, 5))

        self.caption_template = tk.Text(
            naming_card, height=3, wrap="word",
            font=("Segoe UI", 11), bg=PALE, fg=TEXT,
            relief="flat", padx=9, pady=7, undo=True
        )
        self.caption_template.pack(fill="x", padx=14, pady=(0, 6))
        default_template = self.config.get(
            "caption_template", "♡﹒**hair 60**\n♡﹒price : 59.-"
        )
        self.caption_template.insert("1.0", default_template)
        self.bind_shortcuts(self.caption_template)

        tk.Label(
            naming_card,
            text="โปรแกรมจะเปลี่ยนเฉพาะตัวเลขในบรรทัดแรก เช่น 60, 61, 62 ... ส่วนบรรทัดอื่นคงเดิม",
            bg=WHITE, fg=MUTED, font=("Segoe UI", 9),
            wraplength=650, justify="left"
        ).pack(anchor="w", padx=14, pady=(0, 10))

        drop_card = tk.Frame(
            right_panel, bg=WHITE, highlightbackground="#F5D7E4",
            highlightthickness=1
        )
        drop_card.pack(fill="x", pady=(0, 8))

        self.drop_label = tk.Label(
            drop_card,
            text=("ลากรูปภาพมาวางที่นี่ได้เลย  ♡\n"
                  "รองรับ PNG, JPG, JPEG, GIF, WEBP"
                  if DND_AVAILABLE else
                  "เลือกภาพหลายรูปพร้อมกันได้  ♡\n"
                  "ติดตั้งส่วนเสริม Drag & Drop ไม่สำเร็จ"),
            bg=PALE, fg=TEXT, font=("Segoe UI", 11, "bold"),
            justify="center", padx=10, pady=18,
            relief="flat"
        )
        self.drop_label.pack(fill="x", padx=12, pady=12)

        if DND_AVAILABLE:
            try:
                self.drop_label.drop_target_register(DND_FILES)
                self.drop_label.dnd_bind("<<Drop>>", self.on_drop)
            except Exception:
                self.drop_label.config(
                    text="ใช้ปุ่มเลือกรูปภาพด้านล่างเพื่อเพิ่มรูป"
                )

        button_row = tk.Frame(right_panel, bg=PALE)
        button_row.pack(fill="x", pady=(0, 6))

        self.add_button = tk.Button(
            button_row, text="＋ เลือกรูปภาพ", command=self.choose_images,
            bg=PINK, fg=WHITE, activebackground="#E99DBD",
            relief="flat", bd=0, font=("Segoe UI", 10, "bold"),
            cursor="hand2", padx=12, pady=7
        )
        self.add_button.pack(side="left")

        self.remove_button = tk.Button(
            button_row, text="ลบรูปที่เลือก", command=self.remove_selected,
            bg=WHITE, fg=MUTED, activebackground=PALE,
            relief="flat", bd=0, font=("Segoe UI", 9),
            cursor="hand2", padx=12, pady=7
        )
        self.remove_button.pack(side="left", padx=7)

        self.clear_button = tk.Button(
            button_row, text="ล้างรูปทั้งหมด", command=self.clear_images,
            bg=WHITE, fg=MUTED, activebackground=PALE,
            relief="flat", bd=0, font=("Segoe UI", 9),
            cursor="hand2", padx=12, pady=7
        )
        self.clear_button.pack(side="right")

        list_frame = tk.Frame(right_panel, bg=WHITE)
        list_frame.pack(fill="both", expand=True, pady=(0, 4))

        self.image_list = tk.Listbox(
            list_frame, selectmode=tk.EXTENDED,
            font=("Segoe UI", 9), bg=WHITE, fg=TEXT,
            selectbackground=PINK, selectforeground=TEXT,
            relief="flat", bd=0, height=9,
            activestyle="none"
        )
        list_scroll = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.image_list.yview
        )
        self.image_list.configure(yscrollcommand=list_scroll.set)
        self.image_list.pack(side="left", fill="both", expand=True,
                            padx=(10, 0), pady=8)
        list_scroll.pack(side="right", fill="y", padx=(0, 8), pady=8)

        self.count = tk.Label(
            right_panel, text="ยังไม่มีรูปภาพ", bg=PALE, fg=MUTED,
            font=("Segoe UI", 9)
        )
        self.count.pack(anchor="e", pady=(0, 2))

        for path in self.config.get("image_paths", []):
            if os.path.isfile(path) and path.lower().endswith(IMAGE_TYPES):
                self.image_paths.append(path)
        self.sort_images()
        self.refresh_image_list()

    # -------------------- Keyboard shortcuts --------------------

    def setup_keyboard_shortcuts(self):
        # Catch keyboard shortcuts at the toplevel so Tk class bindings
        # cannot swallow Ctrl+V on Windows.
        self.root.bind_all("<KeyPress>", self._global_shortcuts, add="+")

    def bind_shortcuts(self, widget):
        # Retain compatibility for all editable fields; global handler
        # handles Ctrl combinations and Shift+Insert.
        return None

    def _global_shortcuts(self, event):
        widget = event.widget
        if not isinstance(widget, (tk.Entry, tk.Text)):
            return None
        try:
            if str(widget.cget("state")) == "disabled":
                return None
        except tk.TclError:
            return None

        key = event.keysym.lower()
        ctrl_down = bool(event.state & 0x4)
        if os.name == "nt":
            try:
                ctrl_down = ctrl_down or bool(ctypes.windll.user32.GetKeyState(0x11) & 0x8000)
            except Exception:
                pass

        if ctrl_down and key in ("v", "c", "x", "a"):
            if key == "v":
                return self._paste_text(widget)
            if key == "c":
                return self._copy_text(widget)
            if key == "x":
                self._copy_text(widget)
                self._delete_selection(widget)
                return "break"
            return self._select_all_for_widget(widget)

        if key == "insert" and (event.state & 0x1):
            return self._paste_text(widget)
        return None

    @staticmethod
    def _paste_text(widget):
        try:
            value = widget.clipboard_get()
            if isinstance(widget, tk.Text):
                try:
                    widget.delete("sel.first", "sel.last")
                except tk.TclError:
                    pass
                widget.insert("insert", value)
                widget.see("insert")
            else:
                try:
                    widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                except tk.TclError:
                    pass
                widget.insert(tk.INSERT, value)
        except (tk.TclError, OSError):
            pass
        return "break"

    @staticmethod
    def _copy_text(widget):
        try:
            selected = (widget.get("sel.first", "sel.last")
                        if isinstance(widget, tk.Text)
                        else widget.selection_get())
            widget.clipboard_clear()
            widget.clipboard_append(selected)
            widget.update_idletasks()
        except tk.TclError:
            pass
        return "break"

    @staticmethod
    def _delete_selection(widget):
        try:
            if isinstance(widget, tk.Text):
                widget.delete("sel.first", "sel.last")
            else:
                widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass

    @staticmethod
    def _select_all_for_widget(widget):
        if isinstance(widget, tk.Text):
            widget.tag_add("sel", "1.0", "end-1c")
            widget.mark_set("insert", "1.0")
            widget.see("insert")
        else:
            widget.select_range(0, "end")
            widget.icursor("end")
        return "break"

    @staticmethod
    def _select_all(event):
        return LaftelPost._select_all_for_widget(event.widget)

    # -------------------- Config --------------------

    def load_config(self):
        if os.path.isfile(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    if isinstance(data, dict):
                        return data
            except (OSError, json.JSONDecodeError):
                pass
        return {
            "bot_token": "", "channel_id": "",
            "caption_template": "♡﹒**hair 60**\n♡﹒price : 59.-",
            "image_paths": []
        }

    def save_config(self, token, channel):
        data = {
            "bot_token": token,
            "channel_id": channel,
            "caption_template": self.caption_template.get("1.0", "end-1c"),
            "image_paths": self.image_paths,
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        except OSError as exc:
            messagebox.showwarning(
                "Laftel Post",
                f"บันทึกการตั้งค่าไม่สำเร็จ แต่ยังสามารถส่งโพสต์ต่อได้\n{exc}"
            )

    # -------------------- Image selection --------------------

    def add_images(self, paths):
        added = 0
        for path in paths:
            path = os.path.abspath(path)
            if (os.path.isfile(path)
                    and path.lower().endswith(IMAGE_TYPES)
                    and path not in self.image_paths):
                self.image_paths.append(path)
                added += 1
        self.sort_images()
        self.refresh_image_list()
        if added:
            self.status.config(text=f"เพิ่มรูป {added} รูปแล้ว เรียงตามชื่อไฟล์ ♡")

    def sort_images(self):
        self.image_paths.sort(key=natural_sort_key)

    def choose_images(self):
        paths = filedialog.askopenfilenames(
            title="เลือกรูปภาพ (เลือกได้หลายรูป)",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.webp")]
        )
        if paths:
            self.add_images(paths)

    def on_drop(self, event):
        try:
            paths = self.root.tk.splitlist(event.data)
            self.add_images(paths)
        except Exception as exc:
            messagebox.showerror("Laftel Post", f"อ่านไฟล์ที่ลากมาวางไม่ได้\n{exc}")
        return "break"

    def remove_selected(self):
        if self.busy:
            return
        selected = list(self.image_list.curselection())
        for index in reversed(selected):
            del self.image_paths[index]
        self.refresh_image_list()

    def clear_images(self):
        if self.busy:
            return
        if not self.image_paths:
            return
        if messagebox.askyesno("Laftel Post", "ต้องการล้างรูปภาพทั้งหมดหรือไม่?"):
            self.image_paths.clear()
            self.refresh_image_list()

    def refresh_image_list(self):
        self.image_list.delete(0, tk.END)
        for index, path in enumerate(self.image_paths, 1):
            self.image_list.insert(
                tk.END, f"{index:03d}.  {os.path.basename(path)}"
            )
        self.count.config(text=f"{len(self.image_paths)} รูปภาพ • เรียงตามชื่อไฟล์")

    # -------------------- Discord posting --------------------

    def set_status(self, text):
        self.root.after(0, lambda value=text: self.status.config(text=value))

    def set_busy(self, value):
        self.busy = value
        state = "disabled" if value else "normal"
        for button in (self.post, self.add_button,
                       self.remove_button, self.clear_button):
            button.config(state=state)

    def start(self):
        if self.busy:
            return

        token = self.token.get().strip()
        # Discord.py expects the raw bot token, not the "Bot " authorization prefix.
        if token.lower().startswith("bot "):
            token = token[4:].strip()
        channel_id = self.channel.get().strip()
        template = self.caption_template.get("1.0", "end-1c")
        lines = template.splitlines()
        first_line = lines[0] if lines else ""
        number_match = re.search(r"\d+", first_line)

        if not token:
            messagebox.showwarning("Laftel Post", "กรุณาใส่ Bot Token")
            return
        if not channel_id.isdigit():
            messagebox.showwarning("Laftel Post", "กรุณาใส่ Channel ID เป็นตัวเลข")
            return
        if not number_match:
            messagebox.showwarning(
                "Laftel Post",
                "กรุณาใส่เลขเริ่มต้นไว้ในบรรทัดแรก เช่น ♡﹒**hair 60**"
            )
            return
        if not self.image_paths:
            messagebox.showwarning("Laftel Post", "กรุณาเพิ่มรูปภาพก่อน")
            return

        missing = [p for p in self.image_paths if not os.path.isfile(p)]
        if missing:
            messagebox.showwarning(
                "Laftel Post", "ไม่พบไฟล์รูปบางรายการ:\n" + "\n".join(missing[:5])
            )
            return

        self.sort_images()
        jobs = []
        start_number = int(number_match.group(0))
        number_width = len(number_match.group(0))
        for index, path in enumerate(self.image_paths):
            number_text = str(start_number + index).zfill(number_width)
            updated_first_line = (
                first_line[:number_match.start()]
                + number_text
                + first_line[number_match.end():]
            )
            caption_lines = [updated_first_line] + lines[1:]
            caption = "\n".join(caption_lines)
            jobs.append({"path": path, "caption": caption})

        self.save_config(token, channel_id)
        self.set_busy(True)
        self.set_status(f"กำลังเตรียมส่ง {len(jobs)} รูป ...")

        threading.Thread(
            target=self.worker,
            args=(token, int(channel_id), jobs),
            daemon=True
        ).start()

    def worker(self, token, channel_id, jobs):
        error_message = None
        sent = 0
        try:
            sent = asyncio.run(self.send_posts(token, channel_id, jobs))
        except PostSendError as exc:
            sent = exc.sent
            cause = exc.original or exc
            if isinstance(cause, discord.LoginFailure):
                error_message = (
                    "Bot Token ไม่ถูกต้อง (Discord ปฏิเสธการเข้าสู่ระบบ)\n"
                    "ให้นำ Bot Token ใหม่จาก Discord Developer Portal มาใส่ "
                    "และตรวจว่าไม่ได้คัดลอกคำว่า Bot นำหน้ามาด้วย"
                )
            elif isinstance(cause, discord.Forbidden):
                error_message = (
                    "บอทเข้าไม่ถึงห้องนี้หรือไม่มีสิทธิ์ส่งไฟล์แนบ (HTTP 403)\n"
                    "เปิด Server Settings > Integrations/Bots แล้วตรวจว่าบอทอยู่ในเซิร์ฟเวอร์\n"
                    "จากนั้นตั้งสิทธิ์ของห้องให้บอทมี View Channel, Send Messages "
                    "และ Attach Files"
                )
            elif isinstance(cause, discord.NotFound):
                error_message = (
                    "ไม่พบ Channel ID นี้ (HTTP 404)\n"
                    "เปิดโหมด Developer ใน Discord แล้วคลิกขวาที่ห้อง > Copy Channel ID "
                    "และตรวจว่าบอทอยู่ในเซิร์ฟเวอร์นั้น"
                )
            elif isinstance(cause, discord.HTTPException):
                status = cause.status
                if status == 413:
                    hint = "ไฟล์รูปใหญ่เกินขนาดที่ Discord อนุญาต กรุณาลดขนาดรูป"
                elif status == 429:
                    hint = "Discord จำกัดความถี่การส่งชั่วคราว กรุณารอสักครู่แล้วลองใหม่"
                elif status == 401:
                    hint = "Token ไม่ถูกต้องหรือหมดอายุ กรุณาตรวจสอบ Bot Token"
                elif status == 403:
                    hint = "บอทไม่มีสิทธิ์ View Channel, Send Messages หรือ Attach Files"
                elif status == 404:
                    hint = "ไม่พบห้องนี้ หรือบอทไม่มีสิทธิ์เข้าถึง"
                else:
                    hint = "ตรวจสอบการเชื่อมต่ออินเทอร์เน็ตและสิทธิ์ของบอท"
                error_message = (
                    f"Discord ตอบกลับ HTTP {status}: {cause}\n{hint}"
                )
            else:
                error_message = (
                    f"{type(cause).__name__}: {cause}\n"
                    "ตรวจสอบอินเทอร์เน็ต, Token และ Channel ID"
                )
        except Exception as exc:
            error_message = f"{type(exc).__name__}: {exc}"
        finally:
            self.root.after(0, self._finish_post, error_message, sent, len(jobs))

    def _finish_post(self, error_message, sent, total):
        self.set_busy(False)
        if error_message:
            self.status.config(text=f"ส่งสำเร็จแล้ว {sent}/{total} รูป")
            messagebox.showerror(
                "ส่ง Discord ไม่สำเร็จ",
                f"ส่งสำเร็จแล้ว {sent} จาก {total} รูป\n\n"
                f"รูปถัดไปอาจยังไม่ได้ส่ง กรุณาตรวจสอบ Discord ก่อนกดส่งซ้ำ\n\n"
                f"รายละเอียด: {error_message}"
            )
        else:
            self.status.config(text=f"โพสต์สำเร็จครบ {total} รูปแล้ว ♡")
            messagebox.showinfo(
                "Laftel Post",
                f"ส่งโพสต์แยกครบ {total} รูปเรียบร้อยแล้วค่ะ ♡"
            )

    async def send_posts(self, token, channel_id, jobs):
        client = discord.Client(intents=discord.Intents.none())
        sent = 0
        try:
            await client.login(token)
            channel = await client.fetch_channel(channel_id)
            if not hasattr(channel, "send"):
                raise RuntimeError("Channel นี้ไม่รองรับการส่งข้อความ")

            total = len(jobs)
            for index, item in enumerate(jobs, 1):
                filename = os.path.basename(item["path"])
                self.set_status(
                    f"กำลังส่ง {index}/{total}: {filename} ..."
                )
                # Open the image explicitly and keep the underlying handle alive
                # for the complete multipart upload. discord.File is closed in finally.
                image_handle = open(item["path"], "rb")
                upload = None
                try:
                    upload = discord.File(image_handle, filename=filename)
                    await channel.send(content=item["caption"], file=upload)
                except Exception as exc:
                    if isinstance(exc, discord.HTTPException):
                        detail = f"{type(exc).__name__} HTTP {exc.status}: {exc}"
                    else:
                        detail = f"{type(exc).__name__}: {exc}"
                    raise RuntimeError(f"ส่งไฟล์ {filename} ไม่สำเร็จ — {detail}") from exc
                finally:
                    if upload is not None:
                        upload.close()
                    if not image_handle.closed:
                        image_handle.close()
                sent += 1
                if index < total:
                    await asyncio.sleep(1.0)
            self.set_status(f"ส่งสำเร็จ {sent}/{total} รูปแล้ว ♡")
            return sent
        except Exception as exc:
            raise PostSendError(str(exc), sent, exc) from exc
        finally:
            await client.close()


if __name__ == "__main__":
    if DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    app = LaftelPost(root)
    root.mainloop()
