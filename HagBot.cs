using TwitchLib.Client;
using TwitchLib.Client.Models;
using TwitchLib.Client.Events;
using TwitchLib.Communication.Clients;
using TwitchLib.Communication.Models;
using Newtonsoft.Json;
using System.Text.RegularExpressions;
using static System.DateTime;

namespace HagBot
{
    internal partial class HagBot
    {
        private readonly TwitchClient client;
        private readonly long userID;
        private static readonly List<long> userIDs = new();
        private List<List<object>> faq = new();
        private List<List<object>> commands = new();

        public static void Main(string[] _)
        {
            while (true)
            {
                ConnectBots();
                Thread.Sleep(300000);
            }
        }

        private static void ConnectBots()
        {
            List<long> userIDs = Database.GetUsersAsync().Result;
            foreach (long userID in userIDs)
            {
                if (HagBot.userIDs.Contains(userID)) continue;
                Console.WriteLine($"Connecting {userID}");
                var bot = new HagBot(userID);
                bot.Run();
            }
        }

        private HagBot(long userID)
        {
            this.userID = userID;

            string? username = Database.GetUsernameAsync(userID).Result;
            string? oauth = Database.GetOAuthAsync(userID).Result;
            if (username is null || oauth is null) throw new("Username or OAuth is null");

            userIDs.Add(userID);

            var clientOptions = new ClientOptions
            {
                MessagesAllowedInPeriod = 100,
                ThrottlingPeriod = TimeSpan.FromSeconds(30)
            };
            WebSocketClient customClient = new(clientOptions);
            client = new TwitchClient(customClient);
            ConnectionCredentials credentials = new("HagBot", oauth);
            client.Initialize(credentials, username);
        }

        private void Run()
        {
            LoadInfos();

            client.OnMessageReceived += OnMessageReceived;
            client.OnIncorrectLogin += OnIncorrectLogin;
            client.OnConnected += (sender, e) => Console.WriteLine($"Connected! {userID}");
            client.OnDisconnected += (sender, e) => Console.WriteLine($"Disconnected! {userID}");
            client.OnError += (sender, e) => Console.WriteLine($"Error! {userID}");
            client.OnConnectionError += (sender, e) => Console.WriteLine($"Connection error! {userID}");
            client.OnFailureToReceiveJoinConfirmation += (sender, e) => Console.WriteLine($"Failure to receive join confirmation! {userID}");

            client.Connect();
        }

        private static bool CompareMessage(string compareTo, string message)
        {
            // remove line breaks and tabs
            compareTo = compareTo.Replace("\r", "");
            compareTo = compareTo.Replace("\n", "");
            compareTo = compareTo.Replace("\t", "");
            message = message.Replace("\r", "");
            message = message.Replace("\n", "");
            message = message.Replace("\t", "");

            // remove all non-alphanumeric characters
            compareTo = RemoveNonAlphaNumeric().Replace(compareTo, "");
            message = RemoveNonAlphaNumeric().Replace(message, "");

            // remove all whitespace
            compareTo = compareTo.Replace(" ", "");
            message = message.Replace(" ", "");

            // check if both messages are equal
            if (compareTo.Equals(message, StringComparison.OrdinalIgnoreCase))
                return true;

            // check if the message contains any writing mistakes
            double mistakes = 0;
            int maxMistakes = Math.Min(3, (int)Math.Round((double)message.Length / 4));
            int i, j;
            j = 0;
            for (i = 0; i < message.Length && j < compareTo.Length; i++, j++)
            {
                if (message[i] != compareTo[j])
                {
                    if (i + 1 < message.Length && message[i + 1] == compareTo[j])
                        ++i;

                    if (j + 1 < compareTo.Length && message[i] == compareTo[j + 1])
                        ++j;

                    // check if the message contains too many mistakes
                    if (++mistakes > maxMistakes)
                        return false;
                }
            }

            // check i and j to see if they are at the end of the message, if not, add mistakes
            while (i++ < message.Length)
                ++mistakes;

            while (j++ < compareTo.Length)
                ++mistakes;

            // if the message contains less or equal than max mistakes, count it as correct
            if (mistakes <= maxMistakes)
                return true;

            return false;
        }

