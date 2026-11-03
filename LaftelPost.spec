# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
datas, binaries, hiddenimports = collect_all('discord')
a = Analysis(['laftel_post.py'], pathex=[], binaries=binaries, datas=datas + [('assets/LaftelPost_Logo.png', 'assets')], hiddenimports=hiddenimports, hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='LaftelPost', icon='assets/LaftelPost.ico', debug=False, bootloader_ignore_signals=False, strip=False, upx=True, console=False)
