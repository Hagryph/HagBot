(function () {
    document.addEventListener('DOMContentLoaded', function () {
        var chatLog = document.getElementsByClassName('chat-log-container')[0];
        var existingChatLog = [];

        function appendMessage(message) {
            var time = message['time'];
            if (time != null) {
                var year = time.slice(0, 4);
                var month = time.slice(5, 7);
                var day = time.slice(8, 10);
                var hour = time.slice(11, 13);
                var minute = time.slice(14, 16);
                var second = time.slice(17, 19);

                var utcDate = new Date(Date.UTC(year, month - 1, day, hour, minute, second));
                time = utcDate.toLocaleTimeString();
            }

            var user = message['user'];

            var message = message['message'];
            message = message.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');

            var timeElement = document.createElement('span');
            timeElement.classList.add('time');
            timeElement.innerText = time;

            var userElement = document.createElement('span');
            userElement.classList.add('user');
            userElement.innerText = user + ":";

            var messageElement = document.createElement('span');
            messageElement.classList.add('message');
            messageElement.innerHTML = message;

            var messageContainer = document.createElement('div');
            messageContainer.classList.add('chat-message');
            if (user === 'HagBot') {
                messageContainer.classList.add('hagbot');
            }
            messageContainer.appendChild(timeElement);
            messageContainer.appendChild(userElement);
            messageContainer.appendChild(messageElement);

            chatLog.appendChild(messageContainer);
        }

        function updateChatLog() {
            var xhr = new XMLHttpRequest();
            xhr.open('GET', 'data/chat_log', true);

            xhr.onload = function () {
                if (xhr.status === 200) {
                    var newChatLog = JSON.parse(xhr.responseText);

                    var i = 0;
                    var newLength = newChatLog.length;
                    var existingLength = existingChatLog.length;

                    if (newLength > existingLength) {
                        var scrolledDown = false;
                        var lastMessage = chatLog.lastChild;
                        try {
                            var lastMessageBottom = lastMessage.getBoundingClientRect().bottom;
                            var chatLogBottom = chatLog.parentNode.getBoundingClientRect().bottom;
                            if (lastMessageBottom <= chatLogBottom) {
                                scrolledDown = true;
                            }
                        } catch (e) { }
                    }
                    for (i = existingLength; i < newLength; i++) {
                        appendMessage(newChatLog[i]);
                    }

                    if (scrolledDown) {
                        chatLog.parentNode.scrollTop = chatLog.parentNode.scrollHeight;
                    }
                }
                existingChatLog = newChatLog;
            };

            xhr.send();
        };

        updateChatLog();

        var scrollInterval = setInterval(function () {
            if (chatLog.parentNode.parentNode.style.display === 'block') {
                chatLog.parentNode.scrollTop = chatLog.parentNode.scrollHeight;
                clearInterval(scrollInterval);
            }
        }, 10)

        setInterval(function () {
            if (chatLog.parentNode.parentNode.style.display === 'block') {
                updateChatLog();
            }
        }, 2000);
    });
})();