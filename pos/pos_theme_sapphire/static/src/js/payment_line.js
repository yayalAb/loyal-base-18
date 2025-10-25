import { PaymentScreenPaymentLines } from "@point_of_sale/app/screens/payment_screen/payment_lines/payment_lines"
import { _t } from "@web/core/l10n/translation"
import { patch } from "@web/core/utils/patch"

PaymentScreenPaymentLines.components = {
    ...PaymentScreenPaymentLines.components,
}

patch(PaymentScreenPaymentLines.prototype, {
    setup() {
        super.setup(...arguments)
    },

    paymentMethodImage(id) {
        if (this.paymentMethod.image) {
            return `/web/image/pos.payment.method/${id}/image`
        } else if (this.paymentMethod.type === "cash") {
            return "/point_of_sale/static/src/img/money.png"
        } else if (this.paymentMethod.type === "pay_later") {
            return "/point_of_sale/static/src/img/pay-later.png"
        } else {
            return "/point_of_sale/static/src/img/card-bank.png"
        }
    },
})
