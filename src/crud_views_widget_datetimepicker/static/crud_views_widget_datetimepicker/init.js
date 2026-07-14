(function () {
    "use strict";

    function initPickers(root) {
        $(root).find("input[xdsoft-datetime-config]").each(function () {
            var config = JSON.parse($(this).attr("xdsoft-datetime-config"));
            if (config.lang) {
                jQuery.datetimepicker.setLocale(config.lang);
            }
            $(this).datetimepicker(config);
        });
    }

    $(function () {
        initPickers(document);

        // crud_views modal support: content is injected after document-ready,
        // core fires cv:modal:loaded on #cv-modal after each injection.
        var modal = document.getElementById("cv-modal");
        if (modal) {
            modal.addEventListener("cv:modal:loaded", function () {
                initPickers(modal);
            });
        }
    });
})();
