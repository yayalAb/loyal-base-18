/** @odoo-module */
import { registry } from "@web/core/registry"
import { useRef } from "@odoo/owl"
import { useService } from "@web/core/utils/hooks"
import { _t } from "@web/core/l10n/translation"
const { Component, onWillStart, useState } = owl
import { PharmacyOrderLines } from "./pharmacy_orderlines"
var currency = 0
var quantity = 0
var amount = 0
var sub_t = 0
var sub_total = 0
var product_lst = []
var uom_lst = []
var invoice = 0
var invoice_id = 0
var tax = 0
export class PharmacyDashboard extends Component {
    //Initialize Pharmacy Dashboard
    setup() {
        super.setup(...arguments)
        this.ref = useRef("root")
        this.vaccine_div = useRef("vaccine_div")
        this.medicine_div = useRef("medicine_div")
        this.home_content = useRef("home_content")
        this.patient_name = useRef("PatientName")
        this.patient_email = useRef("Email")
        this.patient_search = useRef("PatientSearch")
        this.orders_div = useRef("orders_div")
        this.orm = useService("orm")
        // this.user = useService("user");
        this.actionService = useService("action")
        this.state = useState({
            product_lst: [],
            medicines: [],
            units: [],
            sub_total,
            vaccine: [],
            order_data: [],
            order_line: [],
            menu: "home",
        })
        this.fetch_product()
        onWillStart(async () => {
            this.state.med = await this.orm.call(
                "product.template",
                "action_get_medicine_data",
                []
            )
        })
    }
    //  Fetch product details
    async fetch_product() {
        const domain = [["medicine_ok", "=", true]]
        const result = await this.orm.call("product.template", "search_read", [
            domain,
        ])
        this.state.product_lst = result
        this.create_order()
    }
    //  Method for creating sale order
    async create_order() {
        this.vaccine_div?.el?.classList.add("d-none")
        this.medicine_div?.el?.classList.add("d-none")
        this.home_content?.el?.classList.remove("d-none")
        this.orders_div?.el?.classList.add("d-none")

        // Call company_currency and update text content
        const result = await this.orm.call(
            "hospital.pharmacy",
            "company_currency"
        )

        const symbolEl1 = document.getElementById("symbol" + currency)
        const symbolEl2 = document.getElementById("symbol")

        if (symbolEl1) symbolEl1.textContent = result || ""
        if (symbolEl2) symbolEl2.textContent = result || ""

        this.state.medicines = await this.product_lst
        this.state.units = await this.uom_lst
    }
    // To update the orderline of sale order
    updateOrderLine(line, id) {
        const orderline = this.state.order_line.filter(
            orderline => orderline.id === id
        )[0]
        orderline.product = line.product
        orderline.qty = parseInt(line.qty)
        orderline.uom = line.uom
        orderline.price = line.price
        orderline.sub_total = line.sub_total
    }
    //  To add new row in the sale order line
    addRow() {
        const data = [
            ...this.state.order_line,
            owl.reactive({
                id: new Date(),
                product: false,
                qty: 1,
                uom: 0,
                price: 0,
                sub_total: 0,
            }),
        ]
        this.state.order_line = data
    }
    // To remove the line if not needed
    removeLine(id) {
        const filteredData = this.state.order_line.filter(line => line.id != id)
        this.state.order_line = filteredData
    }
    //  Create sale order
    async create_sale_order() {
        const data = {
            name: document.getElementById("patient-name")?.value || "",
            phone: document.getElementById("patient-phone")?.value || "",
            email: document.getElementById("patient-mail")?.value || "",
            dob: document.getElementById("patient-dob")?.value || "",
            products: this.state.order_line,
        }

        // Validate quantity
        let hasInvalidQuantity = this.state.order_line.some(
            line => line.quantity < 1
        )
        if (hasInvalidQuantity) {
            alert("Medicine quantity must be greater than or equal to 1.")
            return
        }

        // Validate required fields
        if (!data.name.trim()) {
            alert("Please enter the Name")
            return
        }
        if (!data.email.trim()) {
            alert("Please enter the Email")
            return
        }

        try {
            const result = await this.orm.call(
                "hospital.pharmacy",
                "create_sale_order",
                [data]
            )
            alert(
                "The sale order has been created with reference number " +
                    result.invoice
            )
            window.location.reload()
        } catch (error) {
            console.error("Error creating sale order:", error)
            alert(
                "An error occurred while creating the sale order. Please try again."
            )
        }
    }

