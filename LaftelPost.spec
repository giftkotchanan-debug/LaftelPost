# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

discord_datas, discord_binaries, discord_hidden = collect_all("discord")
dnd_datas, dnd_binaries, dnd_hidden = collect_all("tkinterdnd2")

a = Analysis(
    ["laftel_post.py"],
    pathex=[],
    binaries=discord_binaries + dnd_binaries,
    datas=discord_datas + dnd_datas + [("assets/LaftelPost_Logo.png", "assets")],
    hiddenimports=discord_hidden + dnd_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="LaftelPost",
    icon="assets/LaftelPost.ico",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
