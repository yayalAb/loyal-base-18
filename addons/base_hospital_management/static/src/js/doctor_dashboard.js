/** @odoo-module */
import { registry } from "@web/core/registry"
import { useService } from "@web/core/utils/hooks"
import { useRef } from "@odoo/owl"
import { Component, useState } from "@odoo/owl"
import { _t } from "@web/core/l10n/translation"

// Doctor dashboard component initialization
export class DoctorDashboard extends Component {
    setup() {
        super.setup(...arguments)
        this.ref = useRef("root")
        this.orm = useService("orm")
        // Removed useService('user') as it is not available in Odoo 18
        // this.session = useService("session") // Use 'session' service to get user info if needed
        this.actionService = useService("action")
        this.welcome = useRef("welcome")
        this.state = useState({
            patients: [],
            search_button: false,
            patients_search: [],
        })
    }

    // Function for fetching patient data
    async list_patient_data() {
        this.actionService.doAction({
            name: _t("Patient details"),
            type: "ir.actions.act_window",
            res_model: "res.partner",
            view_mode: "list,form",
            views: [
                [false, "list"],
                [false, "form"],
            ],
            domain: [["patient_seq", "not in", ["New", "Employee", "User"]]],
        })

        const patients = await this.orm.call(
            "res.partner",
            "fetch_patient_data",
            []
        )

        // Replace jQuery references with DOM API or OWL refs (assuming you have a method for this)
        const activeElement = document.querySelector(".n_active")
        if (activeElement) {
            activeElement.classList.remove("n_active")
        }
        const patientDataElement = document.querySelector(".patient_data")
        if (patientDataElement) {
            patientDataElement.classList.add("n_active")
        }

        this.state.patients = patients // Set state so UI can react properly
    }

    // Method for generating list of inpatients
    action_list_inpatient() {
        this.actionService.doAction({
            name: _t("Inpatient details"),
            type: "ir.actions.act_window",
            res_model: "hospital.inpatient",
            view_mode: "list,form",
            views: [
                [false, "list"],
                [false, "form"],
            ],
        })
    }

    // Fetch surgery details
    fetch_doctors_schedule() {
        this.actionService.doAction({
            name: _t("Surgery details"),
            type: "ir.actions.act_window",
            res_model: "inpatient.surgery",
            view_mode: "list,form",
            views: [
                [false, "list"],
                [false, "form"],
            ],
        })
    }

    // Fetch outpatient details
    fetch_consultation() {
        this.actionService.doAction({
            name: _t("Outpatient Details"),
            type: "ir.actions.act_window",
            res_model: "hospital.outpatient",
            view_mode: "list,form",
            views: [[false, "list"]],
        })
    }

    // Fetch allocation details
    fetch_allocation_lines() {
        this.actionService.doAction({
            name: _t("Doctor Allocation"),
            type: "ir.actions.act_window",
            res_model: "doctor.allocation",
            view_mode: "list,form",
            views: [
                [false, "list"],
                [false, "form"],
            ],
        })
    }
}

DoctorDashboard.template = "DoctorDashboard"
registry.category("actions").add("doctor_dashboard_tags", DoctorDashboard)
