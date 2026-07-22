"""คู่มือการใช้งาน — in-app user guide dialog."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QTextBrowser,
    QVBoxLayout,
)

from . import theme
from .icon import render_pixmap

_GUIDE_HTML = f"""
<style>
  h2 {{ color: {theme.NEON_CYAN}; margin-bottom: 2px; }}
  h3 {{ color: {theme.NEON_PINK}; margin-top: 18px; margin-bottom: 4px; }}
  p, li {{ color: {theme.TEXT}; line-height: 150%; }}
  .brand {{ color: {theme.NEON_CYAN}; letter-spacing: 3px; font-weight: bold; font-size: 11px; }}
  .muted {{ color: {theme.TEXT_MUTED}; }}
  code {{ color: {theme.NEON_PURPLE}; }}
  .keep {{ color: #00E676; font-weight: bold; }}
  .del {{ color: #FF3B6B; font-weight: bold; }}
  .meta {{ color: #FFB300; font-weight: bold; }}
</style>

<div class="brand">DJ&nbsp;LAB&nbsp;SIAM</div>
<h2>คู่มือการใช้งาน · Duplicate Audio Finder</h2>
<p class="muted">ค้นหาและลบไฟล์เสียงที่ซ้ำกันอย่างปลอดภัย — ไฟล์ที่ลบจะถูกย้ายไป Trash / Recycle Bin เสมอ</p>

<h3>▸ ขั้นตอนใช้งาน</h3>
<ol>
  <li><b>เพิ่มโฟลเดอร์</b> — กด <code>Add folder…</code> เลือกโฟลเดอร์เพลง (เพิ่มได้หลายโฟลเดอร์)</li>
  <li><b>สแกน</b> — กด <code>Scan for duplicates</code> แถบ EQ นีออนจะเต้นระหว่างประมวลผล กด <code>Cancel</code> เพื่อหยุดได้ทุกเมื่อ</li>
  <li><b>ตรวจผล</b> — ผลลัพธ์แสดงเป็นกลุ่มไฟล์ซ้ำ กางดูไฟล์ในแต่ละกลุ่มได้</li>
  <li><b>เลือกไฟล์ที่จะลบ</b> — ติ๊ก/เอาติ๊กออกเองได้ตามต้องการ</li>
  <li><b>ลบ</b> — กด <code>Move selected to Trash</code> แล้วยืนยัน ไฟล์จะไปอยู่ถังขยะ (กู้คืนได้)</li>
</ol>

<h3>▸ ความหมายของสี</h3>
<ul>
  <li><span class="keep">เขียว (keep)</span> — ไฟล์ที่แอปแนะนำให้เก็บ (คุณภาพดีที่สุดในกลุ่ม) เริ่มต้นไม่ติ๊กลบ</li>
  <li><span class="del">ชมพู/แดง</span> — ไฟล์ที่ถูกติ๊กไว้ว่าจะลบ</li>
  <li><span class="meta">ส้ม</span> — กลุ่มที่ตรงกันจาก <b>metadata</b> (ชื่อเพลง/ศิลปิน/อัลบั้ม) ไม่ใช่ไฟล์เหมือนกันทุก byte — โปรดตรวจก่อนลบ</li>
</ul>

<h3>▸ แอปเลือกไฟล์ที่จะเก็บอย่างไร</h3>
<p>จัดอันดับตามลำดับ: <b>bitrate สูงสุด → tag ครบที่สุด → ไม่ใช่ไฟล์ที่ดูเป็น "copy" → path สั้นกว่า → ไฟล์เก่ากว่า</b>
คุณเปลี่ยนการเลือกเองได้เสมอด้วย checkbox</p>

<h3>▸ ความปลอดภัย</h3>
<ul>
  <li>ลบด้วยการ <b>ย้ายไป Trash/Recycle Bin</b> เท่านั้น — ไม่ลบถาวร</li>
  <li>แอป <b>ปฏิเสธ</b>การลบไฟล์ทั้งกลุ่ม (ต้องเหลืออย่างน้อย 1 ไฟล์เสมอ)</li>
  <li>ทุกการลบถูกบันทึกไว้ใน <code>delete_history.jsonl</code> ในโฟลเดอร์ข้อมูลของแอป</li>
</ul>

<h3>▸ ตั้งค่า (Settings)</h3>
<p>ปรับได้ว่าจะจับคู่ด้วย metadata หรือไม่ และกำหนดนามสกุลไฟล์เสียงที่จะสแกน</p>

<p class="muted" style="margin-top:22px;">พัฒนาโดย <b style="color:{theme.NEON_PINK};">Dev&nbsp;ZLEX</b> · DJ LAB SIAM</p>
"""


class HelpDialog(QDialog):
    """A scrollable Thai user guide styled to match the app theme."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("คู่มือการใช้งาน — Duplicate Audio Finder")
        self.setWindowIcon(render_pixmap(64))
        self.resize(560, 620)

        layout = QVBoxLayout(self)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(_GUIDE_HTML)
        layout.addWidget(browser)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        buttons.button(QDialogButtonBox.Close).clicked.connect(self.accept)
        layout.addWidget(buttons, alignment=Qt.AlignRight)
