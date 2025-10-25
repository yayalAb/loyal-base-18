from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import json
from datetime import datetime


class MorApiReceipt(models.Model):
    _name = 'mor.api.receipt'
    _description = 'MOR Payment Receipt'

    receipt_number = fields.Char(string="Receipt Number")
    payment_id = fields.Many2one(
        'account.payment', string="Payment", ondelete='cascade')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('done', 'Done'),
        ('error', 'Error')
    ], default='draft', string="Status")
    response_message = fields.Text("API Response")
    error_message = fields.Text("Error Message")
    rrn = fields.Char("RRN")
    qr_code = fields.Binary("QR Code")
    collected_amount = fields.Float("Collected Amount")

    def register_single_receipt(self, payment):
        """Send payment receipt to MoR API and handle response."""
        receipt_body = self.prepare_receipt_body(payment)
        result = self.env['mor.api.invoice'].mor_api_request(
            "/v1/receipt/sales", receipt_body)
        status_code = result.get("statusCode")
        message = result.get("message")
        body = result.get("body")

        # SUCCESS RESPONSE
        if status_code == 200 and message.upper() == "SUCCESS":
            receipt = self.create({
                'payment_id': payment.id,
                'status': 'done',
                'collected_amount': receipt_body.get('CollectedAmount'),
                'rrn': body.get("rrn"),
                'qr_code': body.get("qr"),
                'response_message': json.dumps(result, indent=4)
            })
            return {
                "status": "success",
                "rrn": body.get("rrn"),
                "qr": body.get("qr")
            }

        # SCHEMA ERROR
        elif status_code == 400 and message.upper() == "SCHEMA ERROR":
            schema_errors = []
            for err in body:
                schema_errors.append(
                    f"{err.get('property')}: {err.get('message')} (Code: {err.get('code')})")
            schema_text = "\n".join(schema_errors)
            self.create({
                'payment_id': payment.id,
                'status': 'error',
                'error_message': schema_text,
                'response_message': json.dumps(result, indent=4)
            })
            return {
                "status": "schema_error",
                "error": schema_text
            }

        # RULE VALIDATION / BUSINESS ERROR
        elif status_code == 406:
            error_details = []
            if 'unknownIrn' in body:
                error_details.append(
                    f"Unknown IRNs: {', '.join(body['unknownIrn'])}")
            if 'dataMissMuch' in body:
                for dm in body['dataMissMuch']:
                    error_details.append(
                        f"{dm.get('tag')}: {', '.join(dm.get('errorMessage', []))}")
            if 'ruleErrorDto' in body:
                for rule in body['ruleErrorDto']:
                    portion = rule.get("portion", "")
                    messages = "error"
                    # messages = ", ".join(
                    #     sum(rule.get("errorMessage", []), []))  # flatten list
                    error_details.append(f"{portion}: {messages}")
            error_text = "\n".join(error_details)
            self.create({
                'payment_id': payment.id,
                'status': 'error',
                'error_message': error_text,
                'response_message': json.dumps(result, indent=4)
            })
            return {
                "status": "rule_error",
                "error": error_text
            }

        # UNKNOWN ERROR
        else:
            self.create({
                'payment_id': payment.id,
                'status': 'error',
                'error_message': f"Unknown response: {result}",
                'response_message': json.dumps(result, indent=4)
            })
            return {
                "status": "unknown_error",
                "response": result
            }

    def register_receipt_withholding(self, payment):
        """Send payment receipt to MoR API and handle response."""
        withholding_body = self.prepare_withholding_body(payment)
        result = self.env['mor.api.invoice'].mor_api_request(
            "/v1/receipt/withholding", withholding_body)
        status_code = result.get("statusCode")
        message = result.get("message")
        body = result.get("body")

    def prepare_receipt_body(self, payment):
        """
        Prepare the JSON body for the Sales Receipt API from an Odoo payment record.
        `payment` is an `account.payment` record.
        """
        if not payment:
            raise UserError(
                _("Payment record is required to prepare receipt."))
        invoice = payment.move_id or False
        invoice_info = self.env['account.move'].search(
            [('name', '=', payment.memo)], limit=1)

        if not invoice_info:
            raise UserError(
                _("Payment must be linked to at least one invoice."))
        irn = invoice_info.irn if invoice_info else ""
        # Generate unique receipt number (custom logic, e.g., REC + timestamp)

        # Convert to the required format: dd-MM-yyyy'T'HH:mm:ss
        formatted_date = payment.date.strftime("%d-%m-%YT%H:%M:%S")

        receipt_body = {
            "ReceiptNumber": "REC1234567890123465",
            "ReceiptType": "Sales Receipts",
            "Reason": f"Payment for invoice {invoice.name}",
            "ReceiptDate": payment.date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+03:00",
            "ReceiptCounter": 1,
            "ManualReceiptNumber": str(payment.id),
            "SourceSystemType": "POS",  # or dynamically get from config
            "SourceSystemNumber": "3D4865D720",
            "ReceiptCurrency": "ETB",
            "CollectedAmount": payment.amount,
            "SellerTIN":  "0095009268",  # company VAT
            "Invoices": [
                {
                    "InvoiceIRN": irn or "",  # IRN stored in invoice
                    "PaymentCoverage": "FULL" if payment.amount >= invoice.amount_total else "PARTIAL",
                    "InvoicePaidAmount": payment.amount,
                    "DiscountAmount": None,
                    "RemainingAmount": max(invoice.amount_total - payment.amount, 0),
                    "TotalAmount": invoice.amount_total,
                }
            ],
            "TransactionDetails": {
                # map journal to API mode
                "ModeOfPayment": "CASH",
                "ChequeNumber": payment.communication if payment.payment_type == 'transfer' else None,
                "CPONumber": None,

                "CollectorName": payment.partner_id.name,
                "PaymentServiceProvider": payment.journal_id.bank_id.name if payment.journal_id.bank_id else "Bank",
                "OtherPaymentServiceProviderName": None,
                "AccountNumber": payment.journal_id.bank_acc_number if payment.journal_id.bank_acc_number else None,
                "TransactionNumber": payment.name
            }
        }
        return receipt_body

    def prepare_withholding_body(self, payment):
        """
        Prepare the JSON body for the Withholding API from an Odoo payment record.
        `payment` is an `account.payment` record.
        """
        if not payment:
            raise UserError(
                _("Payment record is required to prepare withholding body."))

        # Find linked invoice using memo or move_id
        invoice = payment.move_id or self.env['account.move'].search(
            [('name', '=', payment.memo)], limit=1)

        if not invoice:
            raise UserError(
                _("Payment must be linked to at least one invoice."))

        # Extract IRN if available
        irn = invoice.irn or ""

        # Generate unique receipt number (you can customize logic)
        receipt_number = f"REC{fields.Datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Sample counter and manual number
        receipt_counter = str(payment.id)
        manual_receipt_number = str(payment.name)

        # Compute withholding values
        pretax_amount = invoice.amount_untaxed or 0
        withholding_amount = getattr(invoice, 'withholding_amount', 0) or 0

        # Prepare JSON body
        withholding_body = {
            "ReceiptNumber": receipt_number,
            "Reason": "Withhold for goods purchased",
            "ReceiptCounter": receipt_counter,
            "ManualReceiptNumber": manual_receipt_number,
            "SourceSystemType": "MAN",
            "SourceSystemNumber": "112345678",  # or dynamic from config
            "InvoiceDetail": {
                "InvoiceIRN": irn,
                "Currency": invoice.currency_id.name or "ETB",
                "ExchangeRate": None
            },
            "WithholdDetail": {
                "Type": "TWHT",
                "Rate": None,  # you can add logic if rate is stored somewhere
                "PreTaxAmount": pretax_amount,
                "WithholdingAmount": withholding_amount
            }
        }

        return withholding_body
