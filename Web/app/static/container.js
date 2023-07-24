import Overlay from "https://hagbot.de/static/overlay.js";
import { capitalize, pluralize } from "https://hagbot.de/static/helper.js";

export default class OverlayContainer {
    constructor(name, overlayNames, overlayArrays) {
        this.name = name;
        this.overlayNames = overlayNames;
        this.overlayArrays = overlayArrays;
        this.parentContainer = document.getElementsByClassName(pluralize(name) + "-container")[0];
        this.containers = [];
    }

    findHighestIndex() {
        var highestIndex = -1;
        var containers = document.getElementsByClassName(this.name + "-container");

        for (let i = 0; i < containers.length; i++) {
            let container = containers[i];
            let index = parseInt(container.getAttribute("name").split("-")[2]);
            if (index > highestIndex) {
                highestIndex = index;
            }
        }

        return highestIndex;
    }

    createInput(containerText = "") {
        var index = this.findHighestIndex() + 1;
        for (let array of this.overlayArrays) {
            if (!array[index]) {
                array[index] = [];
            }
        }

        var container = document.createElement("div");
        container.classList.add(this.name + "-container");
        container.classList.add("text-field-group");
        container.setAttribute("name", this.name + "-container-" + index);
        this.containers.push(container);

        var text = document.createElement("input");
        text.classList.add(this.name);
        text.classList.add("text-field");
        text.setAttribute("name", this.name + "-" + index);
        text.setAttribute("type", "text");
        text.setAttribute("placeholder", "Question");
        text.value = containerText;
        container.appendChild(text);

        var label = document.createElement("label");
        label.classList.add("text-field-label");
        label.setAttribute("for", this.name + "-" + index);
        label.innerText = capitalize(this.name);
        container.appendChild(label);

        for (let i = 0; i < this.overlayNames.length; i++) {
            let overlayName = this.overlayNames[i];
            let overlayArray = this.overlayArrays[i];
            let overlayButton = document.createElement("button");
            overlayButton.classList.add(pluralize(overlayName) + "-button");
            let numEntries = overlayArray[index].length;
            overlayButton.innerText = numEntries + " " + (numEntries == 1 ? capitalize(overlayName) : capitalize(pluralize(overlayName)));
            overlayButton.addEventListener("click", (function (event) {
                event.preventDefault();
                this.overlay = new Overlay(this, i, index);
                this.overlay.create();
            }).bind(this));
            container.appendChild(overlayButton);
        }

        var deleteButton = document.createElement("button");
        deleteButton.classList.add("delete-button");
        deleteButton.innerText = "Delete";
        deleteButton.addEventListener("click", (function () {
            container.remove();
        }).bind(this));
        container.appendChild(deleteButton);

        var newButton = document.getElementById("new-" + this.name);
        this.parentContainer.insertBefore(container, newButton);
    }

    create() {
        var newButton = document.getElementById("new-" + this.name);
        newButton.addEventListener("click", (function () {
            this.createInput();
        }).bind(this));

        var saveButton = document.getElementsByName(this.name + "-save")[0];
        saveButton.addEventListener("click", (function () {
            for (let i = 0; i < this.overlayNames.length; i++) {
                let overlayName = this.overlayNames[i];
                let overlayArray = this.overlayArrays[i];
                let overlayContainer = document.createElement("div");
                overlayContainer.classList.add(overlayName + "-container");
                overlayContainer.setAttribute("name", overlayName + "-container");

                for (let j = 0; j < overlayArray.length; j++) {
                    for (let k = 0; k < overlayArray[j].length; k++) {
                        let overlay = document.createElement("input");
                        overlay.classList.add(overlayName);
                        overlay.setAttribute("name", overlayName + "-" + j + "-" + k);
                        overlay.setAttribute("type", "hidden");
                        overlay.setAttribute("value", overlayArray[j][k]);
                        overlayContainer.appendChild(overlay);
                    }
                }

                var form = document.getElementsByName(this.name + "-form")[0];
                form.appendChild(overlayContainer);
            }
        }).bind(this));
    }
}