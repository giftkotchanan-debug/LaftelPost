import asyncio, os, threading, json, tkinter as tk
from tkinter import filedialog, messagebox, ttk
import discord

PINK = '#F4B8D0'; PALE = '#FFF5F9'; WHITE = '#FFFFFF'; TEXT = '#75485D'; MUTED = '#A77B90'
CONFIG_FILE = "config.json"

class LaftelPost:
    def __init__(self, root):
        self.root=root; self.root.title('Laftel Post'); self.root.geometry('760x780'); self.root.minsize(680,680); self.root.configure(bg=PALE)
        self.files=[]; self.busy=False
        
        # โหลดค่าตั้งค่าเดิมที่เคยบันทึกไว้
        self.config = self.load_config()

        style=ttk.Style(); style.theme_use('clam'); style.configure('Pink.TCombobox', fieldbackground=WHITE, background=WHITE)
        header=tk.Frame(root,bg=PALE); header.pack(fill='x',padx=28,pady=(18,8))
        tk.Label(header,text='♡  Laftel Post',font=('Segoe UI',27,'bold'),bg=PALE,fg=TEXT).pack(anchor='w')
        tk.Label(header,text='FREE EDITION  •  ส่งรูปสินค้าไป Discord ทีละรูป',font=('Segoe UI',10),bg=PALE,fg=MUTED).pack(anchor='w',pady=(2,0))
        
        card=tk.Frame(root,bg=WHITE,highlightbackground='#F5D7E4',highlightthickness=1); card.pack(fill='x',padx=28,pady=6)
        tk.Label(card,text='ตั้งค่าบอท Discord',font=('Segoe UI',13,'bold'),bg=WHITE,fg=TEXT).pack(anchor='w',padx=18,pady=(12,6))
        
        tk.Label(card,text='Bot Token',bg=WHITE,fg=TEXT,font=('Segoe UI',10,'bold')).pack(anchor='w',padx=18)
        self.token=tk.Entry(card,show='•',font=('Segoe UI',11),relief='flat',bg=PALE,fg=TEXT)
        self.token.pack(fill='x',padx=18,pady=(4,10),ipady=6)
        self.token.insert(0, self.config.get("bot_token", ""))

        tk.Label(card,text='Channel ID',bg=WHITE,fg=TEXT,font=('Segoe UI',10,'bold')).pack(anchor='w',padx=18)
        self.channel=tk.Entry(card,font=('Segoe UI',11),relief='flat',bg=PALE,fg=TEXT)
        self.channel.pack(fill='x',padx=18,pady=(4,12),ipady=6)
        self.channel.insert(0, self.config.get("channel_id", ""))

        # ช่องพิมพ์ข้อความอธิบาย (Description)
        tk.Label(card,text='ข้อความอธิบาย (Description)',bg=WHITE,fg=TEXT,font=('Segoe UI',10,'bold')).pack(anchor='w',padx=18)
        self.desc_text = tk.Text(card,height=3,font=('Segoe UI',10),relief='flat',bg=PALE,fg=TEXT,wrap='word')
        self.desc_text.pack(fill='x',padx=18,pady=(4,14))
        self.desc_text.insert('1.0', self.config.get("description", ""))

        # เปิดใช้งานคีย์ลัด Ctrl+C, Ctrl+V, Ctrl+A แบบแก้ไขให้วางได้ชัวร์
        for widget in [self.token, self.channel, self.desc_text]:
            self.bind_shortcuts(widget)

        area=tk.Frame(root,bg=PALE); area.pack(fill='both',expand=True,padx=28,pady=8)
        tk.Label(area,text='รูปสินค้าที่เลือก',font=('Segoe UI',13,'bold'),bg=PALE,fg=TEXT).pack(anchor='w')
        self.list=tk.Listbox(area,font=('Segoe UI',10),bg=WHITE,fg=TEXT,selectbackground=PINK,relief='flat',height=8,activestyle='none'); self.list.pack(fill='both',expand=True,pady=6)
        
        row=tk.Frame(area,bg=PALE); row.pack(fill='x')
        self.btn(row,'＋ เพิ่มรูป',self.add).pack(side='left',padx=(0,7)); self.btn(row,'ลบรูปที่เลือก',self.remove,light=True).pack(side='left',padx=7); self.btn(row,'ล้างรายการ',self.clear,light=True).pack(side='left',padx=7)
        self.count=tk.Label(row,text='0 รูป',bg=PALE,fg=MUTED,font=('Segoe UI',10)); self.count.pack(side='right')
        
        self.post=tk.Button(root,text='♡  POST IMAGES TO DISCORD  ♡',command=self.start,bg=PINK,fg=WHITE,activebackground='#E99DBD',activeforeground=WHITE,font=('Segoe UI',12,'bold'),relief='flat',bd=0,cursor='hand2'); self.post.pack(fill='x',padx=28,pady=(8,6),ipady=10)
        self.status=tk.Label(root,text='พร้อมใช้งาน ✿',bg=PALE,fg=TEXT,font=('Segoe UI',10)); self.status.pack(pady=(0,12))

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"bot_token": "", "channel_id": "", "description": ""}

    def save_config(self, token, channel, desc):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"bot_token": token, "channel_id": channel, "description": desc}, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def bind_shortcuts(self, widget):
        """ระบบจัดการคีย์ลัด ดึงข้อความวางและคัดลอกโดยตรง"""
        widget.bind("<Control-v>", lambda e: self.paste_text(e))
        widget.bind("<Control-c>", lambda e: self.copy_text(e))
        widget.bind("<Control-x>", lambda e: self.cut_text(e))
        widget.bind("<Control-a>", lambda e: self.select_all(e))

    def paste_text(self, event):
        try:
            text = self.root.clipboard_get()
            if isinstance(event.widget, tk.Text):
                event.widget.insert("insert", text)
            else:
                event.widget.insert(tk.INSERT, text)
        except Exception:
            pass
        return "break"

    def copy_text(self, event):
        try:
            if isinstance(event.widget, tk.Text):
                selected = event.widget.get("sel.first", "sel.last")
            else:
                selected = event.widget.selection_get()
            self.root.clipboard_clear()
            self.root.clipboard_append(selected)
        except Exception:
            pass
        return "break"

    def cut_text(self, event):
        try:
            self.copy_text(event)
            if isinstance(event.widget, tk.Text):
                event.widget.delete("sel.first", "sel.last")
            else:
                event.widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except Exception:
            pass
        return "break"

    def select_all(self, event):
        if isinstance(event.widget, tk.Text):
            event.widget.tag_add("sel", "1.0", "end")
        else:
            event.widget.select_range(0, "end")
            event.widget.icursor("end")
        return "break"

    def btn(self,parent,label,cmd,light=False):
        return tk.Button(parent,text=label,command=cmd,bg=WHITE if light else PINK,fg=TEXT if light else WHITE,activebackground='#FBE0EA',relief='flat',bd=0,font=('Segoe UI',10),cursor='hand2',padx=14,pady=6)
    def add(self):
        paths=filedialog.askopenfilenames(title='เลือกรูปสินค้า',filetypes=[('Image files','*.png *.jpg *.jpeg *.gif *.webp')])
        for p in paths:
            if p not in self.files: self.files.append(p); self.list.insert('end',os.path.basename(p))
        self.count.config(text=f'{len(self.files)} รูป')
    def remove(self):
        for i in reversed(self.list.curselection()): self.list.delete(i); self.files.pop(i)
        self.count.config(text=f'{len(self.files)} รูป')
    def clear(self): self.files.clear(); self.list.delete(0,'end'); self.count.config(text='0 รูป')
    def status_text(self,s): self.root.after(0,lambda:self.status.config(text=s))
    
    def start(self):
        if self.busy: return
        token=self.token.get().strip(); cid=self.channel.get().strip()
        description = self.desc_text.get('1.0', 'end-1c').strip()

        if not token: messagebox.showwarning('Laftel Post','กรุณาใส่ Bot Token'); return
        if not cid.isdigit(): messagebox.showwarning('Laftel Post','กรุณาใส่ Channel ID เป็นตัวเลข'); return
        if not self.files: messagebox.showwarning('Laftel Post','กรุณาเลือกรูปก่อน'); return
        
        self.save_config(token, cid, description)

        self.busy=True; self.post.config(state='disabled')
        threading.Thread(target=self.worker,args=(token,int(cid),description,self.files.copy()),daemon=True).start()

    def worker(self,token,cid,desc,paths):
        try: asyncio.run(self.send(token,cid,desc,paths))
        except Exception as e: self.status_text('โพสต์ไม่สำเร็จ'); self.root.after(0,lambda:messagebox.showerror('เกิดข้อผิดพลาด',str(e)))
        finally: self.busy=False; self.root.after(0,lambda:self.post.config(state='normal'))

    async def send(self,token,cid,desc,paths):
        intents=discord.Intents.none(); client=discord.Client(intents=intents)
        try:
            await client.login(token); channel=await client.fetch_channel(cid)
            if not hasattr(channel,'send'): raise RuntimeError('Channel นี้ไม่สามารถส่งข้อความได้')
            for i,path in enumerate(paths,1):
                self.status_text(f'กำลังโพสต์รูป {i}/{len(paths)} ...')
                with open(path,'rb') as f:
                    content_to_send = desc if i == 1 else ""
                    await channel.send(content=content_to_send, file=discord.File(f,filename=os.path.basename(path)))
            self.status_text(f'โพสต์สำเร็จ {len(paths)} รูปแล้ว ♡')
        finally: await client.close()

if __name__=='__main__':
    root=tk.Tk(); app=LaftelPost(root); root.mainloop()
