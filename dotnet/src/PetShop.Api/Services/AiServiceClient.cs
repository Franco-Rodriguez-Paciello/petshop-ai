using System.Text.Json.Serialization;
using PetShop.Api.Contracts;
using PetShop.Api.Endpoints;

namespace PetShop.Api.Services;

public record AiChatReply(
    [property: JsonPropertyName("session_id")] string SessionId,
    [property: JsonPropertyName("respuesta")] string Reply,
    [property: JsonPropertyName("fuentes")] IReadOnlyList<string>? Sources);

/// <summary>Cliente tipado hacia el servicio de IA en Python. La API es quien autentica y le dice quién es el cliente.</summary>
public class AiServiceClient(HttpClient http, IConfiguration config)
{
    public async Task<AiChatReply> ChatAsync(string customerId, ChatRequest req, CancellationToken ct)
    {
        using var msg = new HttpRequestMessage(HttpMethod.Post, "/chat")
        {
            Content = JsonContent.Create(new { mensaje = req.Message, session_id = req.SessionId }),
        };
        msg.Headers.Add(Auth.InternalKeyHeader, config["Internal:ApiKey"]);
        msg.Headers.Add("X-Cliente-Id", customerId);

        using var res = await http.SendAsync(msg, ct);
        res.EnsureSuccessStatusCode();
        return (await res.Content.ReadFromJsonAsync<AiChatReply>(ct))!;
    }
}
