using System.Net.Http.Headers;
using System.Net.Http.Json;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.DependencyInjection;
using PetShop.Api.Contracts;
using PetShop.Api.Data;
using Testcontainers.PostgreSql;

namespace PetShop.Api.Tests;

/// <summary>Levanta un Postgres real en Docker y la API completa en memoria (como en producción, sin mocks de EF).</summary>
public class ApiFixture : WebApplicationFactory<Program>, IAsyncLifetime
{
    public const string InternalKey = "test-internal-key";

    private readonly PostgreSqlContainer _db = new PostgreSqlBuilder("postgres:17-alpine").WithDatabase("petshop").Build();

    private static string CatalogPath()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir is not null && !File.Exists(Path.Combine(dir.FullName, "data", "catalog", "products.json")))
            dir = dir.Parent;
        return Path.Combine(dir?.FullName ?? throw new FileNotFoundException("products.json"), "data", "catalog", "products.json");
    }

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.UseSetting("ConnectionStrings:PetShop", _db.GetConnectionString());
        builder.UseSetting("Internal:ApiKey", InternalKey);
        builder.UseSetting("Seed:CatalogPath", CatalogPath());
    }

    public async Task InitializeAsync() => await _db.StartAsync();

    public new async Task DisposeAsync()
    {
        await base.DisposeAsync();
        await _db.DisposeAsync();
    }

    public async Task ResetAsync()
    {
        using var scope = Services.CreateScope();
        await scope.ServiceProvider.GetRequiredService<Seeder>().ResetAsync();
    }

    public async Task<HttpClient> LoginAsync(string email)
    {
        var client = CreateClient();
        var res = await client.PostAsJsonAsync("/api/auth/demo-login", new LoginRequest(email));
        res.EnsureSuccessStatusCode();
        var login = await res.Content.ReadFromJsonAsync<LoginResponse>();
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", login!.Token);
        return client;
    }

    public HttpClient InternalClient()
    {
        var client = CreateClient();
        client.DefaultRequestHeaders.Add("X-Internal-Key", InternalKey);
        return client;
    }
}
