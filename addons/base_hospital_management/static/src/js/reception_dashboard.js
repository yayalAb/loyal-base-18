/** @odoo-module */
import { registry } from "@web/core/registry"
import { useService } from "@web/core/utils/hooks"
import { Component, onMounted, useState, useRef } from "@odoo/owl"
import { _t } from "@web/core/l10n/translation"

class ReceptionDashBoard extends Component {
    setup() {
        this.ref = useRef("root")
        this.patient_creation = useRef("patient_creation")
        this.inpatient = useRef("inpatient")
        this.out_patient = useRef("out-patient")
        this.rd_buttons = useRef("rd_buttons")
        this.room_ward = useRef("room_ward")
        this.ward = useRef("ward")
        this.room = useRef("room")
        this.action = useService("action")
        this.orm = useService("orm")
        this.state = useState({
            patient_lst: [],
            ward_data: [],
            room_data: [],
        })
        onMounted(async () => {
            await this.createPatient()
        })
    }
    //  Method for creating patient
    createPatient() {
        // Remove active class from any previously active element
        const active = document.querySelector(".r_active")
        if (active) active.classList.remove("r_active")

        // Add 'r_active' class to the patient button
        const patientButton = document.querySelector(".o_patient_button")
        if (patientButton) patientButton.classList.add("r_active")

        // Toggle visibility using classList
        this.room_ward.el.classList.add("d-none")
        this.patient_creation.el.classList.remove("d-none")
        this.out_patient.el.classList.add("d-none")
        this.inpatient.el.classList.add("d-none")
        this.rd_buttons.el.classList.add("d-none")
        this.ward.el.classList.add("d-none")
        this.room.el.classList.add("d-none")
    }

    //  Method for creating patient
    async savePatient() {
        var data = await this.fetch_patient_data()
        if (data["name"] == "" || data["phone"] == "") {
            alert("Please fill the name and phone")
            return
        }
        await this.orm
            .call("res.partner", "create", [[data]])
            .then(function () {
                alert("the patient record has been created")
                window.location.reload()
            })
    }
    //  Method which returns the details of a patient given in the form
    fetch_patient_data() {
        var patient_name = $("#patient-name").val()
        var patient_img = $("#patient-img").data("file")
        var patient_phone = $("#patient-phone").val()
        var patient_mail = $("#patient-mail").val()
        var patient_dob = $("#patient-dob").val()
        var patient_bloodgroup = $("#patient-bloodgroup").val()
        var patient_m_status = $("#patient-m-status").val() || ""
        var patient_rhtype = $("input[name='rhtype']:checked").val()
        var patient_gender = $("input[name='gender']:checked").val()
        var data = {
            name: patient_name,
            blood_group: patient_bloodgroup,
            rh_type: patient_rhtype,
            gender: patient_gender,
            marital_status: patient_m_status,
            phone: patient_phone,
            email: patient_mail,
            image_1920: patient_img,
        }
        if (patient_dob) {
            data["date_of_birth"] = patient_dob
        }
        return data
    }
    //  Method on clicking  appointment button
    fetchAppointmentData() {
        // Remove existing 'r_active' if present
        const active = document.querySelector(".r_active")
        if (active) active.classList.remove("r_active")

        // Add 'r_active' to the appointment button
        const appointmentButton = document.querySelector(
            ".o_appointment_button"
        )
        if (appointmentButton) appointmentButton.classList.add("r_active")

        // Toggle sections visibility
        this.room_ward.el.classList.add("d-none")
        this.patient_creation.el.classList.add("d-none")
        this.out_patient.el.classList.remove("d-none")
        this.inpatient.el.classList.add("d-none")
        this.rd_buttons.el.classList.remove("d-none")
        this.ward.el.classList.add("d-none")
        this.room.el.classList.add("d-none")

        // Show outpatient creation page by default
        this.createOutPatient()
    }

