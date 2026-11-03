import asyncio, os, threading, tkinter as tk
from tkinter import filedialog, messagebox, ttk
import discord

PINK = '#F4B8D0'; PALE = '#FFF5F9'; WHITE = '#FFFFFF'; TEXT = '#75485D'; MUTED = '#A77B90'

class LaftelPost:
    def __init__(self, root):
        self.root=root; self.root.title('Laftel Post'); self.root.geometry('760x680'); self.root.minsize(680,600); self.root.configure(bg=PALE)
        self.files=[]; self.busy=False
        style=ttk.Style(); style.theme_use('clam'); style.configure('Pink.TCombobox', fieldbackground=WHITE, background=WHITE)
        header=tk.Frame(root,bg=PALE); header.pack(fill='x',padx=28,pady=(22,12))
        tk.Label(header,text='♡  Laftel Post',font=('Segoe UI',27,'bold'),bg=PALE,fg=TEXT).pack(anchor='w')
        tk.Label(header,text='FREE EDITION  •  ส่งรูปสินค้าไป Discord ทีละรูป',font=('Segoe UI',10),bg=PALE,fg=MUTED).pack(anchor='w',pady=(2,0))
        card=tk.Frame(root,bg=WHITE,highlightbackground='#F5D7E4',highlightthickness=1); card.pack(fill='x',padx=28,pady=8)
        tk.Label(card,text='ตั้งค่าบอท Discord',font=('Segoe UI',13,'bold'),bg=WHITE,fg=TEXT).pack(anchor='w',padx=18,pady=(14,8))
        tk.Label(card,text='Bot Token',bg=WHITE,fg=TEXT,font=('Segoe UI',10,'bold')).pack(anchor='w',padx=18)
        self.token=tk.Entry(card,show='•',font=('Segoe UI',11),relief='flat',bg=PALE,fg=TEXT); self.token.pack(fill='x',padx=18,pady=(5,12),ipady=8)
        tk.Label(card,text='Channel ID',bg=WHITE,fg=TEXT,font=('Segoe UI',10,'bold')).pack(anchor='w',padx=18)
        self.channel=tk.Entry(card,font=('Segoe UI',11),relief='flat',bg=PALE,fg=TEXT); self.channel.pack(fill='x',padx=18,pady=(5,16),ipady=8)
        area=tk.Frame(root,bg=PALE); area.pack(fill='both',expand=True,padx=28,pady=10)
        tk.Label(area,text='รูปสินค้าที่เลือก',font=('Segoe UI',13,'bold'),bg=PALE,fg=TEXT).pack(anchor='w')
        self.list=tk.Listbox(area,font=('Segoe UI',10),bg=WHITE,fg=TEXT,selectbackground=PINK,relief='flat',height=11,activestyle='none'); self.list.pack(fill='both',expand=True,pady=8)
        row=tk.Frame(area,bg=PALE); row.pack(fill='x')
        self.btn(row,'＋ เพิ่มรูป',self.add).pack(side='left',padx=(0,7)); self.btn(row,'ลบรูปที่เลือก',self.remove,light=True).pack(side='left',padx=7); self.btn(row,'ล้างรายการ',self.clear,light=True).pack(side='left',padx=7)
        self.count=tk.Label(row,text='0 รูป',bg=PALE,fg=MUTED,font=('Segoe UI',10)); self.count.pack(side='right')
        self.post=tk.Button(root,text='♡  POST IMAGES TO DISCORD  ♡',command=self.start,bg=PINK,fg=WHITE,activebackground='#E99DBD',activeforeground=WHITE,font=('Segoe UI',12,'bold'),relief='flat',bd=0,cursor='hand2'); self.post.pack(fill='x',padx=28,pady=(10,8),ipady=12)
        self.status=tk.Label(root,text='พร้อมใช้งาน ✿',bg=PALE,fg=TEXT,font=('Segoe UI',10)); self.status.pack(pady=(0,18))
    def btn(self,parent,label,cmd,light=False):
        return tk.Button(parent,text=label,command=cmd,bg=WHITE if light else PINK,fg=TEXT if light else WHITE,activebackground='#FBE0EA',relief='flat',bd=0,font=('Segoe UI',10),cursor='hand2',padx=14,pady=8)
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
        if not token: messagebox.showwarning('Laftel Post','กรุณาใส่ Bot Token'); return
        if not cid.isdigit(): messagebox.showwarning('Laftel Post','กรุณาใส่ Channel ID เป็นตัวเลข'); return
        if not self.files: messagebox.showwarning('Laftel Post','กรุณาเลือกรูปก่อน'); return
        self.busy=True; self.post.config(state='disabled'); threading.Thread(target=self.worker,args=(token,int(cid),self.files.copy()),daemon=True).start()
    def worker(self,token,cid,paths):
        try: asyncio.run(self.send(token,cid,paths))
        except Exception as e: self.status_text('โพสต์ไม่สำเร็จ'); self.root.after(0,lambda:messagebox.showerror('เกิดข้อผิดพลาด',str(e)))
        finally: self.busy=False; self.root.after(0,lambda:self.post.config(state='normal'))
    async def send(self,token,cid,paths):
        intents=discord.Intents.none(); client=discord.Client(intents=intents)
        try:
            await client.login(token); channel=await client.fetch_channel(cid)
            if not hasattr(channel,'send'): raise RuntimeError('Channel นี้ไม่สามารถส่งข้อความได้')
            for i,path in enumerate(paths,1):
                self.status_text(f'กำลังโพสต์รูป {i}/{len(paths)} ...')
                with open(path,'rb') as f: await channel.send(file=discord.File(f,filename=os.path.basename(path)))
            self.status_text(f'โพสต์สำเร็จ {len(paths)} รูปแล้ว ♡')
        finally: await client.close()

if __name__=='__main__':
    root=tk.Tk(); app=LaftelPost(root); root.mainloop()
