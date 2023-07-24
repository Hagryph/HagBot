import { capitalize, pluralize } from "https://hagbot.de/static/helper.js";

export default class Overlay {
    constructor(container, index, containerNumber) {
        this.name = container.overlayNames[index];
        this.index = containerNumber;
        this.overlayArray = container.overlayArrays[index];
        this.parentContainer = container.containers[containerNumber];
    }

    findHighestIndex() {
        var containers = document.getElementsByClassName(this.overlayName + "-container");
        var highestIndex = -1;

        for (var i = 0; i < containers.length; i++) {
            var index = parseInt(containers[i].getElementsByClassName(overlayName)[0].getAttribute("name").split("-")[2]);
            if (index > highestIndex) {
                highestIndex = index;
            }
        }

        return highestIndex;
    }

    createInput(text = "") {
        var overlayContainer = document.createElement("div");
        overlayContainer.classList.add("text-field-group");
        overlayContainer.classList.add(this.name + "-container");

        var overlayText = document.createElement("input");
        overlayText.classList.add(this.name);
        overlayText.classList.add("text-field");
        var index = this.findHighestIndex() + 1;
        overlayText.setAttribute("name", this.name + "-" + this.index + "-" + index);
        overlayText.setAttribute("type", "text");
        overlayText.setAttribute("placeholder", capitalize(this.name));
        overlayText.value = text;
        overlayContainer.appendChild(overlayText);

        var overlayLabel = document.createElement("label");
        overlayLabel.classList.add("text-field-label");
        overlayLabel.setAttribute("for", this.name + "-" + this.index + "-" + index);
        overlayLabel.innerText = capitalize(this.name);
        overlayContainer.appendChild(overlayLabel);

        var deleteButton = document.createElement("button");
        deleteButton.classList.add("delete-button");
        deleteButton.innerText = "Delete";
        deleteButton.addEventListener("click", function () {
            overlayContainer.parentElement.removeChild(overlayContainer);
        });
        overlayContainer.appendChild(deleteButton);

        this.overlay.insertBefore(overlayContainer, this.overlay.getElementsByClassName("save-button")[0]);
    }

    create() {
        this.overlay = document.createElement("div");
        this.overlay.classList.add("overlay");
        this.overlay.setAttribute("name", this.name);

        var saveButton = document.createElement("button");
        saveButton.classList.add("save-button");
        saveButton.innerText = "Save";
        saveButton.addEventListener("click", (function (event) {
            event.preventDefault();

            var childContainers = document.getElementsByClassName(this.name + "-container");
            var numChilds = 0;
            this.overlayArray[this.index] = [];

            for (var i = 0; i < childContainers.length; i++) {
                var childContainer = childContainers[i];
                var childText = childContainer.getElementsByClassName(this.name)[0]?.value;
                if (childText.value != "" && childText != undefined) {
                    this.overlayArray[this.index].push(childText);
                    ++numChilds;
                }
            }

            var parentButton = this.parentContainer.getElementsByClassName(pluralize(this.name) + "-button")[0];
            parentButton.innerText = numChilds + " " + (numChilds == 1 ? capitalize(this.name) : capitalize(pluralize(this.name)));
            this.parentContainer.removeChild(this.overlay);
        }).bind(this));
        this.overlay.appendChild(saveButton);

        var cancelButton = document.createElement("button");
        cancelButton.classList.add("cancel-button");
        cancelButton.innerText = "Cancel";
        cancelButton.addEventListener("click", (function () {
            this.parentContainer.removeChild(this.overlay);
        }).bind(this));
        this.overlay.appendChild(cancelButton);

        var newButton = document.createElement("button");
        newButton.classList.add("new-button");
        newButton.innerText = "New " + capitalize(this.name);
        newButton.addEventListener("click", (function (event) {
            event.preventDefault();
            this.createInput();
        }).bind(this));
        this.overlay.appendChild(newButton);

        this.parentContainer.appendChild(this.overlay);

        if (this.overlayArray[this.index] != undefined) {
            for (let i = 0; i < this.overlayArray[this.index].length; i++) {
                this.createInput(this.overlayArray[this.index][i]);
            }
        }
    }
}