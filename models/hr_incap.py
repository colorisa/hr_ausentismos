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

from openerp.osv import fields, osv
from datetime import datetime, timedelta, date

class hr_incap(osv.osv):

    _name = "hr.incap"
    _rec_name = "numero"
    _description = "Incapacidades"
    
    def get_dias(self, cr, uid, ids, context=None):
        #res = self.get_ref(cr, uid, ids, context=context)
        #return dict(res)
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        reads = self.browse(cr, uid, ids)
        res = []
        td = ""
        for records in reads:
            td = (datetime(int(records.fecha_fin[0:4]),int(records.fecha_fin[5:7]),int(records.fecha_fin[8:10])) - datetime(int(records.fecha_ini[0:4]),int(records.fecha_ini[5:7]),int(records.fecha_ini[8:10]))) + timedelta(days=1)
            if td.days:
                res.append((records['id'], td.days))
        return res  
    
    def _get_dias(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.get_dias(cr, uid, ids, context=context)
        return dict(res)
    
    def get_dia(self, cr, uid, ids, context=None):
        #res = self.get_ref(cr, uid, ids, context=context)
        #return dict(res)
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        reads = self.browse(cr, uid, ids)
        res = []
        td = ""
        dia = ""
        for records in reads:
            td = date(int(records.fecha_ini[0:4]),int(records.fecha_ini[5:7]),int(records.fecha_ini[8:10])).isoweekday()
            if td:
                if td == 1:
                    dia = "Lunes"
                if td == 2:
                    dia = "Martes"
                if td == 3:
                    dia = "Miercoles"
                if td == 4:
                    dia = "Jueves"
                if td == 5:
                    dia = "Viernes"    
                if td == 6:
                    dia = "Sabado"    
                if td == 7:
                    dia = "Domingo"    
                res.append((records['id'], dia))
        return res  
    
    def _get_dia(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.get_dia(cr, uid, ids, context=context)
        return dict(res)
    
    
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
        'numero': fields.char('Numero Incapacidad', required=True, translate=True, select=True),
        'ori_incap': fields.selection([
            ('EG', 'Enfermedad general'),
            ('AT', 'Accidente de trabajo'),
            ],'Origen Incapacidad', help="", select=True, required=True),
        'fecha_ini': fields.datetime('Fecha Inicio', required=True, select=True),
        'fecha_fin': fields.datetime('Fecha Finalizacion', required=True, select=True),
        'employee_id': fields.many2one('hr.employee', "Employee", required=True),
        'department_id': fields.function(_get_department,type='char' ,string='Departamento', store=True),
        'dias': fields.function(_get_dias, string='Dias otorgados', store=True),
        'dia': fields.function(_get_dia, string='Dia', type="char", store=True),
        'cod_diag': fields.many2one('hr.diag', 'Codigo DX',required=True, store=True),
        'prorroga': fields.selection([
            ('INI', 'Inicial'),
            ('PRO', 'Prorroga'),
            ],'Inicial o Prorroga', help="", select=True, required=True),
    }

    def _check_period(self, cr, uid, ids, context=None):
        for incap in self.browse(cr, uid, ids, context=context):
            domain = [
                ('empleado', '=', incap.empleado.id),
                ('fecha_ini', '<=', incap.fecha_fin),
                ('fecha_fin', '>=', incap.fecha_ini),
            ]
            incapacidades = self.search_count(cr, uid, domain, context=context)
            print incapacidades
            if incapacidades:
                return False
        return True
        
    def _check_prorroga(self, cr, uid, ids, context=None):
        for incap in self.browse(cr, uid, ids, context=context):
            if incap.prorroga == 'PRO':
                incap_ini = self.search(cr, uid, [('empleado', '=', incap.empleado), ('numero', '=', incap.numero), ('prorroga', '=', 'INI')], limit=1)
                if not incap_ini:
                    return False
        return True
    
    def _check_fecha(self, cr, uid, ids, context=None):
        for incap in self.browse(cr, uid, ids, context=context):
            if incap.fecha_ini > incap.fecha_fin:
                return False
        return True

    _constraints = [#(_check_period, 'Error. Existe otra incapacidad del mismo empleado en conflicto de fechas con esta. ',['fecha_ini','fecha_fin']),
                    #(_check_prorroga, 'Error. No es posible ingresar una prorroga sin una incapacidad inicial', ['prorroga']),
                    (_check_fecha, "Error. La fecha inicial debe ser inferior a la final.", ['fecha_ini','fecha_fin'])
                    ]
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
