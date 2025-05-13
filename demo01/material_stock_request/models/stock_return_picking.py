from odoo import models, _
from odoo.exceptions import ValidationError


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def _create_returns(self):
        res = super()._create_returns()
        if self.picking_id.location_dest_id.id == \
                self.picking_id.stock_request_id.location_dest_id.id:
            raise ValidationError("you can't create a return from a "
                                  "Received transfer")
        else:
            if self.picking_id.stock_request_id:
                for rec in self.product_return_moves:
                    stock_request = self.picking_id.stock_request_id.move_ids\
                        .filtered(lambda l:l.product_id.id ==
                                           rec.product_id.id)
                    if rec.quantity > sum(stock_request.mapped('balance_qty')):
                        raise ValidationError("The quantity that can be returned must not exceed the available balance of the product %s"
                                              %rec.product_id.name)
                    else:
                        stock_request.balance_qty = stock_request.issued_qty - stock_request.already_received_qty - stock_request.returned_qty
        return res