# Copyright 2021-2025 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

import odoo.tests
from odoo.exceptions import AccessError
from odoo.tests.common import users
from odoo.tools import mute_logger

from .common import StorageAttachmentBaseCase


@odoo.tests.tagged("post_install", "-at_install")
class TestDmsPortal(odoo.tests.HttpCase, StorageAttachmentBaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env.ref("base.partner_demo_portal")
        cls.portal_user = cls.partner.user_ids
        cls._create_attachment("test.txt")
        cls._create_attachment("test2.txt", cls.other_partner)
        cls.directory_partner = cls._get_partner_directory()
        cls.other_directory_partner = cls._get_partner_directory(cls.other_partner)
        cls.file_partner = cls.directory_partner.file_ids[0]
        cls.other_file_partner = cls.other_directory_partner.file_ids[0]

    def test_access_portal(self):
        self.authenticate("portal", "portal")
        # 404: Incorrect access_token
        file_text = self.create_file(directory=self.directory_partner)
        url = f"{file_text.access_url}&access_token=abc-def"
        response = self.url_open(url, timeout=20)
        self.assertEqual(
            response.status_code, 404, "Can't access file with incorrect access_token"
        )
        # 200
        response = self.url_open(self.file_partner._get_share_url(), timeout=20)
        self.assertEqual(
            response.status_code, 200, "Can access file with correct access_token"
        )
        # 200
        response = self.url_open(self.directory_partner._get_share_url(), timeout=20)
        self.assertEqual(
            response.status_code, 200, "Can access directory with correct access_token"
        )

    def test_tour(self):
        for tour in ("dms_portal_mail_tour", "dms_portal_partners_tour"):
            with self.subTest(tour=tour):
                self.start_tour("/my", tour, login="portal")

    @users("portal")
    @mute_logger("odoo.addons.base.models.ir_rule")
    def test_permission_portal_user_access_own_attachment(self):
        """
        The user can access its own attachments, even if its access group are not set
        """
        # Has to manually su=False because the portal user is not a superuser,
        # but odoo uses somewhere sudo() internally
        file = self.file_partner.with_user(self.env.user).with_env(self.env(su=False))
        directory = self.directory_partner.with_user(self.env.user).with_env(
            self.env(su=False)
        )
        # Portal user can only read
        file.check_access("read")

        # Portal user can't do anything else
        with self.assertRaises(AccessError, msg="Portal user should not have access"):
            file.check_access("write")
            file.check_access("unlink")
            directory.check_access("create")

    @users("portal")
    @mute_logger("odoo.addons.base.models.ir_rule")
    def test_permission_portal_user_access_other_attachment(self):
        """
        The user can't access other attachments if its access group are not set
        """
        # Has to manually su=False because the portal user is not a superuser,
        # but odoo uses somewhere sudo() internally
        file = self.other_file_partner.with_user(self.env.user).with_env(
            self.env(su=False)
        )
        # file.invalidate_recordset()
        # Portal user can't do anything
        with self.assertRaises(AccessError, msg="Portal user should not have access"):
            file.check_access("read")
        with self.assertRaises(AccessError, msg="Portal user should not have access"):
            file.check_access("write")
        with self.assertRaises(AccessError, msg="Portal user should not have access"):
            file.check_access("unlink")
