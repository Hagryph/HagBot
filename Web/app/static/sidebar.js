(function () {
    document.addEventListener('DOMContentLoaded', () => {
        const collapseButton = document.querySelector('#collapse-button');
        const collapseButtonSidebar = document.querySelector('#collapse-button-sidebar');
        const sidebarCollapseCheckbox = document.querySelector('.sidebar-collapse-checkbox');

        collapseButton.addEventListener('click', () => {
            sidebarCollapseCheckbox.checked = true;
        });

        collapseButtonSidebar.addEventListener('click', () => {
            sidebarCollapseCheckbox.checked = false;
        });

        document.addEventListener("click", function (event) {
            if (event.target.closest(".sidebar a")) {
                var sectionId = event.target.getAttribute("data-section");
                if (!sectionId) {
                    sectionId = event.target.closest(".sidebar#extension")?.getAttribute("data-section");
                }

                if (sectionId) {
                    document.querySelectorAll(".section").forEach(function (section) {
                        section.style.display = "none";
                    });

                    var sectionElement = document.getElementById(sectionId);
                    if (sectionElement) {
                        sectionElement.style.display = "block";
                    }

                    document.querySelectorAll(".sidebar#extension").forEach(function (extension) {
                        var extensionSectionId = extension.getAttribute("data-section");
                        if (extensionSectionId === sectionId) {
                            extension.style.display = "block";
                        } else {
                            extension.style.display = "none";
                        }
                    });
                } else {
                    document.querySelectorAll(".sidebar#extension").forEach(function (extension) {
                        extension.style.display = "none";
                    });
                }

                var tabLinks = event.target.closest(".sidebar")?.querySelectorAll("a");
                tabLinks?.forEach(function (link) {
                    link.classList.remove("active");
                });

                event.target.classList.add("active");
            }  
        });
    });
})();