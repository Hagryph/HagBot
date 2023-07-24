(function () {
    document.addEventListener("DOMContentLoaded", function () {
        var tableSections = document.querySelectorAll(".table-section");
        for (var i = 1; i < tableSections.length; i++) {
            tableSections[i].style.display = "none";
        }

        document.addEventListener("click", function (event) {
            if (event.target.closest(".tab-nav a")) {
                var tabId = event.target.getAttribute("data-table-id");
                var tableSections = document.querySelectorAll(".table-section");
                for (var i = 0; i < tableSections.length; i++) {
                    tableSections[i].style.display = "none";
                }
                document.getElementById("table-" + tabId).style.display = "block";
            }
        });
    });
})();