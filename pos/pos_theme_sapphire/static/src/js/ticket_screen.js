import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen"
import { useService } from "@web/core/utils/hooks"
import { _t } from "@web/core/l10n/translation"
import { patch } from "@web/core/utils/patch"
import { ProxyStatus } from "@point_of_sale/app/navbar/proxy_status/proxy_status"
import { ClosePosPopup } from "@point_of_sale/app/navbar/closing_popup/closing_popup"
import { SaleDetailsButton } from "@point_of_sale/app/navbar/sale_details_button/sale_details_button"
import { CashMovePopup } from "@point_of_sale/app/navbar/cash_move_popup/cash_move_popup"
import { BackButton } from "@point_of_sale/app/screens/product_screen/action_pad/back_button/back_button"
import { CashierName } from "@point_of_sale/app/navbar/cashier_name/cashier_name"
import { OrderTabs } from "@point_of_sale/app/components/order_tabs/order_tabs"
import { isBarcodeScannerSupported } from "@web/core/barcode/barcode_video_scanner"
import { ControlButtonsPopup } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons"
import { SelectPartnerButton } from "@point_of_sale/app/screens/product_screen/control_buttons/select_partner_button/select_partner_button"
import { OrderWidget } from "@point_of_sale/app/generic_components/order_widget/order_widget"
import {
    isDisplayStandalone,
    isMobileOS,
} from "@web/core/browser/feature_detection"

TicketScreen.components = {
    ...TicketScreen.components,
    ProxyStatus,
    SaleDetailsButton,
    BackButton,
    CashierName,
    OrderWidget,
    OrderTabs,
    isBarcodeScannerSupported,
    SelectPartnerButton,
}

patch(TicketScreen.prototype, {
    setup() {
        super.setup(...arguments)
        this.hardwareProxy = useService("hardware_proxy")
        this.selectedCategoryId = null
        this.isDisplayStandalone = isDisplayStandalone()
    },
    async onClickMore() {
        // You can show the same ControlButtons popup from POS
        this.dialog.add(ControlButtonsPopup, {
            close: () => this.dialog.close(),
        })
    },
    setSelectedCategory(categoryId) {
        this.selectedCategoryId = categoryId
        this.pos.setSelectedCategory(categoryId)
        this.render() // manually trigger re-render
    },
    async closeSession() {
        const info = await this.pos.getClosePosInfo()
        this.dialog.add(ClosePosPopup, info)
    },
    get appUrl() {
        return `/scoped_app?app_id=point_of_sale&app_name=${encodeURIComponent(
            this.pos.config.display_name
        )}&path=${encodeURIComponent(`pos/ui?config_id=${this.pos.config.id}`)}`
    },
    onCashMoveButtonClick() {
        this.hardwareProxy.openCashbox(_t("Cash in / out"))
        this.dialog.add(CashMovePopup)
    },
    get orderCount() {
        return this.pos.get_open_orders().length
    },

    async clickLogout() {
        window.location.href = "/web/session/logout"
    },

    async onTicketButtonClick() {
        if (this.isTicketScreenShown) {
            this.pos.closeScreen()
        } else {
            if (this._shouldLoadOrders()) {
                try {
                    this.pos.setLoadingOrderState(true)
                    const message = await this.pos._syncAllOrdersFromServer()
                    if (message) {
                        this.notification.add(message, 5000)
                    }
                } finally {
                    this.pos.setLoadingOrderState(false)
                    this.pos.showScreen("TicketScreen")
                }
            } else {
                this.pos.showScreen("TicketScreen")
            }
        }
    },
    async clearCache() {
        await this.pos.data.resetIndexedDB()
        const items = { ...localStorage }
        for (const key in items) {
            localStorage.removeItem(key)
        }
        window.location.reload()
    },

    _shouldLoadOrders() {
        return this.pos.config.trusted_config_ids.length > 0
    },
    showBackButton() {
        return this.pos.showBackButton() && this.ui.isSmall
    },
    getOrderTabs() {
        return this.pos.get_open_orders().filter(order => !order.table_id)
    },
    get orderCount() {
        return this.pos.get_open_orders().length
    },
    _shouldLoadOrders() {
        return this.pos.config.trusted_config_ids.length > 0
    },
    goToHomeButton() {
        this.pos.showScreen("ProductScreen")
    },
})
