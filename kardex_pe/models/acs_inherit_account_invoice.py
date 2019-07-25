# -*- coding: utf-8 -*-


from odoo import api, fields, models, tools, _
from odoo.tools import float_is_zero, float_compare, pycompat
from openerp.exceptions import AccessDenied, AccessError, UserError, ValidationError


class ACStockMoveLine(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_invoice_open(self):
        # lots of duplicate calls to action_invoice_open, so we remove those already open
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        if to_open_invoices.filtered(lambda inv: inv.state != 'draft'):
            raise UserError(_("Invoice must be in draft state in order to validate it."))
        if to_open_invoices.filtered(lambda inv: float_compare(inv.amount_total, 0.0, precision_rounding=inv.currency_id.rounding) == -1):
            raise UserError(_("You cannot validate an invoice with a negative total amount. You should create a credit note instead."))
        to_open_invoices.action_date_assign()
        to_open_invoices.action_move_create()

        #DevFree: Desde aca intervenimos codigo
        # pricking_id = self.env['stock.picking'].search(['&',('origin','=',self.origin),('state','=','done')])
        manager = self.env['account.move.manager'].search(['&',('origin','=',self.origin),'&',('is_move','=',True),('active','=',True)])
        inv_restriction = self.env['account.move.manager'].search(['&',('origin','=',self.origin),'&',('is_invoice','=',True),('active','=',True)])
        if inv_restriction:
            capture_id = self.id - 1
            msj_id = self.env['account.invoice'].search([('id','=',capture_id)])
            raise UserError(_("Debes entregar los productos de la factura %s, antes de validar una nueva.")% (str(msj_id.number)))

        if manager:
            #DevFree: Procesamos los productos que estamos facturando en este momento self.invoice_line_ids
            # manager = self.env['account.move.manager'].search(['&',('origin','=',self.origin),'&',('is_move','=',True),('active','=',True)])
            this_ids = []
            this_create = []
            this_count = 0
            qty_total = 0
            for this_inv_lines in self.invoice_line_ids:
                for this_inv_products in this_inv_lines.product_id:
                    this_ids.append(this_inv_products.id)
                    this_create.append(this_inv_lines.id)
                    this_count += 1
                    qty_total += this_inv_lines.quantity
            #DevFree: Filtramos, para que la cantidad de productos en move_line sea igual a
            # los que vamos a comparar con self.invoice_line_ids
            to_compare = 0
            to_compare2 = 0
            to_compare_ids = []
            error_msg = ''
            for move_many in manager:
                error_msg = error_msg +' - '+ move_many.picking_id.name
                for move_many_lines in move_many.move_lines:
                    if move_many_lines.state == 'done':
                        for move_many_products in move_many_lines.product_id:
                            to_compare += move_many_lines.quantity_done
                        if to_compare <= qty_total:
                            to_compare_ids.append(move_many_lines.picking_id.id)
                            to_compare2 = qty_total - to_compare
                        else:
                            pass
            if to_compare2 != 0:
                raise UserError(_("Los productos o cantidades que intenta facturar, no coincide con los productos o cantidades entregadas en %s.")% (str(error_msg)))
            manager2 = self.env['account.move.manager'].search([('picking_id', 'in', to_compare_ids)])
            for new_move in manager2:
                new_move.active = False
                for new_move_line in new_move.move_lines:
                    stock_move_line = self.env['stock.move.line'].search([('reference', '=', new_move.picking_id.name)])
                    for move_line_record in stock_move_line:
                        stock_move_line.write(
                              {
                                  'doc_num': self.origin + ' (' + self.number + ')',
                                  'partner_name': self.partner_id.name,
                              })
            return to_open_invoices.invoice_validate()
        else:
            if not self.origin:
                return to_open_invoices.invoice_validate()
            else:
                this_ids = []
                qty_total = 0
                for this_inv_lines in self.invoice_line_ids:
                    this_ids.append(this_inv_lines.id)
                    qty_total += this_inv_lines.quantity

                self.env['account.move.manager'].create({ 'is_move':False,
                                                          'is_invoice': True,
                                                          'invoice_line_ids': [(6, 0, this_ids)],
                                                          'invoice_id': self.id,
                                                          'qty_total': qty_total,
                                                          'active': True,
                                                          'origin': str(self.origin),
                })
                return to_open_invoices.invoice_validate()
