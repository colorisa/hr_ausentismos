##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

import datetime
import math
import time
from operator import attrgetter

from openerp.exceptions import Warning
from openerp import tools
from openerp.osv import fields, osv
from openerp.tools.translate import _

class hr_diag_c3(osv.osv):

    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name','code'], context=context)
        res = []
        for record in reads:
            name = record['code'] + ' - ' + record['name'] 
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    _name = "hr.diag.c3"
    _description = "Categoria Diagnostico"
    _columns = {
        'code': fields.char('Codigo', required=True, translate=True, select=True),
        'name': fields.char('Nombre', required=True, translate=True, select=True),
        'c3' : fields.one2many('hr.diag', 'c3_id', 'Categoria'),
        'complete_name': fields.function(_name_get_fnc, type="char", string='Nombre Completo'),
    }

class hr_diag(osv.osv):

    _name = "hr.diag"
    _description = "Diagnostico"
    _columns = {
        'code': fields.char('Codigo', required=True, translate=True, select=True),
        'name': fields.char('Nombre', required=True, translate=True, select=True),
        'c3_id': fields.many2one('hr.diag.c3', 'Categoria', select=True),
    }
    
class hr_entss(osv.osv):

    _name = "hr.entss"
    _description = "Entidades de Seguridad Social"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _rec_name = 'entidad'
    _columns = {
        'code': fields.char('Codigo', required=True, translate=True, select=True),
        'entidad': fields.many2one('res.partner', 'Proveedor', required=True, domain = [('supplier','=',True)], ondelete='cascade', help="Entidad Seguridad Social"),
        'tipo': fields.selection([
            ('arl', 'Administradora de Riesgos Laborales'),
            ('afp', 'Administradora de Fondos de Pension'),
            ('afc', 'Administradora de Fondos de Cesantias'),
            ('eps', 'Entidad Promotora de Salud'),
            ('ccf', 'Caja de Compensacion Familiar'),
            ]
            ,'Tipo', help="Identifica que tipo de entidad segun el Sistema de Seguridad Social Colombiano.", select=True, required=True),
        'codigo_nacional': fields.char('Codigo Nacional'),
    }
    
class hr_contract(osv.osv):
    _inherit = "hr.contract"
    _name = "hr.contract"
    _columns = {
        'arl_id': fields.many2one('hr.entss', 'Administradora de Riesgos Laborales', required=True, store=True,domain = [('tipo','=','arl')], help="."),
        'afp_id': fields.many2one('hr.entss', 'Administradora de Fondos de Pension', required=True, store=True,domain = [('tipo','=','afp')], help="."),
        'afc_id': fields.many2one('hr.entss', 'Administradora de Fondos de Cesantias', store=True,domain = [('tipo','=','afc')], help='.'),
        'eps_id': fields.many2one('hr.entss', 'Entidad Promotora de Salud', required=True, store=True,domain = [('tipo','=','eps')], help='.'),
        'ccf_id': fields.many2one('hr.entss', 'Caja de Compensacion Familiar', required=True, store=True,domain = [('tipo','=','ccf')], help='.'),
    }
        
    
class hr_holidays(osv.osv):
    _name = "hr.holidays"
    _inherit = ['hr.holidays']
    
    def _compute_number_of_hours(self, cr, uid, ids, name, args, context=None):
        result = {}
        for hol in self.browse(cr, uid, ids, context=context):
            if hol.type=='remove':
                result[hol.id] = -hol.number_of_hours_temp
            else:
                result[hol.id] = hol.number_of_hours_temp
        return result
    
    def get_department(self, cr, uid, ids,context=None):
        #print "Entro"
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        reads = self.browse(cr, uid, ids)
        res = []
        ref = ""
        for records in reads:
            ref = records.employee_id.department_id.name
            if ref:
                res.append((records['id'], ref))
        return res

    
    def _get_department(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.get_department(cr, uid, ids, context=context)
        return dict(res)
    
    _columns = {
        'number_of_hours_temp': fields.float('Allocation Hour', readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]}, copy=False),
        'number_of_hours': fields.function(_compute_number_of_hours, string='Number of Hours', store=True),
        'department_id': fields.function(_get_department,type='char' ,string='Departamento', store=True),
        }
    
    def onchange_date_from(self, cr, uid, ids, date_to, date_from):
        """
        If there are no date set for date_to, automatically set one 8 hours later than
        the date_from.
        Also update the number_of_days.
        """
        # date_to has to be greater than date_from
        if (date_from and date_to) and (date_from > date_to):
            raise osv.except_osv(_('Warning!'),_('The start date must be anterior to the end date.'))

        result = {'value': {}}

        # No date_to set so far: automatically compute one 8 hours later
        if date_from and not date_to:
            date_to_with_delta = datetime.datetime.strptime(date_from, tools.DEFAULT_SERVER_DATETIME_FORMAT) + datetime.timedelta(hours=8)
            result['value']['date_to'] = str(date_to_with_delta)

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            diff_day = self._get_number_of_days(date_from, date_to)
            result['value']['number_of_days_temp'] = diff_day * 2.5
            result['value']['number_of_hours_temp'] = diff_day * 2.5 * 9.6
        else:
            result['value']['number_of_days_temp'] = 0
            result['value']['number_of_hours_temp'] = 0

        return result

    def onchange_date_to(self, cr, uid, ids, date_to, date_from):
        """
        Update the number_of_days.
        """

        # date_to has to be greater than date_from
        if (date_from and date_to) and (date_from > date_to):
            raise osv.except_osv(_('Warning!'),_('The start date must be anterior to the end date.'))

        result = {'value': {}}

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            diff_day = self._get_number_of_days(date_from, date_to)
            result['value']['number_of_days_temp'] = diff_day * 2.5
            result['value']['number_of_hours_temp'] = diff_day * 2.5 * 9.6
        else:
            result['value']['number_of_days_temp'] = 0
            result['value']['number_of_hours_temp'] = 0

        return result
    



    

    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
