# -*- coding: utf-8 -*-


from odoo import api, fields, models, tools, _
from odoo.tools import float_is_zero, float_compare, pycompat


class ACSAccountMoveManager(models.Model):
    _name = 'account.move.manager'

    invoice_line_ids = fields.One2many('account.invoice.line', 'manager_inv_id', string='Invoice Lines')
    move_lines = fields.One2many('stock.move', 'manager_move_id', string="Stock Moves")
    invoice_id = fields.Many2one('account.invoice', string="Facturas")
    picking_id = fields.Many2one('stock.picking', string="Movimientos")
    is_invoice = fields.Boolean(string='Es factura')
    is_move = fields.Boolean(string='Es movimiento')
    active = fields.Boolean(string='Es movimiento', default=True)
    origin = fields.Char(string='Ref. venta')
    qty_total = fields.Integer(string='Cantidad a procesar')

class ACSAccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    manager_inv_id = fields.Many2one('account.move.manager', string='Manager Invoice Reference',
        ondelete='cascade', index=True)


class ACSAccountInvoiceLine(models.Model):
    _inherit = "stock.move"

    manager_move_id = fields.Many2one('account.move.manager', string='Manager Move Reference',
        ondelete='cascade', index=True)

# class ACSaleOrder(models.Model):
#     _inherit = 'sale.order'
#
#     @api.multi
#     def action_confirm(self):
#         if self._get_forbidden_state_confirm() & set(self.mapped('state')):
#             raise UserError(_(
#                 'It is not allowed to confirm an order in the following states: %s'
#             ) % (', '.join(self._get_forbidden_state_confirm())))
#         self._action_confirm()
#         if self.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
#             self.action_done()
#
#         cont = 0
#         for qty_t in self.order_line:
#             cont += qty_t.product_uom_qty
#
#         self.env['account.move.manager'].search([]).create({
#                   'origin': self.name,
#                   'qty_to_process': cont,
#                   'qty_symbolic': cont,
#                   'qty_pending': cont,
#                  })
#         return True
