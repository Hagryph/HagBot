import OverlayContainer from "https://hagbot.de/static/container.js";

(function () {
    document.addEventListener("DOMContentLoaded", function () {
        var responses = [];
        var aliases = [];
        var container = new OverlayContainer("command", ["response", "alias"], [responses, aliases]);
        container.create();

        var xhr = new XMLHttpRequest();
        xhr.open("GET", "/data/responses", true);

        xhr.onload = function () {
            if (xhr.status === 200) {
                var loaded_responses = JSON.parse(xhr.responseText);
                for (var i = 0; i < loaded_responses.length; i++) {
                    var response = loaded_responses[i];
                    var commandID = response["command_id"];
                    var responseText = response["response"];

                    if (responses[commandID] == undefined) {
                        responses[commandID] = [];
                    }

                    responses[commandID].push(responseText);
                }

                var xhr_aliases = new XMLHttpRequest();
                xhr_aliases.open("GET", "/data/aliases", true);

                xhr_aliases.addEventListener("load", function () {
                    var loaded_aliases = JSON.parse(xhr_aliases.responseText);

                    for (var i = 0; i < loaded_aliases.length; i++) {
                        var alias = loaded_aliases[i];
                        var commandID = alias["command_id"];
                        var aliasText = alias["alias"];

                        if (aliases[commandID] == undefined) {
                            aliases[commandID] = [];
                        }

                        aliases[commandID].push(aliasText);
                    }

                    var xhr_commands = new XMLHttpRequest();
                    xhr_commands.open("GET", "/data/commands", true);

                    xhr_commands.addEventListener("load", function () {
                        var commands = JSON.parse(xhr_commands.responseText);

                        for (var i = 0; i < commands.length; i++) {
                            container.createInput(commands[i]["command"]);
                        }
                    });
                    xhr_commands.send();
                });
                xhr_aliases.send();
            }
        };
        xhr.send();
    });
})();