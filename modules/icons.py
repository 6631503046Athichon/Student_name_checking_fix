"""
modules/icons.py
IconManager - จัดการ Font Awesome icons สำหรับ CustomTkinter
ใช้ tkfontawesome แปลงเป็น CTkImage พร้อม dark mode support
"""

import customtkinter as ctk
import tkfontawesome as tfa
from PIL import Image
import tempfile
import os


class IconManager:
    """Singleton จัดการ icons - cache ตาม (name, size, light_color, dark_color)"""

    _instance = None
    _cache = {}
    _tk_root = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def _ensure_tk(cls):
        """ตรวจสอบว่า Tk root มีอยู่แล้ว (จำเป็นสำหรับ tkfontawesome)"""
        pass  # CTk app สร้าง root ไว้แล้ว

    @classmethod
    def _photo_to_pil(cls, photo_image):
        """แปลง SvgImage/PhotoImage -> PIL.Image via temp PNG (รองรับ transparency)"""
        tmpfile = tempfile.mktemp(suffix='.png')
        try:
            photo_image.write(tmpfile, format='png')
            pil_image = Image.open(tmpfile).convert('RGBA')
            pil_image.load()  # Force load before closing file
        finally:
            try:
                os.unlink(tmpfile)
            except OSError:
                pass
        return pil_image

    @classmethod
    def get(cls, name, size=16, color="#374151", dark_color="#E5E7EB"):
        """
        คืน CTkImage สำหรับ icon ที่ระบุ

        Args:
            name: ชื่อ icon (Font Awesome 6 name เช่น 'users', 'plus')
            size: ความกว้าง pixel
            color: สี icon สำหรับ light mode
            dark_color: สี icon สำหรับ dark mode

        Returns:
            CTkImage หรือ None ถ้า icon ไม่มี
        """
        cache_key = (name, size, color, dark_color)
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        try:
            # สร้าง icon สำหรับ light mode
            light_photo = tfa.icon_to_image(name, fill=color, scale_to_width=size)
            light_pil = cls._photo_to_pil(light_photo)

            # สร้าง icon สำหรับ dark mode
            dark_photo = tfa.icon_to_image(name, fill=dark_color, scale_to_width=size)
            dark_pil = cls._photo_to_pil(dark_photo)

            # สร้าง CTkImage (รองรับ dark/light mode อัตโนมัติ)
            ctk_image = ctk.CTkImage(
                light_image=light_pil,
                dark_image=dark_pil,
                size=(size, size)
            )

            cls._cache[cache_key] = ctk_image
            return ctk_image

        except Exception:
            return None

    @classmethod
    def get_white(cls, name, size=16):
        """คืน CTkImage สีขาว (สำหรับปุ่ม PRIMARY/DANGER ที่พื้นสี)"""
        return cls.get(name, size, color="#FFFFFF", dark_color="#FFFFFF")

    @classmethod
    def get_sidebar(cls, name, size=18):
        """คืน CTkImage สำหรับ sidebar (สีอ่อนทั้ง light/dark)"""
        return cls.get(name, size, color="#D1D5DB", dark_color="#D1D5DB")

    @classmethod
    def clear_cache(cls):
        """ล้าง cache"""
        cls._cache.clear()
