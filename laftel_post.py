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
    def __init__(self, message, sent):
        super().__init__(message)
        self.sent = sent


class LaftelPost:
    def __init__(self, root):
        self.root = root
        self.root.title("Laftel Post")
        self.root.geometry("760x820")
        self.root.minsize(680, 650)
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
        header.pack(fill="x", padx=28, pady=(18, 8))

        tk.Label(
            header, text="♡  Laftel Post",
            font=("Segoe UI", 27, "bold"), bg=PALE, fg=TEXT
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
        self.settings_card.pack(fill="x", padx=28, pady=6)

        tk.Label(
            self.settings_card, text="ตั้งค่าบอท Discord",
            font=("Segoe UI", 13, "bold"), bg=WHITE, fg=TEXT
        ).pack(anchor="w", padx=18, pady=(12, 6))

        tk.Label(
            self.settings_card, text="Bot Token", bg=WHITE, fg=TEXT,
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", padx=18)

        self.token = tk.Entry(
            self.settings_card, show="•", font=("Segoe UI", 11),
            relief="flat", bg=PALE, fg=TEXT
        )
        self.token.pack(fill="x", padx=18, pady=(4, 10), ipady=6)
        self.token.insert(0, self.config.get("bot_token", ""))

        tk.Label(
            self.settings_card, text="Channel ID", bg=WHITE, fg=TEXT,
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", padx=18)

        self.channel = tk.Entry(
            self.settings_card, font=("Segoe UI", 11),
            relief="flat", bg=PALE, fg=TEXT
        )
        self.channel.pack(fill="x", padx=18, pady=(4, 12), ipady=6)
        self.channel.insert(0, self.config.get("channel_id", ""))

        self.bind_shortcuts(self.token)
        self.bind_shortcuts(self.channel)

        area = tk.Frame(root, bg=PALE)
        area.pack(fill="both", expand=True, padx=28, pady=(8, 4))

        tk.Label(
            area, text="ตั้งชื่อข้อความและเพิ่มรูปภาพ",
            font=("Segoe UI", 13, "bold"), bg=PALE, fg=TEXT
        ).pack(anchor="w", pady=(0, 6))

        naming_card = tk.Frame(
            area, bg=WHITE, highlightbackground="#F5D7E4",
            highlightthickness=1
        )
        naming_card.pack(fill="x", pady=(0, 8))

        name_row = tk.Frame(naming_card, bg=WHITE)
        name_row.pack(fill="x", padx=14, pady=(10, 5))

        tk.Label(
            name_row, text="ชื่อหลัก", bg=WHITE, fg=TEXT,
            font=("Segoe UI", 10, "bold")
        ).pack(side="left")

        self.name_prefix = tk.Entry(
            name_row, font=("Segoe UI", 11), relief="flat",
            bg=PALE, fg=TEXT
        )
        self.name_prefix.pack(side="left", fill="x", expand=True,
                              padx=(12, 0), ipady=5)
        self.name_prefix.insert(0, self.config.get("name_prefix", "hair"))
        self.bind_shortcuts(self.name_prefix)

        number_row = tk.Frame(naming_card, bg=WHITE)
        number_row.pack(fill="x", padx=14, pady=(4, 5))

        tk.Label(
            number_row, text="เลขเริ่มต้น", bg=WHITE, fg=TEXT,
            font=("Segoe UI", 10, "bold")
        ).pack(side="left")

        self.start_number = tk.Entry(
            number_row, width=8, font=("Segoe UI", 11),
            relief="flat", bg=PALE, fg=TEXT
        )
        self.start_number.pack(side="left", padx=(12, 18), ipady=5)
        self.start_number.insert(0, str(self.config.get("start_number", 1)))
        self.bind_shortcuts(self.start_number)

        tk.Label(
            number_row, text="จำนวนหลัก", bg=WHITE, fg=TEXT,
            font=("Segoe UI", 10, "bold")
        ).pack(side="left")

        self.digit_width = tk.Entry(
            number_row, width=8, font=("Segoe UI", 11),
            relief="flat", bg=PALE, fg=TEXT
        )
        self.digit_width.pack(side="left", padx=(12, 0), ipady=5)
        self.digit_width.insert(0, str(self.config.get("digit_width", 2)))
        self.bind_shortcuts(self.digit_width)

        tk.Label(
            naming_card,
            text="ตัวอย่างข้อความ: hair 01, hair 02, hair 03 ...",
            bg=WHITE, fg=MUTED, font=("Segoe UI", 9)
        ).pack(anchor="w", padx=14, pady=(0, 10))

        drop_card = tk.Frame(
            area, bg=WHITE, highlightbackground="#F5D7E4",
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

        button_row = tk.Frame(area, bg=PALE)
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

        list_frame = tk.Frame(area, bg=WHITE)
        list_frame.pack(fill="both", expand=True, pady=(0, 4))

        self.image_list = tk.Listbox(
            list_frame, selectmode=tk.EXTENDED,
            font=("Segoe UI", 10), bg=WHITE, fg=TEXT,
            selectbackground=PINK, selectforeground=TEXT,
            relief="flat", bd=0, height=7,
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
            area, text="ยังไม่มีรูปภาพ", bg=PALE, fg=MUTED,
            font=("Segoe UI", 9)
        )
        self.count.pack(anchor="e", pady=(0, 2))

        self.post = tk.Button(
            root, text="♡  POST TO DISCORD  ♡", command=self.start,
            bg=PINK, fg=WHITE, activebackground="#E99DBD",
            activeforeground=WHITE, font=("Segoe UI", 12, "bold"),
            relief="flat", bd=0, cursor="hand2"
        )
        self.post.pack(fill="x", padx=28, pady=(6, 6), ipady=10)

        self.status = tk.Label(
            root, text="พร้อมใช้งาน ✿", bg=PALE, fg=TEXT,
            font=("Segoe UI", 10)
        )
        self.status.pack(pady=(0, 12))

        for path in self.config.get("image_paths", []):
            if os.path.isfile(path) and path.lower().endswith(IMAGE_TYPES):
                self.image_paths.append(path)
        self.sort_images()
        self.refresh_image_list()

    # -------------------- Keyboard shortcuts --------------------

    def setup_keyboard_shortcuts(self):
        self.root.bind_class(SHORTCUT_TAG, "<Control-v>", self._paste_clipboard)
        self.root.bind_class(SHORTCUT_TAG, "<Control-V>", self._paste_clipboard)
        self.root.bind_class(SHORTCUT_TAG, "<Control-c>", self._copy_clipboard)
        self.root.bind_class(SHORTCUT_TAG, "<Control-C>", self._copy_clipboard)
        self.root.bind_class(SHORTCUT_TAG, "<Control-x>", self._cut_clipboard)
        self.root.bind_class(SHORTCUT_TAG, "<Control-X>", self._cut_clipboard)
        self.root.bind_class(SHORTCUT_TAG, "<Control-a>", self._select_all)
        self.root.bind_class(SHORTCUT_TAG, "<Control-A>", self._select_all)
        self.root.bind_class(SHORTCUT_TAG, "<KeyPress>", self._handle_shortcuts)

    def bind_shortcuts(self, widget):
        tags = list(widget.bindtags())
        if SHORTCUT_TAG not in tags:
            tags.insert(0, SHORTCUT_TAG)
            widget.bindtags(tuple(tags))

    def _handle_shortcuts(self, event):
        if not isinstance(event.widget, (tk.Entry, tk.Text)):
            return None
        if not (event.state & 0x4):
            return None
        key = event.keysym.lower()
        handlers = {
            "v": self._paste_clipboard,
            "c": self._copy_clipboard,
            "x": self._cut_clipboard,
            "a": self._select_all,
        }
        handler = handlers.get(key)
        return handler(event) if handler else None

    @staticmethod
    def _native_clipboard_text():
        """Read Unicode clipboard text through Windows API, then Tk fallback."""
        if os.name == "nt":
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
            kernel32.GlobalLock.restype = ctypes.c_void_p
            kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
            user32.GetClipboardData.argtypes = [ctypes.c_uint]
            user32.GetClipboardData.restype = ctypes.c_void_p
            if user32.OpenClipboard(None):
                try:
                    handle = user32.GetClipboardData(13)  # CF_UNICODETEXT
                    if handle:
                        pointer = kernel32.GlobalLock(handle)
                        if pointer:
                            try:
                                return ctypes.wstring_at(pointer)
                            finally:
                                kernel32.GlobalUnlock(handle)
                finally:
                    user32.CloseClipboard()
        return None

    @staticmethod
    def _paste_clipboard(event):
        widget = event.widget
        try:
            if str(widget.cget("state")) == "disabled":
                return "break"
            value = LaftelPost._native_clipboard_text()
            if value is None:
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
        except (tk.TclError, OSError, AttributeError):
            pass
        return "break"

    @staticmethod
    def _copy_clipboard(event):
        widget = event.widget
        try:
            selected = (widget.get("sel.first", "sel.last")
                        if isinstance(widget, tk.Text)
                        else widget.selection_get())
            widget.clipboard_clear()
            widget.clipboard_append(selected)
        except tk.TclError:
            pass
        return "break"

    @staticmethod
    def _cut_clipboard(event):
        widget = event.widget
        try:
            if str(widget.cget("state")) == "disabled":
                return "break"
            selected = (widget.get("sel.first", "sel.last")
                        if isinstance(widget, tk.Text)
                        else widget.selection_get())
            widget.clipboard_clear()
            widget.clipboard_append(selected)
            if isinstance(widget, tk.Text):
                widget.delete("sel.first", "sel.last")
            else:
                widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass
        return "break"

    @staticmethod
    def _select_all(event):
        widget = event.widget
        if isinstance(widget, tk.Text):
            widget.tag_add("sel", "1.0", "end-1c")
            widget.mark_set("insert", "1.0")
            widget.see("insert")
        else:
            widget.select_range(0, "end")
            widget.icursor("end")
        return "break"

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
            "bot_token": "", "channel_id": "", "name_prefix": "hair",
            "start_number": 1, "digit_width": 2, "image_paths": []
        }

    def save_config(self, token, channel):
        data = {
            "bot_token": token,
            "channel_id": channel,
            "name_prefix": self.name_prefix.get().strip(),
            "start_number": int(self.start_number.get()),
            "digit_width": int(self.digit_width.get()),
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
        channel_id = self.channel.get().strip()
        prefix = self.name_prefix.get().strip()

        if not token:
            messagebox.showwarning("Laftel Post", "กรุณาใส่ Bot Token")
            return
        if not channel_id.isdigit():
            messagebox.showwarning("Laftel Post", "กรุณาใส่ Channel ID เป็นตัวเลข")
            return
        if not prefix:
            messagebox.showwarning("Laftel Post", "กรุณาใส่ชื่อหลัก เช่น hair")
            return
        if not self.image_paths:
            messagebox.showwarning("Laftel Post", "กรุณาเพิ่มรูปภาพก่อน")
            return

        try:
            start_number = int(self.start_number.get())
            digit_width = int(self.digit_width.get())
            if start_number < 0 or digit_width < 1 or digit_width > 6:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Laftel Post", "เลขเริ่มต้นต้องเป็น 0 ขึ้นไป และจำนวนหลัก 1–6"
            )
            return

        missing = [p for p in self.image_paths if not os.path.isfile(p)]
        if missing:
            messagebox.showwarning(
                "Laftel Post", "ไม่พบไฟล์รูปบางรายการ:\n" + "\n".join(missing[:5])
            )
            return

        self.sort_images()
        jobs = []
        for index, path in enumerate(self.image_paths):
            number = start_number + index
            caption = f"{prefix} {number:0{digit_width}d}"
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
        failed_caption = ""
        failed_path = ""
        try:
            sent = asyncio.run(self.send_posts(token, channel_id, jobs))
        except PostSendError as exc:
            sent = exc.sent
            error_message = str(exc)
        except discord.LoginFailure:
            error_message = "Bot Token ไม่ถูกต้อง กรุณาตรวจสอบ Token ใน Discord Developer Portal"
        except discord.Forbidden:
            error_message = (
                "บอทไม่มีสิทธิ์ส่งข้อความหรือแนบไฟล์ในห้องนี้\n"
                "ตรวจสอบ View Channel, Send Messages และ Attach Files"
            )
        except discord.NotFound:
            error_message = "ไม่พบ Channel ID นี้ หรือบอทไม่มีสิทธิ์เข้าถึงห้อง"
        except discord.HTTPException as exc:
            error_message = f"Discord ตอบกลับข้อผิดพลาด HTTP ({exc.status}): {exc}"
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
                self.set_status(
                    f"กำลังส่ง {index}/{total}: {item['caption']} ..."
                )
                upload = discord.File(
                    item["path"], filename=os.path.basename(item["path"])
                )
                try:
                    await channel.send(content=item["caption"], file=upload)
                finally:
                    upload.close()
                sent += 1
            self.set_status(f"ส่งสำเร็จ {sent}/{total} รูปแล้ว ♡")
            return sent
        except Exception as exc:
            raise PostSendError(str(exc), sent) from exc
        finally:
            await client.close()


if __name__ == "__main__":
    if DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    app = LaftelPost(root)
    root.mainloop()
