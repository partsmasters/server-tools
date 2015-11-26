# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2013 Agile Business Group sagl (<http://www.agilebg.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
from openerp.osv import orm, fields
from openerp import SUPERUSER_ID
from openerp.tools.translate import _


class ir_model(orm.Model):
    _inherit = 'ir.model'

    _columns = {
        'avoid_quick_create': fields.boolean('Avoid quick create'),
        }

    def _wrap_name_create(self, old_create, model):
        def wrapper(cr, uid, name, context=None):
            raise orm.except_orm(
                _('Error'),
                _("Can't create quickly. Opening create form"))
        return wrapper

    def _register_hook(self, cr, ids=None):
        """
        On any model that has been configured to disable quick creation,
        replace the name_create method by a method that raises an exception,
        as this will trigger the full form creation popup in the client,
        effectively disabling the quick create method.

        Without the ids argument, we check all models, but not if we
        have seen them before (marked by the check_quick_create attribute).
        """
        logger = logging.getLogger(
            'openerp.addons.base_optional_quick_create')
        force = True
        if ids is None:
            ids = self.search(cr, SUPERUSER_ID, [])
            force = False
        for model in self.browse(cr, SUPERUSER_ID, ids):
            model_obj = self.pool.get(model.model)
            if not model_obj or (not force and hasattr(
                    model_obj, 'check_quick_create')):
                continue
            if model.avoid_quick_create:
                if not hasattr(model_obj, 'name_create_orig'):
                    logger.debug(
                        'Replacing original name_create method on %s',
                        model.model)
                    model_obj.name_create_orig = model_obj.name_create
                    model_obj.name_create = self._wrap_name_create(
                        model_obj.name_create, model.name)
            else:
                if hasattr(model_obj, 'name_create_orig'):
                    logger.debug(
                        'Restoring original name_create method on %s',
                        model.model)
                    model_obj.name_create = model_obj.name_create_orig
                    delattr(model_obj, 'name_create_orig')
            model_obj.check_quick_create = True
        return True

    def create(self, cr, uid, vals, context=None):
        res_id = super(ir_model, self).create(cr, uid, vals, context=context)
        self._register_hook(cr, [res_id])
        return res_id

    def write(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = super(ir_model, self).write(cr, uid, ids, vals, context=context)
        self._register_hook(cr, ids)
        return res
