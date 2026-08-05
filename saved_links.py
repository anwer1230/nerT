"""
saved_links.py — إدارة الروابط المحفوظة
"""
import json
import os
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

SAVED_LINKS_FILE = os.path.join(DATA_DIR, 'saved_links.json')


def load_saved_links():
    """تحميل الروابط المحفوظة"""
    try:
        if os.path.exists(SAVED_LINKS_FILE):
            with open(SAVED_LINKS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading saved links: {e}")
    return {"links": []}


def save_saved_links(data):
    """حفظ الروابط"""
    try:
        with open(SAVED_LINKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving saved links: {e}")
        return False


def add_saved_link(url, title=None, category='عام', notes='', source='يدوي'):
    """إضافة رابط جديد"""
    data = load_saved_links()
    for link in data["links"]:
        if link["url"] == url:
            return False, "الرابط موجود بالفعل"
    new_link = {
        "id": str(uuid.uuid4())[:8],
        "url": url,
        "title": title or url,
        "category": category,
        "date_saved": datetime.now().isoformat(),
        "source": source,
        "notes": notes
    }
    data["links"].append(new_link)
    save_saved_links(data)
    return True, new_link


def add_multiple_links(urls, category='عام', source='دفعة'):
    """إضافة عدة روابط"""
    data = load_saved_links()
    added = []
    skipped = []
    for url in urls:
        url = url.strip()
        if not url:
            continue
        if any(l["url"] == url for l in data["links"]):
            skipped.append(url)
            continue
        new_link = {
            "id": str(uuid.uuid4())[:8],
            "url": url,
            "title": url,
            "category": category,
            "date_saved": datetime.now().isoformat(),
            "source": source,
            "notes": ""
        }
        data["links"].append(new_link)
        added.append(url)
    save_saved_links(data)
    return added, skipped


def delete_saved_link(link_id):
    """حذف رابط"""
    data = load_saved_links()
    data["links"] = [l for l in data["links"] if l["id"] != link_id]
    save_saved_links(data)
    return True


def delete_multiple_links(link_ids):
    """حذف عدة روابط"""
    data = load_saved_links()
    data["links"] = [l for l in data["links"] if l["id"] not in link_ids]
    save_saved_links(data)
    return True


def update_saved_link(link_id, updates):
    """تحديث رابط"""
    data = load_saved_links()
    for link in data["links"]:
        if link["id"] == link_id:
            for k, v in updates.items():
                link[k] = v
            save_saved_links(data)
            return True, link
    return False, None


def get_saved_links_by_category(category=None):
    """جلب الروابط حسب التصنيف"""
    data = load_saved_links()
    if category:
        return [l for l in data["links"] if l.get("category") == category]
    return data["links"]


def get_categories():
    """قائمة التصنيفات"""
    data = load_saved_links()
    return sorted(set(l.get("category", "عام") for l in data["links"]))
