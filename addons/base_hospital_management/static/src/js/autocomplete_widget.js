odoo.define("base_hospital_management.autocomplete_widget", function (require) {
    "use strict"

    var AbstractField = require("web.AbstractField")
    var fieldRegistry = require("web.field_registry")

    var AutoCompleteWidget = AbstractField.extend({
        template: "AutoCompleteWidget",
        events: {
            "input .auto_complete_input": "_onInput",
            "focusin .auto_complete_input": "_onFocus",
            "blur .auto_complete_input": "_onBlur",
            "click .suggestion_item": "_onSuggestionClick",
        },

        init: function (parent, state, params) {
            this._super.apply(this, arguments)
            this.suggestions = []
            this.suggestionVisible = false
        },

        _render: function () {
            this._super.apply(this, arguments)
            var self = this
            this.$input = this.$(".auto_complete_input")
            this.$suggestionList = this.$(".suggestion_list")

            // Set initial value
            if (this.value) {
                this.$input.val(this.value)
            }
        },

        _onInput: function (ev) {
            var value = ev.target.value
            this._setValue(value)

            if (value && value.length >= 2) {
                this._fetchSuggestions(value)
            } else {
                this._hideSuggestions()
            }
        },

        _onFocus: function () {
            var value = this.$input.val()
            if (value && value.length >= 2) {
                this._fetchSuggestions(value)
            }
        },

        _onBlur: function () {
            var self = this
            setTimeout(function () {
                self._hideSuggestions()
            }, 200)
        },

        _onSuggestionClick: function (ev) {
            var value = $(ev.currentTarget).text()
            this.$input.val(value)
            this._setValue(value)
            this._hideSuggestions()
        },

        _fetchSuggestions: function (searchTerm) {
            var self = this
            this._rpc({
                model: "prescription.line",
                method: "get_medication_suggestions",
                args: [searchTerm],
            }).then(function (suggestions) {
                self.suggestions = suggestions
                if (suggestions.length > 0) {
                    self._showSuggestions(suggestions)
                } else {
                    self._hideSuggestions()
                }
            })
        },

        _showSuggestions: function (suggestions) {
            var self = this
            this.$suggestionList.empty()

            suggestions.forEach(function (suggestion) {
                var $li = $('<li class="suggestion_item"></li>').text(
                    suggestion
                )
                self.$suggestionList.append($li)
            })

            this.$suggestionList.show()
            this.suggestionVisible = true
        },

        _hideSuggestions: function () {
            this.$suggestionList.hide()
            this.suggestionVisible = false
        },

        _setValue: function (value) {
            this._setValue(value)
        },
    })

    fieldRegistry.add("medication_autocomplete", AutoCompleteWidget)
    return AutoCompleteWidget
})
