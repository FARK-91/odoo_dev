# -*- coding: utf-8 -*-


from odoo import api, fields, models, tools, _


class ACStockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    doc_num = fields.Char(string='Ref. Movimiento')
    partner_name = fields.Char(string='Socio')
    price_unit = fields.Float(string='Precio unitario')


    # DevFree: Metodo para setear todos los valores del modelo stock.move.line
    # se utilizara una sola vez, lo tanto se debe eliminar despues de usar.
    api.multi
    def _delete_later(self):
        move_line_obj = self.env['stock.move.line'].search([('id', '>', 0)])
        for move_line in move_line_obj:
            move_obj = self.env['stock.picking'].search([('name', '=', move_line.reference)])
            if not move_obj.sale_id:
                order = self.env['purchase.order'].search([('name','=',move_obj.origin)])
                partner_id = move_obj.partner_id.name
                supplier_ref = order.partner_ref
                if not supplier_ref:
                    mov = order.name
                else:
                    mov = order.name +'/'+supplier_ref
                for order_line in order.order_line:
                    if order_line.product_id.id == move_obj.product_id.id:
                        if order_line.price_subtotal == 0 or order_line.product_qty == 0:
                            new_move_line = self.env['stock.move.line'].search([('move_id','=',move_obj.id)]).write({
                                                    'doc_num': mov,
                                                    'partner_name': partner_id,
                                                    'price_unit': 0.00,
                                                   })
                            break
                        else:
                            price = order_line.price_subtotal / order_line.product_qty
                            new_move_line = self.env['stock.move.line'].search([('move_id','=',move_obj.id)]).write({
                                                    'doc_num': mov,
                                                    'partner_name': partner_id,
                                                    'price_unit': price,
                                                   })
                            break

            else:
                sale = self.env['sale.order'].search([('name','=',move_obj.origin)])
                partner_id = sale.partner_id.name
                for order_line in sale.order_line:
                    if order_line.product_id.id == move_obj.product_id.id:
                        if order_line.price_subtotal == 0 or order_line.product_uom_qty == 0:
                            new_move_line = self.env['stock.move.line'].search([('move_id','=',move_obj.id)]).write({
                                                    'doc_num': sale.name,
                                                    'partner_name': partner_id,
                                                    'price_unit': 0.00,
                                                   })
                            break
                        else:
                            price = order_line.price_subtotal / order_line.product_uom_qty
                            new_move_line = self.env['stock.move.line'].search([('move_id','=',move_obj.id)]).write({
                                                    'doc_num': sale.name,
                                                    'partner_name': partner_id,
                                                    'price_unit': price,
                                                   })
                            break
        return True
