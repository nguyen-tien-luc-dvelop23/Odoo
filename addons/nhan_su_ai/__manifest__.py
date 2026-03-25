# -*- coding: utf-8 -*-
{
    'name': "Nhân sự AI & Kết nối",
    'summary': """Tích hợp Gemini AI và API External cho hệ thống Nhân sự""",
    'description': """
        Tính năng:
        - Tóm tắt hồ sơ nhân viên bằng Gemini AI.
        - Trợ lý ảo giải đáp nội quy.
        - (Sắp tới) Thông báo qua Telegram.
    """,
    'author': "My Company",
    'category': 'Human Resources',
    'version': '1.0',
    'depends': ['nhan_su', 'base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/nhan_vien_ai_views.xml',
        'views/ai_chat_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
