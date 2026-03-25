# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date

class DuAn(models.Model):
    _name = 'du_an'
    _description = 'Quản lý Dự án'
    _rec_name = 'ten_du_an'
    _order = 'ngay_bat_dau desc, id desc'

    active = fields.Boolean(string="Hoạt động", default=True)

    ma_du_an = fields.Char(
        string="Mã dự án",
        readonly=True,
        copy=False,
        default=lambda self: 'Mới'
    )
    ten_du_an = fields.Char(string="Tên dự án", required=True)
    muc_tieu = fields.Text(string="Mục tiêu dự án")

    ngay_bat_dau = fields.Date(string="Ngày bắt đầu", required=True)
    ngay_ket_thuc = fields.Date(string="Ngày kết thúc (Dự kiến)", required=True)

    trang_thai = fields.Selection([
        ('nhap', 'Nháp'),
        ('dang_thuc_hien', 'Đang thực hiện'),
        ('hoan_thanh', 'Hoàn thành'),
        ('tam_dung', 'Tạm dừng')
    ], string="Trạng thái", default='nhap')

    mau_kanban = fields.Integer(string="Màu Kanban", default=0)

    nguoi_quan_ly_id = fields.Many2one('nhan_vien', string="Người quản lý dự án", ondelete="set null")

    # ✅ FIX: Khai báo rõ relation table khớp với nhan_vien_inherit.py
    thanh_vien_ids = fields.Many2many(
        'nhan_vien',
        'du_an_nhan_vien_rel',   # Tên bảng quan hệ
        'du_an_id',
        'nhan_vien_id',
        string="Thành viên dự án"
    )

    cong_viec_ids = fields.One2many('cong_viec', 'du_an_id', string="Các công việc")

    tien_do = fields.Float(string="Tiến độ (%)", compute="_compute_tien_do", store=True)
    tong_cong_viec = fields.Integer(string="Tổng công việc", compute="_compute_tien_do", store=True)
    cong_viec_hoan_thanh = fields.Integer(string="Đã hoàn thành", compute="_compute_tien_do", store=True)
    cong_viec_tre_han = fields.Integer(string="Trễ hạn", compute="_compute_tien_do", store=True)

    @api.depends('cong_viec_ids', 'cong_viec_ids.trang_thai', 'cong_viec_ids.is_qua_han')
    def _compute_tien_do(self):
        for rec in self:
            total = len(rec.cong_viec_ids)
            completed = len(rec.cong_viec_ids.filtered(lambda t: t.trang_thai == 'hoan_thanh'))
            tre_han = len(rec.cong_viec_ids.filtered(lambda t: t.is_qua_han))
            rec.tong_cong_viec = total
            rec.cong_viec_hoan_thanh = completed
            rec.cong_viec_tre_han = tre_han
            rec.tien_do = (completed / total * 100) if total > 0 else 0.0

    @api.constrains('ngay_bat_dau', 'ngay_ket_thuc')
    def _check_ngay(self):
        for rec in self:
            if rec.ngay_bat_dau and rec.ngay_ket_thuc:
                if rec.ngay_ket_thuc < rec.ngay_bat_dau:
                    raise ValidationError("Ngày kết thúc không thể trước ngày bắt đầu!")

    @api.model
    def create(self, vals):
        if vals.get('ma_du_an', 'Mới') == 'Mới':
            vals['ma_du_an'] = self.env['ir.sequence'].next_by_code('du_an.sequence') or 'DA001'
        record = super(DuAn, self).create(vals)
        
        from datetime import date
        today = date.today()

        # Tự động ghi lịch sử cho Người quản lý
        if record.nguoi_quan_ly_id:
            self.env['lich_su_lam_viec'].create({
                'nhan_vien_id': record.nguoi_quan_ly_id.id,
                'loai_lich_su': 'du_an',
                'du_an_id': record.id,
                'ten_cong_viec': f'Quản lý dự án: {record.ten_du_an}',
                'ngay_bat_dau': today,
            })

        # Nếu có thành viên khi tạo mới, thu nạp vào lịch sử
        if record.thanh_vien_ids:
            for emp in record.thanh_vien_ids:
                self.env['lich_su_lam_viec'].create({
                    'nhan_vien_id': emp.id,
                    'loai_lich_su': 'du_an',
                    'du_an_id': record.id,
                    'ten_cong_viec': f'Thành viên dự án: {record.ten_du_an}',
                    'ngay_bat_dau': today,
                })
        return record

    def write(self, vals):
        # Lưu ds thành viên và quản lý trước khi cập nhật
        old_data = {rec.id: {'members': set(rec.thanh_vien_ids.ids), 'manager': rec.nguoi_quan_ly_id.id} for rec in self}
        res = super(DuAn, self).write(vals)
        
        from datetime import date
        today = date.today()
        for rec in self:
            # 1. Xử lý thay đổi Người quản lý
            if 'nguoi_quan_ly_id' in vals:
                old_manager_id = old_data[rec.id]['manager']
                if old_manager_id != rec.nguoi_quan_ly_id.id:
                    # Kết thúc lịch sử cũ của người quản lý cũ
                    if old_manager_id:
                        old_h = self.env['lich_su_lam_viec'].search([
                            ('nhan_vien_id', '=', old_manager_id),
                            ('du_an_id', '=', rec.id),
                            ('loai_lich_su', '=', 'du_an'),
                            ('ngay_ket_thuc', '=', False)
                        ], limit=1)
                        if old_h:
                            old_h.write({'ngay_ket_thuc': today, 'ghi_chu': 'Thôi giữ chức vụ quản lý dự án'})
                    
                    # Tạo lịch sử mới cho người quản lý mới
                    if rec.nguoi_quan_ly_id:
                        self.env['lich_su_lam_viec'].create({
                            'nhan_vien_id': rec.nguoi_quan_ly_id.id,
                            'loai_lich_su': 'du_an',
                            'du_an_id': rec.id,
                            'ten_cong_viec': f'Quản lý dự án: {rec.ten_du_an}',
                            'ngay_bat_dau': today,
                        })

            # 2. Xử lý thay đổi Thành viên
            if 'thanh_vien_ids' in vals:
                new_members = set(rec.thanh_vien_ids.ids)
                olds = old_data[rec.id]['members']
                
                added = new_members - olds
                removed = olds - new_members
                
                for emp_id in added:
                    self.env['lich_su_lam_viec'].create({
                        'nhan_vien_id': emp_id,
                        'loai_lich_su': 'du_an',
                        'du_an_id': rec.id,
                        'ten_cong_viec': f'Thành viên dự án {rec.ten_du_an}',
                        'ngay_bat_dau': date.today(),
                    })
                for emp_id in removed:
                    history = self.env['lich_su_lam_viec'].search([
                        ('nhan_vien_id', '=', emp_id),
                        ('loai_lich_su', '=', 'du_an'),
                        ('du_an_id', '=', rec.id),
                        ('ngay_ket_thuc', '=', False)
                    ], limit=1)
                    if history:
                        history.write({
                            'ngay_ket_thuc': date.today(),
                            'ghi_chu': 'Rời dự án'
                        })

            if 'trang_thai' in vals and vals['trang_thai'] in ['hoan_thanh', 'tam_dung']:
                histories = self.env['lich_su_lam_viec'].search([
                    ('loai_lich_su', '=', 'du_an'),
                    ('du_an_id', '=', rec.id),
                    ('ngay_ket_thuc', '=', False)
                ])
                if histories:
                    stt_text = 'Hoàn thành dự án' if vals['trang_thai'] == 'hoan_thanh' else 'Dòng dự án bị tạm dừng'
                    histories.write({
                        'ngay_ket_thuc': date.today(),
                        'ghi_chu': stt_text
                    })
        return res

    def action_view_cong_viec(self):
        """Mở danh sách công việc của dự án này."""
        return {
            'name': f'Công việc - {self.ten_du_an}',
            'type': 'ir.actions.act_window',
            'res_model': 'cong_viec',
            'view_mode': 'tree,form',
            'domain': [('du_an_id', '=', self.id)],
            'context': {'default_du_an_id': self.id},
        }

    def action_view_cong_viec_tre_han(self):
        """Mở danh sách công việc trễ hạn."""
        return {
            'name': f'Công việc trễ hạn - {self.ten_du_an}',
            'type': 'ir.actions.act_window',
            'res_model': 'cong_viec',
            'view_mode': 'tree,form',
            'domain': [('du_an_id', '=', self.id), ('is_qua_han', '=', True)],
            'context': {'default_du_an_id': self.id},
        }

    def action_dang_thuc_hien(self):
        self.write({'trang_thai': 'dang_thuc_hien'})

    def action_tam_dung(self):
        self.write({'trang_thai': 'tam_dung'})

    def action_hoan_thanh(self):
        for rec in self:
            # ✅ Kiểm tra: có công việc chưa xong không?
            cong_viec_chua_xong = rec.cong_viec_ids.filtered(
                lambda t: t.trang_thai not in ['hoan_thanh', 'huy_bo'])
            if cong_viec_chua_xong:
                raise ValidationError(
                    f"Dự án còn {len(cong_viec_chua_xong)} công việc chưa hoàn thành!\n"
                    "Vui lòng hoàn tất hoặc hủy bỏ tất cả công việc trước khi đóng dự án."
                )
        self.write({'trang_thai': 'hoan_thanh'})

    def action_nhap(self):
        self.write({'trang_thai': 'nhap'})
