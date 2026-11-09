import asyncio
import json
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import discord

PINK = "#F4B8D0"
PALE = "#FFF5F9"
WHITE = "#FFFFFF"
TEXT = "#75485D"
MUTED = "#A77B90"
CONFIG_FILE = "config.json"
IMAGE_TYPES = (".png", ".jpg", ".jpeg", ".gif", ".webp")

SHORTCUT_TAG = "LaftelPostShortcuts"


class PostGroup:
    """One Discord message: one description plus one image."""

    def __init__(self, app, number):
        self.app = app
        self.number = number
        self.image_path = None

        self.frame = tk.Frame(
            app.groups_inner,
            bg=WHITE,
            highlightbackground="#F5D7E4",
            highlightthickness=1
        )
        self.frame.pack(fill="x", pady=5)

        top = tk.Frame(self.frame, bg=WHITE)
        top.pack(fill="x", padx=12, pady=(10, 4))

        self.title = tk.Label(
            top,
            text=f"ชุดโพสต์ {number}",
            bg=WHITE,
            fg=TEXT,
            font=("Segoe UI", 11, "bold")
        )
        self.title.pack(side="left")

        self.remove_button = tk.Button(
            top,
            text="ลบชุดนี้",
            command=lambda: app.remove_group(self),
            bg=WHITE,
            fg=MUTED,
            activebackground=PALE,
            relief="flat",
            bd=0,
            cursor="hand2"
        )
        self.remove_button.pack(side="right")

        tk.Label(
            self.frame,
            text="ข้อความที่จะส่งพร้อมรูปนี้",
            bg=WHITE,
            fg=TEXT,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", padx=12, pady=(4, 3))

        self.description = tk.Text(
            self.frame,
            height=3,
            font=("Segoe UI", 10),
            relief="flat",
            bg=PALE,
            fg=TEXT,
            wrap="word",
            undo=True
        )
        self.description.pack(fill="x", padx=12, pady=(0, 8))

        image_row = tk.Frame(self.frame, bg=WHITE)
        image_row.pack(fill="x", padx=12, pady=(0, 10))

        self.image_label = tk.Label(
            image_row,
            text="ยังไม่ได้เลือกรูป",
            bg=WHITE,
            fg=MUTED,
            font=("Segoe UI", 9),
            anchor="w"
        )
        self.image_label.pack(side="left", fill="x", expand=True)

        tk.Button(
            image_row,
            text="เลือกรูป",
            command=self.choose_image,
            bg=PINK,
            fg=WHITE,
            activebackground="#E99DBD",
            relief="flat",
            bd=0,
            font=("Segoe UI", 9),
            cursor="hand2",
            padx=12,
            pady=5
        ).pack(side="right")

        app.bind_shortcuts(self.description)

    def choose_image(self):
        path = filedialog.askopenfilename(
            title=f"เลือกรูปสำหรับชุดโพสต์ {self.number}",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.webp")
            ]
        )

        if path:
            self.image_path = path
            self.image_label.config(
                text=os.path.basename(path),
                fg=TEXT
            )

    def get_data(self):
        return {
            "description": self.description.get("1.0", "end-1c").strip(),
            "image_path": self.image_path,
        }

    def destroy(self):
        self.frame.destroy()


