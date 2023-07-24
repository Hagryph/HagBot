import OverlayContainer from "https://hagbot.de/static/container.js";

(function () {
    document.addEventListener("DOMContentLoaded", function () {
        var answers = [];
        var container = new OverlayContainer("question", ["answer"], [answers]);
        container.create();

        var xhr = new XMLHttpRequest();
        xhr.open("GET", "/data/answers", true);

        xhr.onload = function () {
            if (xhr.status === 200) {
                var loaded_answers = JSON.parse(xhr.responseText);
                for (var i = 0; i < loaded_answers.length; i++) {
                    var answer = loaded_answers[i];
                    var questionID = answer["question_id"];
                    var answerText = answer["answer"];

                    if (answers[questionID] == undefined) {
                        answers[questionID] = [];
                    }

                    answers[questionID].push(answerText);
                }

                var xhr_questions = new XMLHttpRequest();
                xhr_questions.open("GET", "/data/questions", true);

                xhr_questions.addEventListener("load", function () {
                    var questions = JSON.parse(xhr_questions.responseText);

                    for (let question of questions) {
                        container.createInput(question["question"]);
                    }
                });
                xhr_questions.send();
            }
        };
        xhr.send();
    });
})()