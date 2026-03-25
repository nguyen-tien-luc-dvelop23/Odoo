#!/usr/bin/env python3
"""Clean up orphan external IDs and recreate dashboard records"""
import psycopg2

conn = psycopg2.connect(dbname='odoo_db', user='odoo', password='odoo', host='localhost', port=5431)
conn.autocommit = True
cur = conn.cursor()

# 1. Find orphan external IDs for dashboard
cur.execute("SELECT id, name, model, res_id FROM ir_model_data WHERE module='nhan_su' AND name LIKE '%%dashboard%%'")
rows = cur.fetchall()
print('Dashboard external IDs:', rows)

# 2. Delete them
cur.execute("DELETE FROM ir_model_data WHERE module='nhan_su' AND name LIKE '%%dashboard%%'")
print('Deleted dashboard external IDs:', cur.rowcount)

# 3. Delete orphan menu external ID
cur.execute("SELECT id, name, model, res_id FROM ir_model_data WHERE module='nhan_su' AND name='menu_dashboard'")
rows2 = cur.fetchall()
print('Menu dashboard external IDs:', rows2)
cur.execute("DELETE FROM ir_model_data WHERE module='nhan_su' AND name='menu_dashboard'")
print('Deleted menu_dashboard external IDs:', cur.rowcount)

# 4. Delete any old client action records
cur.execute("SELECT id, name FROM ir_act_client WHERE tag='nhan_su_dashboard_action'")
old_actions = cur.fetchall()
print('Old client actions:', old_actions)
for row in old_actions:
    cur.execute('DELETE FROM ir_act_client WHERE id=%s', (row[0],))
    print('Deleted old client action id:', row[0])

# 5. Delete orphan menu items named Tổng quan under QLNS
cur.execute("SELECT m.id, m.name FROM ir_ui_menu m WHERE m.name IN ('Tổng quan', 'Tổng quan Nhân sự')")
old_menus = cur.fetchall()
print('Old menu items:', old_menus)
for row in old_menus:
    cur.execute('DELETE FROM ir_ui_menu WHERE id=%s', (row[0],))
    print('Deleted menu id:', row[0])

cur.close()
conn.close()
print('DONE - DB cleaned up!')
