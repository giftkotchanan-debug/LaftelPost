# Laftel Post 🌸

โปรแกรม Windows สำหรับส่งรูปไปยัง Discord ทีละรูป โดยไม่มีข้อความประกอบ

## สร้างไฟล์ติดตั้งฟรีผ่าน GitHub Actions
1. สมัคร/เข้าสู่ระบบ GitHub
2. สร้าง repository ใหม่ชื่อ `LaftelPost` และเลือก Public (เพื่อใช้ GitHub Actions ฟรีตามโควตาสาธารณะ)
3. แตกไฟล์ ZIP นี้ แล้วอัปโหลดไฟล์และโฟลเดอร์ทั้งหมดเข้า repository โดยคงโฟลเดอร์ `.github/workflows` ไว้
4. กดแท็บ **Actions** แล้วเลือก **Build Laftel Post Windows Installer**
5. กด **Run workflow** หาก workflow ยังไม่เริ่มเอง
6. เมื่อสำเร็จ เปิดรายการ run แล้วดาวน์โหลด Artifact ชื่อ `LaftelPost-Windows-Installer`
7. แตก Artifact จะได้ `LaftelPost_Setup.exe`

## ใช้งาน
- เปิด Laftel Post
- ใส่ Discord Bot Token และ Channel ID
- เพิ่มรูปหนึ่งรูปหรือหลายรูป
- กดปุ่ม POST โปรแกรมจะส่งรูปแยกเป็นข้อความละหนึ่งรูป

## ตั้งค่า Discord Bot
สร้างแอปที่ https://discord.com/developers/applications แล้วเพิ่ม Bot จากนั้นเชิญเข้าห้อง/เซิร์ฟเวอร์ที่ต้องการ โดยให้สิทธิ์ View Channel, Send Messages และ Attach Files

**ความปลอดภัย:** ห้ามส่ง Bot Token ให้ผู้อื่นหรืออัปโหลดลง GitHub ค่าที่กรอกในโปรแกรมใช้ในเครื่องขณะรันเท่านั้น

## หมายเหตุ
- ต้องเชื่อมต่ออินเทอร์เน็ตและเปิดโปรแกรมขณะโพสต์
- Bot ต้องอยู่ในเซิร์ฟเวอร์และมีสิทธิ์ในห้องเป้าหมาย
- ตัวติดตั้งนี้ยังไม่ได้ลงนามดิจิทัล Windows อาจแสดง SmartScreen warning สำหรับแอปที่ไม่รู้จัก
- ทดสอบกับ Windows 10/11 64-bit ก่อนใช้งานจริง