    //  Fetch patient data
    async fetch_patient_data() {
        try {
            const result = await this.orm.call(
                "res.partner",
                "action_get_patient_data",
                [[this.patient_search.el.value]]
            )

            // Helper for text fields
            const setText = (id, text = "") => {
                const el = document.getElementById(id)
                if (el) el.textContent = text
            }

            setText("patient-title", result.name || "")
            setText("patient-code", result.unique || "")
            setText("patient-age", result.dob || "")
            setText("patient-blood", result.blood_group || "")
            setText("patient-gender", result.gender || "")

            // Handle image
            const imgEl = document.getElementById("patient-image")
            if (imgEl) {
                if (result.name === "Patient Not Found") {
                    imgEl.src =
                        "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png"
                    const histHead = document.getElementById("hist_head")
                    if (histHead) histHead.innerHTML = ""
                } else if (result.image_1920) {
                    imgEl.src = "data:image/png;base64," + result.image_1920
                }
            }
        } catch (error) {
            console.error("Error fetching patient data:", error)
            alert("Failed to load patient data. Please try again.")
        }
    }

    //  Fetch medicine data while clicking Medicine button
    async fetch_medicine_data() {
        this.vaccine_div?.el?.classList.add("d-none")
        this.home_content?.el?.classList.add("d-none")
        this.medicine_div?.el?.classList.remove("d-none")
        this.orders_div?.el?.classList.add("d-none")
    }
    //  Fetch vaccine data
    async fetch_vaccine_data() {
        this.vaccine_div?.el?.classList.remove("d-none")
        this.home_content?.el?.classList.add("d-none")
        this.medicine_div?.el?.classList.add("d-none")
        this.orders_div?.el?.classList.add("d-none")
        this.state.vaccine = await this.orm.call(
            "product.template",
            "action_get_vaccine_data",
            []
        )
    }
    //  Method fo fetching all sale orders
    async fetch_sale_orders() {
        this.vaccine_div?.el?.classList.add("d-none")
        this.home_content?.el?.classList.add("d-none")
        this.medicine_div?.el?.classList.add("d-none")
        this.orders_div?.el?.classList.remove("d-none")
        this.state.order_data = await this.orm.call(
            "sale.order",
            "search_read",
            [
                [
                    [
                        "partner_id.patient_seq",
                        "not in",
                        ["New", "Employee", "User"],
                    ],
                ],
                ["name", "create_date", "partner_id", "amount_total", "state"],
            ]
        )
    }
    //  Method for emptying the data
    async clear_data() {
        this.patient_search.el.value = ""

        // Replace jQuery html("") → native DOM
        const setHTML = (id, html = "") => {
            const el = document.getElementById(id)
            if (el) el.innerHTML = html
        }

        setHTML("hist_head")
        setHTML("patient-title")
        setHTML("patient-code")
        setHTML("patient-gender")
        setHTML("patient-blood")

        // Replace jQuery attr() → native setAttribute()
        const imgEl = document.getElementById("patient-image")
        if (imgEl) {
            imgEl.setAttribute(
                "src",
                "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png"
            )
        }
    }
}
PharmacyDashboard.template = "PharmacyDashboard"
registry.category("actions").add("pharmacy_dashboard_tags", PharmacyDashboard)
PharmacyDashboard.components = { PharmacyOrderLines }