class LaftelPost:
    def __init__(self, root):
        self.root = root
        self.root.title("Laftel Post")
        self.root.geometry("760x820")
        self.root.minsize(680, 650)
        self.root.configure(bg=PALE)

        self.busy = False
        self.groups = []
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
            header,
            text="♡  Laftel Post",
            font=("Segoe UI", 27, "bold"),
            bg=PALE,
            fg=TEXT
        ).pack(anchor="w")

        tk.Label(
            header,
            text="FREE EDITION  •  หนึ่งชุดข้อความต่อหนึ่งรูป",
            font=("Segoe UI", 10),
            bg=PALE,
            fg=MUTED
        ).pack(anchor="w", pady=(2, 0))

        self.settings_card = tk.Frame(
            root,
            bg=WHITE,
            highlightbackground="#F5D7E4",
            highlightthickness=1
        )
        self.settings_card.pack(fill="x", padx=28, pady=6)

        tk.Label(
            self.settings_card,
            text="ตั้งค่าบอท Discord",
            font=("Segoe UI", 13, "bold"),
            bg=WHITE,
            fg=TEXT
        ).pack(anchor="w", padx=18, pady=(12, 6))

        tk.Label(
            self.settings_card,
            text="Bot Token",
            bg=WHITE,
            fg=TEXT,
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", padx=18)

        self.token = tk.Entry(
            self.settings_card,
            show="•",
            font=("Segoe UI", 11),
            relief="flat",
            bg=PALE,
            fg=TEXT
        )
        self.token.pack(
            fill="x",
            padx=18,
            pady=(4, 10),
            ipady=6
        )
        self.token.insert(0, self.config.get("bot_token", ""))

        tk.Label(
            self.settings_card,
            text="Channel ID",
            bg=WHITE,
            fg=TEXT,
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", padx=18)

        self.channel = tk.Entry(
            self.settings_card,
            font=("Segoe UI", 11),
            relief="flat",
            bg=PALE,
            fg=TEXT
        )
        self.channel.pack(
            fill="x",
            padx=18,
            pady=(4, 12),
            ipady=6
        )
        self.channel.insert(0, self.config.get("channel_id", ""))

        self.bind_shortcuts(self.token)
        self.bind_shortcuts(self.channel)

        area = tk.Frame(root, bg=PALE)
        area.pack(fill="both", expand=True, padx=28, pady=(8, 4))

        title_row = tk.Frame(area, bg=PALE)
        title_row.pack(fill="x")

        tk.Label(
            title_row,
            text="ชุดข้อความและรูปภาพ",
            font=("Segoe UI", 13, "bold"),
            bg=PALE,
            fg=TEXT
        ).pack(side="left")

        self.add_button = tk.Button(
            title_row,
            text="＋ เพิ่มชุดโพสต์",
            command=self.add_group,
            bg=PINK,
            fg=WHITE,
            activebackground="#E99DBD",
            relief="flat",
            bd=0,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
            padx=12,
            pady=6
        )
        self.add_button.pack(side="right")

        list_shell = tk.Frame(area, bg=PALE)
        list_shell.pack(fill="both", expand=True, pady=6)

        self.canvas = tk.Canvas(
            list_shell,
            bg=PALE,
            highlightthickness=0,
            bd=0
        )

        scrollbar = ttk.Scrollbar(
            list_shell,
            orient="vertical",
            command=self.canvas.yview
        )

        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.groups_inner = tk.Frame(self.canvas, bg=PALE)

        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.groups_inner,
            anchor="nw"
        )

        self.groups_inner.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_groups_inner)

        self.count = tk.Label(
            area,
            text="0 ชุดโพสต์",
            bg=PALE,
            fg=MUTED,
            font=("Segoe UI", 9)
        )
        self.count.pack(anchor="e", pady=(0, 2))

        self.post = tk.Button(
            root,
            text="♡  POST TO DISCORD  ♡",
            command=self.start,
            bg=PINK,
            fg=WHITE,
            activebackground="#E99DBD",
            activeforeground=WHITE,
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            bd=0,
            cursor="hand2"
        )
        self.post.pack(fill="x", padx=28, pady=(6, 6), ipady=10)

        self.status = tk.Label(
            root,
            text="พร้อมใช้งาน ✿",
            bg=PALE,
            fg=TEXT,
            font=("Segoe UI", 10)
        )
        self.status.pack(pady=(0, 12))

        saved_groups = self.config.get("post_groups", [])

        if saved_groups:
            for item in saved_groups:
                group = self.add_group()
                group.description.insert("1.0", item.get("description", ""))

                path = item.get("image_path")
                if path and os.path.isfile(path):
                    group.image_path = path
                    group.image_label.config(
                        text=os.path.basename(path),
                        fg=TEXT
                    )
        else:
            self.add_group()

    # ---------------------------------------------------------
    # WINDOWS KEYBOARD SHORTCUTS
    # ---------------------------------------------------------

    def setup_keyboard_shortcuts(self):
        self.root.bind_class(
            SHORTCUT_TAG,
            "<KeyPress>",
            self._handle_shortcuts
        )

    def bind_shortcuts(self, widget):
        tags = list(widget.bindtags())
        if SHORTCUT_TAG not in tags:
            tags.insert(0, SHORTCUT_TAG)
            widget.bindtags(tuple(tags))

    def _handle_shortcuts(self, event):
        widget = event.widget
        if not isinstance(widget, (tk.Entry, tk.Text)):
            return None

        # Ctrl modifier on Windows Tk.
        if not (event.state & 0x4):
            return None

        key = event.keysym.lower()
        if key == "v":
            return self._paste_clipboard(event)
        if key == "c":
            return self._copy_clipboard(event)
        if key == "x":
            return self._cut_clipboard(event)
        if key == "a":
            return self._select_all(event)
        return None

    @staticmethod
    def _paste_clipboard(event):
        widget = event.widget
        try:
            if str(widget.cget("state")) == "disabled":
                return "break"

            clipboard_text = widget.clipboard_get()

            if isinstance(widget, tk.Text):
                try:
                    widget.delete("sel.first", "sel.last")
                except tk.TclError:
                    pass
                widget.insert("insert", clipboard_text)
            else:
                try:
                    widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                except tk.TclError:
                    pass
                widget.insert(tk.INSERT, clipboard_text)
        except tk.TclError:
            pass
        return "break"

    @staticmethod
    def _copy_clipboard(event):
        widget = event.widget
        try:
            if isinstance(widget, tk.Text):
                selected = widget.get("sel.first", "sel.last")
            else:
                selected = widget.selection_get()
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

            if isinstance(widget, tk.Text):
                selected = widget.get("sel.first", "sel.last")
                widget.clipboard_clear()
                widget.clipboard_append(selected)
                widget.delete("sel.first", "sel.last")
            else:
                selected = widget.selection_get()
                widget.clipboard_clear()
                widget.clipboard_append(selected)
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

    # ---------------------------------------------------------
    # CONFIG
    # ---------------------------------------------------------

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
            "bot_token": "",
            "channel_id": "",
            "post_groups": []
        }

    def save_config(self, token, channel, groups_data):
        data = {
            "bot_token": token,
            "channel_id": channel,
            "post_groups": groups_data,
        }

        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        except OSError as exc:
            messagebox.showwarning(
                "Laftel Post",
                f"บันทึกการตั้งค่าไม่สำเร็จ แต่ยังสามารถส่งโพสต์ต่อได้\n{exc}"
            )

    # ---------------------------------------------------------
    # POST GROUPS
    # ---------------------------------------------------------

    def add_group(self):
        group = PostGroup(self, len(self.groups) + 1)
        self.groups.append(group)
        self.renumber_groups()
        self.count.config(text=f"{len(self.groups)} ชุดโพสต์")
        return group

    def remove_group(self, group):
        if self.busy:
            return

        if len(self.groups) <= 1:
            messagebox.showinfo(
                "Laftel Post",
                "ต้องมีอย่างน้อย 1 ชุดโพสต์"
            )
            return

        self.groups.remove(group)
        group.destroy()
        self.renumber_groups()
        self.count.config(text=f"{len(self.groups)} ชุดโพสต์")

    def renumber_groups(self):
        for index, group in enumerate(self.groups, 1):
            group.number = index
            group.title.config(text=f"ชุดโพสต์ {index}")

    def _update_scroll_region(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_groups_inner(self, event):
        self.canvas.itemconfigure(self.canvas_window, width=event.width)

    # ---------------------------------------------------------
    # DISCORD POSTING
    # ---------------------------------------------------------

    def set_status(self, text):
        self.root.after(
            0,
            lambda value=text: self.status.config(text=value)
        )

    def start(self):
        if self.busy:
            return

        token = self.token.get().strip()
        channel_id = self.channel.get().strip()

        if not token:
            messagebox.showwarning("Laftel Post", "กรุณาใส่ Bot Token")
            return

        if not channel_id.isdigit():
            messagebox.showwarning(
                "Laftel Post",
                "กรุณาใส่ Channel ID เป็นตัวเลข"
            )
            return

        groups_data = [group.get_data() for group in self.groups]

        if not groups_data:
            messagebox.showwarning(
                "Laftel Post",
                "กรุณาเพิ่มชุดโพสต์ก่อน"
            )
            return

        for index, item in enumerate(groups_data, 1):
            path = item["image_path"]

            if not path:
                messagebox.showwarning(
                    "Laftel Post",
                    f"ชุดโพสต์ {index} ยังไม่ได้เลือกรูป"
                )
                return

            if not os.path.isfile(path):
                messagebox.showwarning(
                    "Laftel Post",
                    f"ไม่พบไฟล์รูปของชุดโพสต์ {index}\n{path}"
                )
                return

            if not path.lower().endswith(IMAGE_TYPES):
                messagebox.showwarning(
                    "Laftel Post",
                    f"ชนิดไฟล์รูปของชุดโพสต์ {index} ไม่รองรับ"
                )
                return

        self.save_config(token, channel_id, groups_data)

        self.busy = True
        self.post.config(state="disabled")
        self.add_button.config(state="disabled")

        for group in self.groups:
            group.remove_button.config(state="disabled")

        threading.Thread(
            target=self.worker,
            args=(token, int(channel_id), groups_data),
            daemon=True
        ).start()

    def worker(self, token, channel_id, groups_data):
        error_message = None
        try:
            asyncio.run(self.send_posts(token, channel_id, groups_data))
        except discord.LoginFailure:
            error_message = (
                "Bot Token ไม่ถูกต้อง "
                "กรุณาตรวจสอบ Token ใน Discord Developer Portal"
            )
        except discord.Forbidden:
            error_message = (
                "บอทไม่มีสิทธิ์ส่งข้อความหรือแนบไฟล์ในห้องนี้\n"
                "ตรวจสอบสิทธิ์ View Channel, Send Messages และ Attach Files"
            )
        except discord.NotFound:
            error_message = (
                "ไม่พบ Channel ID นี้ หรือบอทไม่มีสิทธิ์เข้าถึงห้องดังกล่าว"
            )
        except discord.HTTPException as exc:
            error_message = (
                f"Discord ตอบกลับข้อผิดพลาด HTTP ({exc.status}): {exc}"
            )
        except Exception as exc:
            error_message = f"{type(exc).__name__}: {exc}"
        finally:
            self.root.after(0, self._finish_post, error_message)

    def _finish_post(self, error_message):
        self.busy = False
        self.post.config(state="normal")
        self.add_button.config(state="normal")

        for group in self.groups:
            group.remove_button.config(state="normal")

        if error_message:
            self.status.config(text="โพสต์ไม่สำเร็จ")
            messagebox.showerror("ส่ง Discord ไม่สำเร็จ", error_message)
        else:
            self.status.config(text="โพสต์ทุกชุดสำเร็จแล้ว ♡")
            messagebox.showinfo(
                "Laftel Post",
                "ส่งโพสต์ทุกชุดไปยัง Discord สำเร็จแล้วค่ะ"
            )

    async def send_posts(self, token, channel_id, groups_data):
        intents = discord.Intents.none()
        client = discord.Client(intents=intents)

        try:
            await client.login(token)
            channel = await client.fetch_channel(channel_id)

            if not hasattr(channel, "send"):
                raise RuntimeError("Channel นี้ไม่รองรับการส่งข้อความ")

            total = len(groups_data)
            for index, item in enumerate(groups_data, 1):
                self.set_status(f"กำลังส่งชุดโพสต์ {index}/{total} ...")

                await channel.send(
                    content=item["description"] or None,
                    file=discord.File(
                        item["image_path"],
                        filename=os.path.basename(item["image_path"])
                    )
                )

            self.set_status(f"ส่งสำเร็จ {total} ชุดโพสต์แล้ว ♡")
        finally:
            await client.close()


if __name__ == "__main__":
    root = tk.Tk()
    app = LaftelPost(root)
    root.mainloop()
