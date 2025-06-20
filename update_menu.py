import sqlite3
import os

# الاتصال بقاعدة البيانات
db_path = os.path.join(os.path.dirname(__file__), 'src', 'database', 'app.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # حذف قسم تصميم المواقع القديم (id: 4)
    cursor.execute("UPDATE menu_sections SET is_active = 0 WHERE id = 4")
    print("تم حذف قسم تصميم المواقع القديم")
    
    # تحديث قسم المنتجات الرقمية (id: 5) إلى تصميم المواقع
    cursor.execute("""
        UPDATE menu_sections 
        SET label_ar = 'تصميم المواقع', 
            label_en = 'Web Design',
            name = 'web-design',
            icon = 'Monitor'
        WHERE id = 5
    """)
    print("تم تحديث قسم المنتجات الرقمية إلى تصميم المواقع")
    
    # حفظ التغييرات
    conn.commit()
    print("تم حفظ جميع التغييرات بنجاح!")
    
    # عرض النتائج
    cursor.execute("SELECT id, name, label_ar, label_en, is_active FROM menu_sections ORDER BY order_index")
    results = cursor.fetchall()
    
    print("\nالقوائم الحالية:")
    for row in results:
        status = "نشط" if row[4] else "محذوف"
        print(f"ID: {row[0]}, Name: {row[1]}, Arabic: {row[2]}, English: {row[3]}, Status: {status}")
        
except Exception as e:
    print(f"خطأ: {e}")
    conn.rollback()
finally:
    conn.close()

