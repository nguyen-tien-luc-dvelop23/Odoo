# -*- coding: utf-8 -*-
{
    'name': "Quản lý Nhân sự",
    'summary': """Module quản lý nhân sự, chức vụ, phòng ban, lịch sử làm việc và quản lý dự án (MBO)""",
    'description': """
        Module quản lý nhân sự bao gồm:
        - Quản lý thông tin nhân viên
        - Quản lý chức vụ
        - Quản lý phòng ban
        - Quản lý lịch sử làm việc
        - Quản lý Dự án & Công việc (MBO)
    """,
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Human Resources',
    'version': '1.1',
    'license': 'LGPL-3',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/chuc_vu.xml',
        'views/phong_ban.xml',
        'views/nhan_vien.xml',
        'views/lich_su_lam_viec.xml',
        'views/du_an_views.xml',
        'views/cong_viec_views.xml',
        'views/nhan_vien_inherit_views.xml',
        'views/nhan_vien_inherit_views.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'nhan_su/static/src/css/nhan_vien.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
