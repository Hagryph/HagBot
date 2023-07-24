using Newtonsoft.Json;

public class Client
{
    private readonly HttpClient client;

    public Client()
    {
        client = new HttpClient();
    }

    public async Task<string> ExecuteAsync(string function, params object?[] args)
    {
        string json = JsonConvert.SerializeObject(args);
        string url = "http://127.0.0.1:8002/execute/" + function + "?args=" + System.Web.HttpUtility.UrlEncode(json);
        HttpResponseMessage response = await client.GetAsync(url);
        string responseBody = await response.Content.ReadAsStringAsync();
        return responseBody[1..^1].Replace("\\\"", "\"");
    }
}