        private async void CheckFAQ(ChatMessage message)
        {
            foreach (List<object> faqEntry in faq)
            {
                if (CompareMessage((string)faqEntry[0], message.Message))
                {
                    List<string> answers = (List<string>)faqEntry[1];
                    Random random = new();
                    int index = random.Next(0, answers.Count);
                    string answer = answers[index];
                    client.SendMessage(message.Channel, answer);
                    _ = await Database.InsertChatMessageAsync(userID, "HagBot", answer, Now);
                    break;
                }
            }
        }

        private async void CheckCommand(ChatMessage message)
        {
            foreach (List<object> command in commands)
            {
                string commandName = (string)command[0];
                List<string> aliases = (List<string>)command[1];
                List<string> triggers = aliases.Append(commandName).ToList();
                foreach (string trigger in triggers)
                {
                    if (message.Message == trigger)
                    {
                        List<string> answers = (List<string>)command[2];
                        Random random = new();
                        int index = random.Next(0, answers.Count);
                        string answer = answers[index];
                        client.SendMessage(message.Channel, answer);
                        _ = await Database.InsertChatMessageAsync(userID, "HagBot", answer, Now);
                        break;
                    }
                }
            }
        }

        private async void OnMessageReceived(object? sender, OnMessageReceivedArgs e)
        {
            DateTime time = Now;
            Console.WriteLine($"{time} - {e.ChatMessage.Username}: {e.ChatMessage.Message}");
            await Database.InsertChatMessageAsync(userID, e.ChatMessage.Username, e.ChatMessage.Message, time);

            CheckFAQ(e.ChatMessage);
            CheckCommand(e.ChatMessage);
        }

        private void OnIncorrectLogin(object? sender, OnIncorrectLoginArgs e)
        {
            Console.WriteLine($"Incorrect login! {userID}");
            string? refreshToken = Database.GetRefreshTokenAsync(userID).Result;
            if (refreshToken is null) return;
            string? newOAuth = RefreshAccessToken(refreshToken);
            if (newOAuth is null) return;
            _ = Database.UpdateOAuthAsync(userID, newOAuth);

            client.Disconnect();
            userIDs.Remove(userID);
            var Bot = new HagBot(userID);
            Bot.Run();
        }

        private async void LoadInfos()
        {
            while (true)
            {
                faq = await Database.GetFAQAsync(userID);
                commands = await Database.GetCommandsAsync(userID);
                await Task.Delay(300000);
            }
        }

        private static string? RefreshAccessToken(string refreshToken)
        {
            string? clientID = null;
            string? clientSecret = null;
            try
            {
                using StreamReader file = File.OpenText("credentials.json");
                JsonSerializer serializer = new();
                dynamic? credentials = serializer.Deserialize(file, typeof(object));
                clientID = credentials?.client_id;
                clientSecret = credentials?.client_secret;
            }
            catch (Exception e)
            {
                Console.WriteLine(e.Message);
            }

            if (clientID is null || clientSecret is null) throw new("Can't read config properly");

            var data = new Dictionary<string, string>
            {
                { "client_id", clientID },
                { "client_secret", clientSecret },
                { "refresh_token", refreshToken },
                { "grant_type", "refresh_token" }
            };

            try
            {
                using HttpClient client = new();
                HttpResponseMessage response = client.PostAsync("https://id.twitch.tv/oauth2/token", new FormUrlEncodedContent(data)).Result;
                string tokenResponse = response.Content.ReadAsStringAsync().Result;
                dynamic? token = JsonConvert.DeserializeObject(tokenResponse);

                if (token is null || token.access_token is null)
                {
                    throw new Exception($"Failed to refresh access token: {token?.status} {token?.message}");
                }

                return token?.access_token;
            }
            catch (Exception e)
            {
                Console.WriteLine(e.Message);
                return null;
            }
        }

        [GeneratedRegex("[^a-zA-Z0-9]")]
        private static partial Regex RemoveNonAlphaNumeric();
    }
}