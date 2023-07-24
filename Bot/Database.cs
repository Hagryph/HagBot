using UserIDsConverter;
using UsernameConverter;
using AccessTokenConverter;
using RefreshTokenConverter;
using UpdateOAuthTokenConverter;
using FAQConverter;
using AnswersConverter;
using InsertChatMessageConverter;
using CommandsConverter;
using AliasesConverter;
using ResponsesConverter;

namespace HagBot
{
    internal static class Database
    {
        private static readonly Client client = new();

        private static async Task<string> ExecuteAsync(string function, params object[] args) => await client.ExecuteAsync(function, args);

        internal static async Task<string?> GetOAuthAsync(long userID)
        {
            string result = await ExecuteAsync("select", "accounts", new[] { "access_token" }, new[] { "id" }, new[] { userID });
            return AccessToken.FromJson(result).First().AccessTokenClassArray.First().AccessToken;
        }

        internal static async Task<string?> GetRefreshTokenAsync(long userID)
        {
            string result = await ExecuteAsync("select", "accounts", new[] { "refresh_token" }, new[] { "id" }, new[] { userID });
            return RefreshToken.FromJson(result).First().RefreshTokenClassArray.First().RefreshToken;
        }

        internal static async Task<string?> GetUsernameAsync(long userID)
        {
            string result = await ExecuteAsync("select", "accounts", new[] { "username" }, new[] { "id" }, new[] { userID });
            return Username.FromJson(result).First().UsernameClassArray.First().Username;
        }

        internal static async Task<List<long>> GetUsersAsync()
        {
            string result = await ExecuteAsync("select", "accounts", new[] { "id" });
            return UserIDs.FromJson(result).First().UserIdClassArray.Select(x => x.Id).ToList();
        }

        internal static async Task<List<List<object>>> GetFAQAsync(long userID)
        {
            List<List<object>> faq = new();
            string result = await ExecuteAsync("select", "faq", new[] { "question", "id" }, new[] { "account_id" }, new[] { userID });
            var questions = Faq.FromJson(result).First().FaqClassArray;


            foreach (var question in questions)
            {
                string questionText = question.Question;
                long id = question.Id;

                List<string> answersList = new();
                result = await ExecuteAsync("select", "faq_answers", new[] { "answer" }, new[] { "account_id", "question_id" }, new long[] { userID, id });
                var answers = Answers.FromJson(result).First().AnswerClassArray;

                foreach (var answer in answers)
                {
                    string answerText = answer.Answer;
                    answersList.Add(answerText);
                }

                faq.Add(new List<object> { questionText, answersList });
            }

            return faq;
        }

        internal static async Task<List<List<object>>> GetCommandsAsync(long userID)
        {
            List<List<object>> commands = new();
            string result = await ExecuteAsync("select", "commands", new[] { "id", "command" }, new[] { "account_id" }, new[] { userID });
            var commandsList = Commands.FromJson(result).First().CommandClassArray;

            foreach (var command in commandsList)
            {
                long id = command.Id;
                string commandText = command.Command;

                List<string> responsesList = new();
                result = await ExecuteAsync("select", "responses", new[] { "response" }, new[] { "account_id", "command_id" }, new long[] { userID, id });
                var responses = Responses.FromJson(result).First().ResponseClassArray;

                foreach (var response in responses)
                {
                    string responseText = response.Response;
                    responsesList.Add(responseText);
                }

                List<string> aliasList = new();
                result = await ExecuteAsync("select", "aliases", new[] { "alias" }, new[] { "account_id", "command_id" }, new long[] { userID, id });
                var aliases = Aliases.FromJson(result).First().AliasClassArray;

                foreach (var alias in aliases)
                {
                    string aliasText = alias.Alias;
                    aliasList.Add(aliasText);
                }

                commands.Add(new List<object> { commandText, aliasList, responsesList });
            }

            return commands;
        }

        internal static async Task<bool> UpdateOAuthAsync(long userID, string accessToken)
        {
            string result = await ExecuteAsync("update", "accounts", new[] { "id", "access_token" }, new object[] { userID, accessToken });
            return UpdateOAuthToken.FromJson(result)[0].Bool ?? false;
        }

        internal static async Task<bool> InsertChatMessageAsync(long userID, string user, string message, DateTime time)
        {
            string result = await ExecuteAsync("update", "chat_logs", new[] { "account_id", "user", "message", "time" }, new object[] { userID, user, message, time });
            return InsertChatMessage.FromJson(result)[1] ?? false;
        }
    }
}