    //  Creates new outpatient
    async createOutPatient() {
        const date = new Date()
        const formattedCurrentDate = date.toISOString().split("T")[0]

        // Fetch patient data
        const result = await this.orm.call(
            "res.partner",
            "fetch_patient_data",
            []
        )
        this.state.patient_lst = result

        // Populate patient select dropdown
        const patientSelect = document.querySelector(".select_patient")
        if (patientSelect) {
            // Clear existing options
            patientSelect.innerHTML = '<option value=""></option>'
            result.forEach(element => {
                const option = document.createElement("option")
                option.value = element.id
                option.textContent = `${element.patient_seq}-${element.name}`
                patientSelect.appendChild(option)
            })
        }

        // Fetch doctor allocation data
        const doctorResult = await this.orm.call(
            "doctor.allocation",
            "search_read",
            []
        )
        this.dr_lst = doctorResult

        // Populate doctor dropdown
        const doctorSelect = document.querySelector(".select_dr")
        if (doctorSelect) {
            doctorSelect.innerHTML = ""
            doctorResult.forEach(element => {
                const option = document.createElement("option")
                option.value = element.id
                option.textContent = element.display_name
                doctorSelect.appendChild(option)
            })
        }

        // Clear the #controls element content (if exists)
        const controls = document.getElementById("controls")
        if (controls) {
            controls.innerHTML = ""
        }

        // Set current date for outpatient date field
        const opDateInput = document.getElementById("op_date")
        if (opDateInput) {
            opDateInput.value = formattedCurrentDate
        }
    }

    //  Method for creating inpatient
    async createInPatient() {
        // Hide and show relevant sections
        this.room_ward.el.classList.add("d-none")
        this.patient_creation.el.classList.add("d-none")
        this.out_patient.el.classList.add("d-none")
        this.inpatient.el.classList.remove("d-none")
        this.ward.el.classList.add("d-none")
        this.room.el.classList.add("d-none")

        const domain = [["job_id.name", "=", "Doctor"]]

        // --- Fetch patient list ---
        const patientResult = await this.orm.call(
            "res.partner",
            "fetch_patient_data",
            []
        )
        this.patient_id_lst = patientResult

        const patientSelect = document.querySelector(".select_patient_id")
        if (patientSelect) {
            patientSelect.innerHTML = ""
            patientResult.forEach(element => {
                const option = document.createElement("option")
                option.value = element.id
                option.textContent = `${element.patient_seq}-${element.name}`
                patientSelect.appendChild(option)
            })
        }

        // --- Fetch attending doctor list ---
        const doctorResult = await this.orm.call("hr.employee", "search_read", [
            domain,
        ])
        this.attending_dr_lst = doctorResult

        const doctorSelect = document.querySelector(".attending_doctor_id")
        if (doctorSelect) {
            doctorSelect.innerHTML = ""
            doctorResult.forEach(element => {
                const option = document.createElement("option")
                option.value = element.id
                option.textContent = element.display_name
                doctorSelect.appendChild(option)
            })
        }
    }

    //  Method for saving outpatient
    async save_out_patient_data() {
        var self = this
        var data = await self.fetch_out_patient_data()
        if (data != false) {
            var result = await this.orm.call("res.partner", "create_patient", [
                data,
            ])
            alert("the outpatient is created")
            $("#o_patient-name").val("")
            $("#sl_patient").val("")
            $("#o_patient-phone").val("")
            $("#o_patient-dob").val("")
        }
    }

    //  Method for displaying patient card
    patient_card() {
        if ($("#select_type").val() === "dont_have_card") {
            $("#sl_patient").hide()
            $("#patient_label").hide()
        } else {
            $("#sl_patient").show()
            $("#patient_label").show()
        }
    }

    //  Method for fetching OP details
    async fetch_op_details() {
        var patient_id = $("#sl_patient").val()
        var phone = $("#o_patient-phone").val()
        var data = {
            patient_data: patient_id,
            "patient-phone": phone,
        }
        return data
    }

    //  Method for fetching patient details
    async fetch_patient_id() {
        const data = await this.fetch_op_details()

        const result = await this.orm.call(
            "res.partner",
            "reception_op_barcode",
            [data]
        )

        const nameInput = document.querySelector("#o_patient-name")
        const dobInput = document.querySelector("#o_patient-dob")
        const bloodGroupInput = document.querySelector("#o_patient_bloodgroup")
        const genderInput = document.querySelector("#o_patient-gender")
        const phoneInput = document.querySelector("#o_patient-phone")

        if (nameInput) nameInput.value = result.name || ""
        if (dobInput) dobInput.value = result.date_of_birth || ""
        if (bloodGroupInput) bloodGroupInput.value = result.blood_group || ""
        if (genderInput) genderInput.value = result.gender || ""
        if (phoneInput && result.phone) phoneInput.value = result.phone
    }

