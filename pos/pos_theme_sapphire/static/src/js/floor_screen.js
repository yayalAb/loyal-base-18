/** @odoo-module **/
import { FloorScreen } from "@pos_restaurant/app/floor_screen/floor_screen"
import { useService } from "@web/core/utils/hooks"
import { _t } from "@web/core/l10n/translation"
import { patch } from "@web/core/utils/patch"
import { useState } from "@odoo/owl"
import { ProxyStatus } from "@point_of_sale/app/navbar/proxy_status/proxy_status"
import { ClosePosPopup } from "@point_of_sale/app/navbar/closing_popup/closing_popup"
import { SaleDetailsButton } from "@point_of_sale/app/navbar/sale_details_button/sale_details_button"
import { CashMovePopup } from "@point_of_sale/app/navbar/cash_move_popup/cash_move_popup"
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen"
import { BackButton } from "@point_of_sale/app/screens/product_screen/action_pad/back_button/back_button"
import { CashierName } from "@point_of_sale/app/navbar/cashier_name/cashier_name"
import { usePos } from "@point_of_sale/app/store/pos_hook"
import { useTime } from "@point_of_sale/app/utils/time_hook"
import { OrderTabs } from "@point_of_sale/app/components/order_tabs/order_tabs"
import { isBarcodeScannerSupported } from "@web/core/barcode/barcode_video_scanner"
import { ControlButtonsPopup } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons"
import { SelectPartnerButton } from "@point_of_sale/app/screens/product_screen/control_buttons/select_partner_button/select_partner_button"
import {
    isDisplayStandalone,
    isMobileOS,
} from "@web/core/browser/feature_detection"
FloorScreen.components = {
    ...FloorScreen.components,
    ProxyStatus,
    SaleDetailsButton,
    BackButton,
    CashierName,
    usePos,
    useTime,
    OrderTabs,
    isBarcodeScannerSupported,
    SelectPartnerButton,
}

patch(FloorScreen.prototype, {
    setup() {
        super.setup(...arguments)
        this.hardwareProxy = useService("hardware_proxy")
        this.selectedCategoryId = null
        this.pos = usePos()
        this.time = useTime()
        this.isDisplayStandalone = isDisplayStandalone()
    },
    async onClickMore() {
        // You can show the same ControlButtons popup from POS
        this.dialog.add(ControlButtonsPopup, {
            close: () => this.dialog.close(),
        })

        // OR run custom logic:
        // this.notification.add("Action button clicked!", { type: "success" });
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

    onClickScan() {
        if (!this.pos.scanning) {
            this.pos.showScreen("FloorScreen")
            this.pos.mobile_pane = "right"
        }
        this.pos.scanning = !this.pos.scanning
    },
    async onClickTableTab() {
        await this.pos.syncAllOrders()
        this.dialog.add(TableSelector, {
            title: _t("Table Selector"),
            placeholder: _t("Enter a table number"),
            buttons: getButtons([
                EMPTY,
                ZERO,
                { ...BACKSPACE, class: "o_colorlist_item_color_transparent_1" },
            ]),
            confirmButtonLabel: _t("Jump"),
            getPayload: async table_number => {
                const find_table = t =>
                    t.table_number === parseInt(table_number)
                const table =
                    this.pos.currentFloor?.table_ids.find(find_table) ||
                    this.pos.models["restaurant.table"].find(find_table)
                if (table) {
                    return this.pos.setTableFromUi(table)
                }
                const floating_order = this.pos
                    .get_open_orders()
                    .find(o => o.getFloatingOrderName() === table_number)
                if (floating_order) {
                    return this.setFloatingOrder(floating_order)
                }
                if (!table && !floating_order) {
                    this.pos.selectedTable = null
                    const newOrder = this.pos.add_new_order()
                    newOrder.floating_order_name = table_number
                    newOrder.setBooked(true)
                    return this.setFloatingOrder(newOrder)
                }
            },
        })
    },
    onClickPlanButton() {
        this.pos.showScreen("FloorScreen", { floor: this.floor })
    },
    goToHomeButton() {
        this.pos.showScreen("ProductScreen")
    },
})
