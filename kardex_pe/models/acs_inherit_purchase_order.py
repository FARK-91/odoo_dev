# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import UserError, AccessError
from odoo.tools.misc import formatLang
from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP
from odoo.addons import decimal_precision as dp


class ACSPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def write(self, vals):
        order = super(ACSPurchaseOrder, self).write(vals)
        if 'partner_ref' in vals:
            partner_ref = vals['partner_ref']
            order = super(ACSPurchaseOrder, self).write(vals)
            picking_obj = self.env['stock.picking'].search([('origin', '=', self.name)])
            if not picking_obj:
                return order
            else:
                for num in picking_obj:
                    if num.state == 'done':
                        picking_name = num.name
                        move_line_obj = self.env['stock.move.line'].search([('reference', '=', picking_name)])
                        for data_update in move_line_obj:
                            doc_num = self.name +' ('+ partner_ref +')'
                            data_update.write({'doc_num': doc_num,})
        return order
