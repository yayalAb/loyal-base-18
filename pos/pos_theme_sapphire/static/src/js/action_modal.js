import { patch } from "@web/core/utils/patch"
import { ControlButtonsPopup } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons"
import { Component, useState, xml } from "@odoo/owl"
import { _t } from "@web/core/l10n/translation"

patch(ControlButtonsPopup, {
    template: xml`
        <Dialog  
            contentClass="'pos-modal-dialog'" 
            header="false" 
            bodyClass="'d-flex flex-column custom-body'" 
            footer="false" 
            title="'Actions'"
            t-on-click="props.close"
            size="'lg'"
        >
            <ControlButtons showRemainingButtons="true" close="props.close"/>
        </Dialog>
    `,
})
