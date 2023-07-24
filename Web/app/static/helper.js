export function capitalize(string) {
    var splittedStrings = string.split(" ");
    for (var i = 0; i < splittedStrings.length; i++) {
        splittedStrings[i] = splittedStrings[i].charAt(0).toUpperCase() + splittedStrings[i].slice(1);
    }

    return splittedStrings.join(" ");
}

export function pluralize(string) {
    return string + (string.endsWith("y") ? "ies" : (string.endsWith("s") ? "es" : "s"));
}