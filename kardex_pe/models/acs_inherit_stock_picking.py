# -*- coding: utf-8 -*-


from odoo import api, fields, models, tools, _
from openerp.exceptions import AccessDenied, AccessError, UserError, ValidationError

class ACStockPicking(models.Model):
    _inherit = 'stock.picking'

    # iter_state = fields.Boolean(string="Campo auxiliar", default= False)

    @api.multi
    def action_done(self):
        """Changes picking state to done by processing the Stock Moves of the Picking

        Normally that happens when the button "Done" is pressed on a Picking view.
        @return: True
        """
        # TDE FIXME: remove decorator when migration the remaining
        todo_moves = self.mapped('move_lines').filtered(lambda self: self.state in ['draft', 'waiting', 'partially_available', 'assigned', 'confirmed'])
        # Check if there are ops not linked to moves yet
        for pick in self:
            # # Explode manually added packages
            # for ops in pick.move_line_ids.filtered(lambda x: not x.move_id and not x.product_id):
            #     for quant in ops.package_id.quant_ids: #Or use get_content for multiple levels
            #         self.move_line_ids.create({'product_id': quant.product_id.id,
            #                                    'package_id': quant.package_id.id,
            #                                    'result_package_id': ops.result_package_id,
            #                                    'lot_id': quant.lot_id.id,
            #                                    'owner_id': quant.owner_id.id,
            #                                    'product_uom_id': quant.product_id.uom_id.id,
            #                                    'product_qty': quant.qty,
            #                                    'qty_done': quant.qty,
            #                                    'location_id': quant.location_id.id, # Could be ops too
            #                                    'location_dest_id': ops.location_dest_id.id,
            #                                    'picking_id': pick.id
            #                                    }) # Might change first element
            # # Link existing moves or add moves when no one is related
            for ops in pick.move_line_ids.filtered(lambda x: not x.move_id):
                # Search move with this product
                moves = pick.move_lines.filtered(lambda x: x.product_id == ops.product_id)
                moves = sorted(moves, key=lambda m: m.quantity_done < m.product_qty, reverse=True)
                if moves:
                    ops.move_id = moves[0].id
                else:
                    new_move = self.env['stock.move'].create({
                                                    'name': _('New Move:') + ops.product_id.display_name,
                                                    'product_id': ops.product_id.id,
                                                    'product_uom_qty': ops.qty_done,
                                                    'product_uom': ops.product_uom_id.id,
                                                    'location_id': pick.location_id.id,
                                                    'location_dest_id': pick.location_dest_id.id,
                                                    'picking_id': pick.id,
                                                   })
                    ops.move_id = new_move.id
                    new_move._action_confirm()
                    todo_moves |= new_move
                    #'qty_done': ops.qty_done})

        # DevFree: Se interviene el codigo a partir de este punto
        for lines in todo_moves:
            if lines.purchase_line_id:
                order = self.env['purchase.order'].search([('name','=',lines.origin)])
                partner_id = lines.purchase_line_id.partner_id.name
                supplier_ref = order.partner_ref
                if not supplier_ref:
                    mov = order.name
                else:
                    mov = order.name +' ('+ supplier_ref + ')'
                for order_line in order.order_line:
                    if order_line.product_id.id == lines.product_id.id:
                        if order_line.price_subtotal == 0 or order_line.product_qty == 0:
                            new_move_line = self.env['stock.move.line'].search([('move_id','=',lines.id)]).write({
                                                    'doc_num': mov,
                                                    'partner_name': partner_id,
                                                    'price_unit': 0.00,
                                                   })
                            break
                        else:
                            price = order_line.price_subtotal / order_line.product_qty
                            new_move_line = self.env['stock.move.line'].search([('move_id','=',lines.id)]).write({
                                                    'doc_num': mov,
                                                    'partner_name': partner_id,
                                                    'price_unit': price,
                                                   })
                            break
            elif lines.sale_line_id:
                #DevFree: Desde aca intervenimos codigo
                # invoice_id = self.env['account.invoice'].search(['&',('origin','=',self.origin),('state','in',('open','paid'))])
                manager = self.env['account.move.manager'].search(['&',('origin','=',self.origin),'&',('is_invoice','=',True),('active','=',True)])
                # if restriction > 1:
                #     raise UserError(_("NO PUEDES"))

                if manager:
                    #DevFree: Procesamos los productos que estamos facturando en este momento self.invoice_line_ids
                    # manager = self.env['account.move.manager'].search(['&',('origin','=',self.origin),'&',('is_invoice','=',True),('active','=',True)])
                    this_ids = []
                    this_create = []
                    this_count = 0
                    qty_total = 0
                    for this_move_lines in self.move_lines:
                        for this_move_products in this_move_lines.product_id:
                            this_ids.append(this_move_products.id)
                            this_create.append(this_move_lines.id)
                            this_count += 1
                            qty_total += this_move_lines.quantity_done
                    #DevFree: Filtramos, para que la cantidad de productos en move_line sea igual a
                    # los que vamos a comparar con self.invoice_line_ids
                    to_compare = 0
                    to_compare2 = 0
                    to_compare_ids = []
                    for inv_many in manager:
                        for inv_many_lines in inv_many.invoice_line_ids:
                            if inv_many.invoice_id.state in ('open'):
                                for inv_many_products in inv_many_lines.product_id:
                                    to_compare += inv_many_lines.quantity
                                if to_compare <= qty_total:
                                    to_compare_ids.append(inv_many_lines.invoice_id.id)
                                    to_compare2 = qty_total - to_compare
                                elif to_compare > qty_total:
                                    raise UserError(_("La cantidad de productos que intenta entregar, difiere con las cantidades facturadas en %s.")% (str(manager.invoice_id.number)))
                    if to_compare2 != 0:
                        raise UserError(_("La cantidad de productos que intenta entregar, difiere con las cantidades facturadas en %s.")% (str(manager.invoice_id.number)))
                    manager2 = self.env['account.move.manager'].search([('invoice_id', 'in', to_compare_ids)])
                    stock_move_line = self.env['stock.move.line'].search([('picking_id', '=', self.id)])
                    for new_move in manager2:
                        new_move.active = False
                    order_id = self.env['sale.order'].search([('name','=',self.origin)])

                    for product_price in order_id.order_line:
                        for move_price in stock_move_line:
                            if move_price.product_id.id == product_price.product_id.id:
                                # price = product_price.price_subtotal / product_price.product_uom_qty
                                price = product_price.sale_order_line_pdesc
                                new_move_line = self.env['stock.move.line'].search([('id','=',move_price.id)]).write({'doc_num': self.origin + ' (' + manager2.invoice_id.number + ')',
                                                    'partner_name': self.partner_id.name,
                                                    'price_unit': price,
                                                   })
                    todo_moves._action_done()
                    self.write({'date_done': fields.Datetime.now()})
                    return True
                else:
                    if not self.origin:
                        return to_open_invoices.invoice_validate()
                    else:
                        this_ids = []
                        qty_total = 0
                        for this_move_lines in self.move_lines:
                            this_ids.append(this_move_lines.id)
                            qty_total += this_move_lines.quantity_done

                        self.env['account.move.manager'].create({ 'is_move':True,
                                                                  'is_invoice': False,
                                                                  'move_lines': [(6, 0, this_ids)],
                                                                  'picking_id': self.id,
                                                                  'qty_total': qty_total,
                                                                  'active': True,
                                                                  'origin': str(self.origin),
                        })

                        move_line_id = self.env['stock.move.line'].search([('picking_id','=',self.id)])
                        order_id = self.env['sale.order'].search([('name','=',self.origin)])

                        for product_price in order_id.order_line:
                            for move_price in move_line_id:
                                if move_price.product_id.id == product_price.product_id.id:
                                    price = product_price.price_subtotal / product_price.product_uom_qty
                                    new_move_line = self.env['stock.move.line'].search([('id','=',move_price.id)]).write({'doc_num': self.origin,
                                                        'partner_name': self.partner_id.name,
                                                        'price_unit': price,
                                                       })
                        todo_moves._action_done()
                        self.write({'date_done': fields.Datetime.now()})
                        return True
