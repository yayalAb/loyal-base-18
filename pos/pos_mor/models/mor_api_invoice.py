from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import requests
from datetime import datetime


class MorApiInvoice(models.Model):
    _name = 'mor.api.invoice'
    _description = 'MOR Invoice Registration'
    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Related Invoice',
        ondelete='cascade'
    )

    name = fields.Char(string="Document Number")
    status = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('done', 'Done'),
        ('error', 'Error')
    ], default='draft', string="Status")
    response_message = fields.Text("API Response")
    irn = fields.Char("IRN")
    ack_date = fields.Char("Acknowledgement Date")
    signed_qr = fields.Binary("Signed QR")
    signed_invoice = fields.Text("Signed Invoice")
    error_message = fields.Text("Error Message")
    documant_no = fields.Integer(
        string="Document NO",
    )

    def mor_api_request(self, url, payload):
        """Send invoice to MoR API and handle all response cases."""
        base_url = self.env['ir.config_parameter'].sudo(
        ).get_param('pos_mor.base_url')

        endpoint = f"{base_url.rstrip('/')}{url}"
        token_record = self.env['mor.api'].ensure_valid_token()
        if not token_record or not token_record['access_token']:
            raise UserError(_("Missing access token for MoR API."))
        print("payload payload payload payload payload: ", endpoint)
        headers = {
            "Authorization": f"Bearer {token_record['access_token']}",
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(
                endpoint, headers=headers, json=payload, timeout=60)
            result = response.json()
            print("mor api request response response response: ",
                  response, result)
        except Exception as e:
            raise UserError(_("Error connecting to MoR API: %s") % e)
        return result

    def register_single_invoice(self, invoice):
        """Send invoice to MoR API and handle all response cases."""
        invoice_body = self.preper_invoice_payload(invoice)
        result = self.mor_api_request("/v1/register", invoice_body)
        status_code = result.get("statusCode")
        message = result.get("message")
        body = result.get("body")
        documant_no = invoice_body['DocumentDetails']['DocumentNumber']

        # 🟩 SUCCESS RESPONSE
        if status_code == 200 and message == "SUCCESS":
            invoice.write(
                {'irn': body.get("irn"), 'status': 'done', 'signed_qr': body.get("signedQR"), 'signed_invoice': body.get("signedInvoice")
                 })

            self.create({
                'status': 'done',
                'move_id': invoice.id,
                'irn': body.get("irn"),
                'ack_date': body.get("ackDate"),
                'documant_no': documant_no,
                'signed_qr': body.get("signedQR"),
                'signed_invoice': body.get("signedInvoice"),
                'response_message': json.dumps(result, indent=4),
            })
            return {
                "status": "success",
                "irn": body.get("irn"),
                "ack_date": body.get("ackDate"),
                "signed_qr": body.get("signedQR"),
                "documentNumber": body.get("documentNumber"),
                "signed_invoice": body.get("signedInvoice"),
            }

        # 🟨 VALIDATION ERROR
        elif status_code == 406 and message == "RULE VALIDATION ERROR":
            error_details = []
            for err in body:
                portion = err.get("portion")
                messages = err.get("errorMessage", [])
                error_details.append(f"{portion}: {', '.join(messages)}")
            error_text = "\n".join(error_details)

            self.create({
                'status': 'error',
                'error_message': error_text,
                'response_message': json.dumps(result, indent=4),
            })
            return {
                "status": "validation_error",
                "error": error_text
            }

        # 🟥 SCHEMA ERROR
        elif status_code == 400 and message == "SCHEMA ERROR":
            schema_errors = []
            for err in body:
                schema_errors.append(
                    f"{err.get('property')}: {err.get('message')} (Code: {err.get('code')})"
                )
            schema_text = "\n".join(schema_errors)

            self.create({
                'status': 'error',
                'error_message': schema_text,
                'response_message': json.dumps(result, indent=4),
            })
            return {
                "status": "schema_error",
                "error": schema_text
            }

        # ❓ UNKNOWN ERROR
        else:
            self.create({
                'status': 'error',
                'error_message': f"Unknown response: {result}",
                'response_message': json.dumps(result, indent=4),
            })
            return {
                "status": "unknown_error",
                "response": result
            }

    def register_multi_invoice(self, invoices, previous_irn=""):
        """Register multiple invoices in bulk with proper chaining."""
        last_done = self.env['mor.api.invoice'].search(
            [('status', '=', 'done')], order='create_date desc', limit=1)
        last_doc_no = last_done.documant_no if last_done else 0
        last_irn = last_done.irn if last_done else previous_irn or ""
        payload = []
        current_doc_no = last_doc_no

        for index, inv in enumerate(invoices, start=1):
            current_doc_no += 1
            if index == 1:
                ref_irn = last_irn
            else:
                ref_irn = ""
            inv_body = self.preper_invoice_payload(
                inv, current_doc_no, ref_irn)
            payload.append(inv_body)
        print("payload payload payload payload payload: ", payload)
        result = self.mor_api_request("/v1/bulkRegister", payload)

        return result

    def cancel_single_invoice(self, irn, reason_code='1', remark=''):
        """Cancel an invoice via MoR API."""
        payload = {
            "Irn": irn,
            "ReasonCode": reason_code,
            "Remark": remark
        }
        result = self.mor_api_request("/v1/cancel", payload)
        status_code = result.get("statusCode")
        message = result.get("message")
        body = result.get("body")

        # ✅ Success
        if status_code == 200 and message.lower() == "success":
            self.write({
                'status': 'cancelled',
                'response_message': json.dumps(result, indent=4),
            })
            return {
                "status": "success",
                "cancellation_date": body.get("cancellationDate")
            }

        # 🟨 Schema Error
        elif status_code == 400 and message.upper() == "SCHEMA_ERROR":
            schema_errors = []
            for err in body:
                schema_errors.append(
                    f"{err.get('instanceLocation')}: {err.get('message')} (Code: {err.get('code')})"
                )
            schema_text = "\n".join(schema_errors)
            self.write({
                'status': 'error',
                'error_message': schema_text,
                'response_message': json.dumps(result, indent=4),
            })
            return {
                "status": "schema_error",
                "error": schema_text
            }

        # 🟨 Rule Validation Error
        elif status_code == 406 and "rule_validation_error" in message.lower():
            error_text = "\n".join(
                body if isinstance(body, list) else [str(body)])
            self.write({
                'status': 'error',
                'error_message': error_text,
                'response_message': json.dumps(result, indent=4),
            })
            return {
                "status": "validation_error",
                "error": error_text
            }

        # ❓ Unknown Error
        else:
            self.write({
                'status': 'error',
                'error_message': f"Unknown response: {result}",
                'response_message': json.dumps(result, indent=4),
            })
            return {
                "status": "unknown_error",
                "response": result
            }

    def cancel_bulk_invoice(self, invoices, reason_code='1', remark=''):
        """Cancel multiple invoices via MoR API."""
        payload = []

        # 🧩 Build payload
        for inv in invoices:
            if inv.status == "done":
                payload.append({
                    "Irn": inv.irn,
                    "ReasonCode": reason_code,
                    "Remark": remark
                })

        # 🔗 Call API
        result = self.mor_api_request("/v1/bulkCancel", payload)
        status_code = result.get("statusCode")
        message = result.get("message")
        body = result.get("body", [])

        # === ✅ 200 and message "Received" ===
        if status_code == 200 and message.lower() == "received":
            success_irns, failed_irns, details = [], [], []

            for item in body:
                irn = item.get("Irn")
                status = item.get("status") or item.get("Status")
                msg = item.get("msg") or item.get("Remark") or "No message"

                if status == "C":  # ✅ Cancelled successfully
                    success_irns.append(irn)
                    details.append(f"IRN {irn}: Cancelled successfully.")
                else:  # ❌ Failed / processing error
                    failed_irns.append(irn)
                    details.append(f"IRN {irn}: Failed - {msg}")

            # === Update each invoice ===
            for inv in invoices:
                if inv.irn in success_irns:
                    inv.write({'status': 'cancelled'})
                elif inv.irn in failed_irns:
                    inv.write({'status': 'error'})

            # Log full API response for traceability
            self.create({
                'response_message': json.dumps(result, indent=4),
                'error_message': "\n".join(details)
            })

            # Determine final status summary
            if len(success_irns) == len(invoices):
                overall_status = "success"
            elif len(failed_irns) == len(invoices):
                overall_status = "failed"
            else:
                overall_status = "partial_success"

            return {
                "status": overall_status,
                "success_count": len(success_irns),
                "failed_count": len(failed_irns),
                "details": details,
            }

        # === 🧩 400 SCHEMA ERROR ===
        elif status_code == 400 and message.upper() == "SCHEMA_ERROR":
            schema_details = []

            for item in body:
                irn = item.get("Irn")
                for err in item.get("body", []):
                    schema_details.append(
                        f"IRN {irn}: {err.get('message')} "
                        f"(Code: {err.get('code')}, Field: {err.get('property')})"
                    )

            schema_text = "\n".join(schema_details)
            self.create({
                'status': 'error',
                'error_message': schema_text,
                'response_message': json.dumps(result, indent=4),
            })

            return {
                "status": "schema_error",
                "error_count": len(schema_details),
                "errors": schema_details
            }

        # === ❌ Any Other Response ===
        else:
            self.create({
                'status': 'error',
                'error_message': message or 'Unknown error occurred',
                'response_message': json.dumps(result, indent=4),
            })

            return {
                "status": "failed",
                "error": message or 'Unknown error occurred',
            }

    def verify_invoice(self, irn):

        payload = {"irn": irn}
        result = self.mor_api_request("/v1/verify", payload)

        status_code = result.get("statusCode")
        message = result.get("message")
        body = result.get("body")

        # ✅ Success
        if status_code == 200 and message.upper() == "SUCCESS":
            self.write({
                'status': 'verified',
                'response_message': json.dumps(result, indent=4),
            })
            return {
                "status": "success",
                "invoice_data": body
            }

        # 🟨 Invoice Not Registered
        elif status_code == 400 and message.upper() == "VERIFICATION ERROR":
            error_msg = body.get("message", "Invoice not registered")
            self.write({
                'status': 'error',
                'error_message': error_msg,
                'response_message': json.dumps(result, indent=4),
            })
            return {
                "status": "not_registered",
                "error": error_msg
            }

        # 🟨 Schema Error
        elif status_code == 400 and message.upper() == "SCHEMA ERROR":
            schema_errors = []
            for err in body:
                schema_errors.append(
                    f"{err.get('instanceLocation')}: {err.get('message')} (Code: {err.get('code')})"
                )
            schema_text = "\n".join(schema_errors)
            self.write({
                'status': 'error',
                'error_message': schema_text,
                'response_message': json.dumps(result, indent=4),
            })
            return {
                "status": "schema_error",
                "error": schema_text
            }

        # ❓ Unknown Error
        else:
            self.write({
                'status': 'error',
                'error_message': f"Unknown response: {result}",
                'response_message': json.dumps(result, indent=4),
            })
            return {
                "status": "unknown_error",
                "response": result
            }

    def preper_invoice_payload(self, invoice, is_mulit=False, last_irn=""):
        """Prepare MoR-compliant invoice body from Odoo invoice"""
        his = self.env['mor.api.invoice'].search(
            [('status', '=', 'done')], order='create_date desc', limit=1)
        documant_no = 38
        if his and not is_mulit:
            documant_no = his.documant_no + 1
        elif is_mulit:
            documant_no = is_mulit
        if not invoice:
            raise UserError(_("No invoice provided."))

        partner = invoice.partner_id
        company = invoice.company_id

        # === 1️⃣ Buyer Details ===
        buyer_details = {
            "City": partner.city or "0",
            "Email": "user804346@gmail.com",
            "HouseNumber": partner.street or "NEW",
            "IdNumber": getattr(partner, "id_number", "") or "11122222222222222",
            "IdType": getattr(partner, "id_type", "KID"),
            "LegalName": partner.name or "ABC Trading",
            "Phone": partner.phone or "0912345678",
            "Region": "13",
            "Country": partner.country_id and partner.country_id.code or "70",
            "Zone": getattr(partner, "zone", "SHA"),
            "Kebele": getattr(partner, "kebele", "03"),
            "Wereda": getattr(partner, "wereda", "574"),
        }

        # === 2️⃣ Document Details ===
        invoice_date = invoice.invoice_date or datetime.now()

        # Convert to the required format: dd-MM-yyyy'T'HH:mm:ss
        formatted_date = invoice_date.strftime("%d-%m-%YT%H:%M:%S")
        document_details = {
            "DocumentNumber": documant_no,
            "Date": formatted_date,
            "Type": "INV"
        }

        # === 3️⃣ Item List ===
        item_list = []
        for idx, line in enumerate(invoice.invoice_line_ids, start=1):
            tax_rate = sum(line.tax_ids.mapped(
                "amount")) if line.tax_ids else 0
            tax_code = "VAT15"  # static default per MoR structure
            pretax = line.price_subtotal
            tax_amount = pretax * (tax_rate / 100)
            total_line = pretax + tax_amount

            item_list.append({
                "Discount": 0,
                "ExciseTaxValue": 0,
                "NatureOfSupplies": "goods",
                "ItemCode": line.product_id.default_code or "1111",
                "ProductDescription": line.product_id.name or line.name or "string",
                "PreTaxValue": pretax,
                "Quantity": line.quantity,
                "LineNumber": idx,
                "TaxAmount": tax_amount,
                "TaxCode": tax_code,
                "TotalLineAmount": total_line,
                "Unit": line.product_uom_id.name or "PCS",
                "UnitPrice": line.price_unit,
            })

        # === 4️⃣ Payment Details ===
        payment_details = {
            "Mode": "CASH",
            "PaymentTerm": "IMMIDIATE",
        }

        # === 5️⃣ Reference Details ===
        reference_details = {
            "PreviousIrn": last_irn,
            "RelatedDocument": None,
        }

        # === 6️⃣ Seller Details ===
        seller_details = {
            "City": "101",
            "Email": "Anwar.Yesuf@niyatconsultancy.com",
            "HouseNumber": 101,
            "LegalName": company.name or "{{sellerLegalName}}",
            "Locality": False,
            "Phone": "+251912359676",
            "Region": "1",
            "SubCity": "Bole",
            "Tin": "0095009268",
            "VatNumber": "43256663343256663322",
            "Wereda": "13",
        }

        # === 7️⃣ Source System ===
        source_system = {
            "CashierName": self.env.user.name or "AAA",
            "InvoiceCounter": documant_no,
            "SalesPersonName": invoice.invoice_user_id.name or "AAA",
            "SystemNumber": "3D4865D720",
            "SystemType": "POS",
        }

        # === 8️⃣ Value Details ===
        value_details = {
            "Discount": 0,
            "ExciseValue": 0,
            "IncomeWithholdValue": getattr(invoice, "income_withhold", 220),
            "TaxValue": invoice.amount_tax or 0,
            "TotalValue": invoice.amount_total or 0,
            "TransactionWithholdValue": getattr(invoice, "transaction_withhold", 0),
            "InvoiceCurrency": "ETB",
        }

        # === ✅ Final Body ===
        invoice_body = {
            "BuyerDetails": buyer_details,
            "DocumentDetails": document_details,
            "ItemList": item_list,
            "PaymentDetails": payment_details,
            "ReferenceDetails": reference_details,
            "SellerDetails": seller_details,
            "SourceSystem": source_system,
            "TransactionType": "B2C",
            "ValueDetails": value_details,
            "Version": "1"
        }
        return invoice_body

    def return_sample_payload(self):
        """Return a sample payload for testing purposes."""
        sample_payload = [
            {
                "BuyerDetails": {
                    "City": "0",
                    "Email": "user804346@gmail.com",
                    "HouseNumber": "NEW",
                    "IdNumber": "11122222222222222",
                    "IdType": "KID",
                    "LegalName": "ABC Trading",
                    "Phone": "0912345678",
                    "Region": "13",
                    "Country": "70",
                    "Zone": "SHA",
                    "Kebele": "03",
                    "Wereda": "574"
                },
                "DocumentDetails": {
                    "DocumentNumber": 36,
                    "Date": "21-03-2025T00:00:00",
                    "Type": "INV"
                },
                "ItemList": [
                    {
                        "Discount": 0,
                        "ExciseTaxValue": 0,
                        "HarmonizationCode": False,
                        "NatureOfSupplies": "goods",
                        "ItemCode": "1111",
                        "ProductDescription": "string",
                        "PreTaxValue": 1000,
                        "Quantity": 1,
                        "LineNumber": 1,
                        "TaxAmount": 150,
                        "TaxCode": "VAT15",
                        "TotalLineAmount": 1150,
                        "Unit": "PCS",
                        "UnitPrice": 1000
                    },
                    {
                        "Discount": 0,
                        "ExciseTaxValue": 0,
                        "HarmonizationCode": False,
                        "NatureOfSupplies": "goods",
                        "ItemCode": "1111",
                        "ProductDescription": "Phone",
                        "PreTaxValue": 10000,
                        "Quantity": 1,
                        "LineNumber": 2,
                        "TaxAmount": 1500,
                        "TaxCode": "VAT15",
                        "TotalLineAmount": 11500,
                        "Unit": "PCS",
                        "UnitPrice": 10000
                    }
                ],
                "PaymentDetails": {
                    "Mode": "CASH",
                    "PaymentTerm": "IMMIDIATE"
                },
                "ReferenceDetails": {
                    "PreviousIrn": "f25d514df91b72f10cfdce53a2a18670944e04362f41ac7fa76619045f18b478",
                    "RelatedDocument": False
                },
                "SellerDetails": {
                    "City": "101",
                    "Email": "Anwar.Yesuf@niyatconsultancy.com",
                    "HouseNumber": 101,
                    "LegalName": "Niyat Consultancy PLC",
                    "Locality": False,
                    "Phone": "+251912359676",
                    "Region": "1",
                    "SubCity": "Bole",
                    "Tin": "0095009268",
                    "VatNumber": "43256663343256663322",
                    "Wereda": "13"
                },
                "SourceSystem": {
                    "CashierName": "Administrator",
                    "InvoiceCounter": 36,
                    "SalesPersonName": "Administrator",
                    "SystemNumber": "3D4865D720",
                    "SystemType": "POS"
                },
                "TransactionType": "B2C",
                "ValueDetails": {
                    "Discount": False,
                    "ExciseValue": 0,
                    "IncomeWithholdValue": 220,
                    "TaxValue": 1650,
                    "TotalValue": 12650,
                    "TransactionWithholdValue": 0,
                    "InvoiceCurrency": "ETB"
                },
                "Version": "1"
            },

            {
                "BuyerDetails": {
                    "City": "0",
                    "Email": "user804346@gmail.com",
                    "HouseNumber": "NEW",
                    "IdNumber": "11122222222222222",
                    "IdType": "KID",
                    "LegalName": "ABC Trading",
                    "Phone": "0912345678",
                    "Region": "13",
                    "Country": "70",
                    "Zone": "SHA",
                    "Kebele": "03",
                    "Wereda": "574"
                },
                "DocumentDetails": {
                    "DocumentNumber": 37,
                    "Date": "21-03-2025T00:00:00",
                    "Type": "INV"
                },
                "ItemList": [
                    {
                        "Discount": 0,
                        "ExciseTaxValue": 0,
                        "HarmonizationCode": False,
                        "NatureOfSupplies": "goods",
                        "ItemCode": "1111",
                        "ProductDescription": "string",
                        "PreTaxValue": 1000,
                        "Quantity": 1,
                        "LineNumber": 1,
                        "TaxAmount": 150,
                        "TaxCode": "VAT15",
                        "TotalLineAmount": 1150,
                        "Unit": "PCS",
                        "UnitPrice": 1000
                    },
                    {
                        "Discount": 0,
                        "ExciseTaxValue": 0,
                        "HarmonizationCode": False,
                        "NatureOfSupplies": "goods",
                        "ItemCode": "1111",
                        "ProductDescription": "Phone",
                        "PreTaxValue": 10000,
                        "Quantity": 1,
                        "LineNumber": 2,
                        "TaxAmount": 1500,
                        "TaxCode": "VAT15",
                        "TotalLineAmount": 11500,
                        "Unit": "PCS",
                        "UnitPrice": 10000
                    }
                ],
                "PaymentDetails": {
                    "Mode": "CASH",
                    "PaymentTerm": "IMMIDIATE"
                },
                "ReferenceDetails": {
                    "PreviousIrn": "f25d514df91b72f10cfdce53a2a18670944e04362f41ac7fa76619045f18b479",
                    "RelatedDocument": False
                },
                "SellerDetails": {
                    "City": "101",
                    "Email": "Anwar.Yesuf@niyatconsultancy.com",
                    "HouseNumber": 101,
                    "LegalName": "Niyat Consultancy PLC",
                    "Locality": False,
                    "Phone": "+251912359676",
                    "Region": "1",
                    "SubCity": "Bole",
                    "Tin": "0095009268",
                    "VatNumber": "43256663343256663322",
                    "Wereda": "13"
                },
                "SourceSystem": {
                    "CashierName": "Administrator",
                    "InvoiceCounter": 37,
                    "SalesPersonName": "Administrator",
                    "SystemNumber": "3D4865D720",
                    "SystemType": "POS"
                },
                "TransactionType": "B2C",
                "ValueDetails": {
                    "Discount": False,
                    "ExciseValue": 0,
                    "IncomeWithholdValue": 220,
                    "TaxValue": 1650,
                    "TotalValue": 12650,
                    "TransactionWithholdValue": 0,
                    "InvoiceCurrency": "ETB"
                },
                "Version": "1"
            }
        ]
        return sample_payload
