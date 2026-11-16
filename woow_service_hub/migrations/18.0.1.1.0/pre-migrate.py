"""18.0.1.1.0: Internal Manager points to res.users instead of hr.employee.

The module no longer depends on hr: the employee model was only used for
this one optional field. Existing values are hr_employee ids, so each one is
replaced by the employee's linked user (hr_employee.user_id). An employee
without a user account cannot be mapped: the value is cleared and the
service is logged so an administrator can pick a user. hr itself stays
installed; uninstall it separately if nothing else needs it.

Runs before the ORM updates the column. The old foreign key to hr_employee
is dropped here (the ORM then creates the one to res_users). That foreign key
is also the marker that the column still holds employee ids, so the script
is a no-op on fresh installs and when run again.
"""
import logging

from odoo.tools import SQL

_logger = logging.getLogger(__name__)


def _employee_foreign_keys(cr):
    cr.execute("""
        SELECT c.conname
          FROM pg_constraint c
          JOIN pg_attribute a
            ON a.attrelid = c.conrelid AND a.attnum = ANY (c.conkey)
         WHERE c.contype = 'f'
           AND c.conrelid = to_regclass('woow_service')
           AND c.confrelid = to_regclass('hr_employee')
           AND a.attname = 'internal_manager_id'
    """)
    return [row[0] for row in cr.fetchall()]


def migrate(cr, version):
    if not version:
        return
    foreign_keys = _employee_foreign_keys(cr)
    if not foreign_keys:
        return
    for name in foreign_keys:
        cr.execute(SQL("ALTER TABLE woow_service DROP CONSTRAINT %s", SQL.identifier(name)))

    cr.execute("""
        SELECT s.id, s.name, e.id
          FROM woow_service s
          JOIN hr_employee e ON e.id = s.internal_manager_id
         WHERE e.user_id IS NULL
         ORDER BY s.id
    """)
    cleared = cr.fetchall()
    for service_id, service_name, employee_id in cleared:
        _logger.warning(
            "woow_service_hub: service %s (id=%s): the internal manager "
            "(employee id=%s) has no user account, so it was cleared; "
            "please pick a user.",
            service_name, service_id, employee_id,
        )
    cr.execute("""
        UPDATE woow_service s
           SET internal_manager_id = e.user_id
          FROM hr_employee e
         WHERE e.id = s.internal_manager_id
    """)
    _logger.info(
        "woow_service_hub: internal manager now uses res.users: %s service(s) "
        "moved to the employee's user, %s cleared",
        cr.rowcount - len(cleared), len(cleared),
    )