    //  Method for fetching outpatient data
    async fetch_out_patient_data() {
        const getValue = selector => {
            const el = document.querySelector(selector)
            return el ? el.value : ""
        }

        // For checked radio buttons or checkboxes:
        const getCheckedValue = selector => {
            const el = document.querySelector(selector)
            return el ? el.value : ""
        }

        const o_patient_name = getValue("#o_patient-name")
        const o_patient_phone = getValue("#o_patient-phone")
        const o_patient_dob = getValue("#o_patient-dob")
        const o_patient_blood_group = getValue("#o_patient_bloodgroup")
        const o_patient_rhtype = getCheckedValue("input[id='o_rhtype']:checked")
        const o_patient_gender = getCheckedValue(
            "input[id='o_patient-gender']:checked"
        )
        const patient_id = getValue("#sl_patient")
        const op_date = getValue("#op_date")
        const reason = getValue("#reason")
        const ticket_no = getValue("#slot")
        const doctor = getValue("#sl_dr")

        if (o_patient_name === "" || doctor === "" || op_date === "") {
            alert("Please fill out all the required fields.")
            return false // Prevent form submission
        }

        const data = {
            op_name: o_patient_name,
            op_phone: o_patient_phone,
            op_blood_group: o_patient_blood_group,
            op_rh: o_patient_rhtype,
            op_gender: o_patient_gender,
            patient_id: patient_id,
            date: op_date,
            reason: reason,
            slot: 0.0,
            doctor: doctor,
        }

        if (o_patient_dob) {
            data.op_dob = o_patient_dob
        }

        return data
    }

    //  Method for fetching inpatient data
    async fetch_in_patient_data() {
        const getValue = selector => {
            const el = document.querySelector(selector)
            return el ? el.value : null
        }

        const patient_id = getValue("#sl_patient_id")
        const reason_of_admission = getValue("#reason_of_admission")
        const admission_type = getValue("#admission_type")
        const attending_doctor_id = getValue("#attending_doctor_id")

        if (
            patient_id === null ||
            attending_doctor_id === null ||
            admission_type === null
        ) {
            alert("Please fill out all the required fields.")
            return false // Prevent form submission
        }

        const data = {
            patient_id: patient_id,
            reason_of_admission: reason_of_admission,
            admission_type: admission_type,
            attending_doctor_id: attending_doctor_id,
        }
        return data
    }

    //  Method for creating new inpatient
    async save_in_patient_data() {
        var data = await this.fetch_in_patient_data()
        if (data != false || data != null || data != undefined) {
            this.orm
                .call("hospital.inpatient", "create_new_in_patient", [
                    null,
                    data,
                ])
                .then(function () {
                    alert("Inpatient is created")
                    $("#sl_patient_id").val("")
                    $("#reason_of_admission").val("")
                    $("#admission_type").val("")
                    $("#attending_doctor_id").val("")
                })
        }
    }
    //  Method for getting room or ward details
    fetchRoomWard() {
        const viewSecondary = document.querySelector("#view_secondary")
        if (viewSecondary) {
            viewSecondary.innerHTML = ""
        }

        this.room_ward.el.classList.remove("d-none")
        this.patient_creation.el.classList.add("d-none")
        this.out_patient.el.classList.add("d-none")
        this.inpatient.el.classList.add("d-none")
        this.rd_buttons.el.classList.add("d-none")

        const activeElement = document.querySelector(".r_active")
        if (activeElement) {
            activeElement.classList.remove("r_active")
        }

        const roomWardButton = document.querySelector(".o_room_ward_button")
        if (roomWardButton) {
            roomWardButton.classList.add("r_active")
        }
    }

    //  Method for getting ward details
    async fetchWard() {
        this.ward.el.classList.remove("d-none")
        this.room.el.classList.add("d-none")

        const activeElement = document.querySelector(".r_active2")
        if (activeElement) {
            activeElement.classList.remove("r_active2")
        }

        const wardButton = document.querySelector(".o_ward_button")
        if (wardButton) {
            wardButton.classList.add("r_active2")
        }

        const result = await this.orm.call("hospital.ward", "search_read")
        this.state.ward_data = result
    }

    //  Method for getting room details
    async fetchRoom() {
        this.room.el.classList.remove("d-none")
        this.ward.el.classList.add("d-none")

        const activeElement = document.querySelector(".r_active2")
        if (activeElement) {
            activeElement.classList.remove("r_active2")
        }

        const roomButton = document.querySelector(".o_room_button")
        if (roomButton) {
            roomButton.classList.add("r_active2")
        }

        const result = await this.orm.call("patient.room", "search_read")
        this.state.room_data = result
    }
}
ReceptionDashBoard.template = "ReceptionDashboard"
registry.category("actions").add("reception_dashboard_tags", ReceptionDashBoard)
