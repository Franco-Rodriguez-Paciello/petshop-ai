using System.Net;
using System.Net.Http.Json;
using PetShop.Api.Contracts;

namespace PetShop.Api.Tests;

[CollectionDefinition("api")]
public class ApiCollection : ICollectionFixture<ApiFixture>;

[Collection("api")]
public class ApiTests(ApiFixture api) : IAsyncLifetime
{
    public Task InitializeAsync() => api.ResetAsync();
    public Task DisposeAsync() => Task.CompletedTask;

    [Fact]
    public async Task Catalog_is_seeded_and_searchable()
    {
        var products = await api.CreateClient().GetFromJsonAsync<List<ProductDto>>("/api/products?q=arena&species=gato");
        Assert.NotEmpty(products!);
        Assert.All(products!, p => Assert.Equal("gato", p.Species));
    }

    [Fact]
    public async Task Internal_endpoints_require_key()
    {
        var res = await api.CreateClient().GetAsync("/internal/customers/C-001/orders");
        Assert.Equal(HttpStatusCode.Unauthorized, res.StatusCode);
    }

    [Fact]
    public async Task Customer_only_sees_own_orders()
    {
        var maria = await api.LoginAsync("maria@example.com");
        var orders = await maria.GetFromJsonAsync<List<OrderDto>>("/api/me/orders");
        Assert.Equal([1, 2], orders!.Select(o => o.Id).Order());
    }

    [Fact]
    public async Task Cannot_request_return_of_someone_elses_order()
    {
        var res = await api.InternalClient().PostAsJsonAsync("/internal/customers/C-001/return-requests", new ReturnRequest(4));
        Assert.Equal(HttpStatusCode.NotFound, res.StatusCode);
    }

    [Fact]
    public async Task Return_outside_window_is_rejected()
    {
        var res = await api.InternalClient().PostAsJsonAsync("/internal/customers/C-001/return-requests", new ReturnRequest(2));
        Assert.Equal(HttpStatusCode.Conflict, res.StatusCode);
    }

    [Fact]
    public async Task Return_flow_requires_customer_confirmation()
    {
        var res = await api.InternalClient().PostAsJsonAsync("/internal/customers/C-001/return-requests", new ReturnRequest(1));
        var action = await res.Content.ReadFromJsonAsync<PendingActionDto>();

        // Un servicio interno (el LLM vía MCP) no tiene endpoint para confirmar
        var internalConfirm = await api.InternalClient().PostAsync($"/internal/customers/C-001/pending-actions/{action!.Id}/confirm", null);
        Assert.Equal(HttpStatusCode.NotFound, internalConfirm.StatusCode);

        // Otro cliente no puede confirmarla
        var carlos = await api.LoginAsync("carlos@example.com");
        Assert.Equal(HttpStatusCode.NotFound, (await carlos.PostAsync($"/api/me/pending-actions/{action.Id}/confirm", null)).StatusCode);

        var maria = await api.LoginAsync("maria@example.com");
        Assert.Equal(HttpStatusCode.OK, (await maria.PostAsync($"/api/me/pending-actions/{action.Id}/confirm", null)).StatusCode);
        var orders = await maria.GetFromJsonAsync<List<OrderDto>>("/api/me/orders");
        Assert.Equal("Returned", orders!.Single(o => o.Id == 1).Status);
    }

    [Fact]
    public async Task Appointment_blocks_slot_until_cancelled()
    {
        var when = NextWeekday().ToDateTime(new TimeOnly(10, 0));
        var client = api.InternalClient();
        var first = await client.PostAsJsonAsync("/internal/customers/C-001/appointment-requests", new AppointmentRequest("Luna", "baño", when));
        Assert.Equal(HttpStatusCode.OK, first.StatusCode);
        var second = await client.PostAsJsonAsync("/internal/customers/C-002/appointment-requests", new AppointmentRequest("Rocky", "baño", when));
        Assert.Equal(HttpStatusCode.Conflict, second.StatusCode);

        var action = await first.Content.ReadFromJsonAsync<PendingActionDto>();
        var maria = await api.LoginAsync("maria@example.com");
        await maria.PostAsync($"/api/me/pending-actions/{action!.Id}/cancel", null);
        var retry = await client.PostAsJsonAsync("/internal/customers/C-002/appointment-requests", new AppointmentRequest("Rocky", "baño", when));
        Assert.Equal(HttpStatusCode.OK, retry.StatusCode);
    }

    [Fact]
    public async Task Cannot_book_for_someone_elses_pet()
    {
        var when = NextWeekday().ToDateTime(new TimeOnly(11, 0));
        var res = await api.InternalClient().PostAsJsonAsync("/internal/customers/C-001/appointment-requests", new AppointmentRequest("Rocky", "baño", when));
        Assert.Equal(HttpStatusCode.NotFound, res.StatusCode);
    }

    [Fact]
    public async Task Food_recommendation_for_pet_uses_its_profile()
    {
        var res = await api.InternalClient().PostAsJsonAsync("/internal/customers/C-002/food-recommendations",
            new FoodRecommendationRequest("Rocky", null, null, null, null));
        var rec = await res.Content.ReadFromJsonAsync<FoodRecommendationDto>();
        Assert.Equal("cachorro", rec!.LifeStage);
        Assert.Equal("pequeño", rec.Size);
        Assert.NotEmpty(rec.Products);
        Assert.All(rec.Products, p => Assert.True(p.Stock > 0));
    }

    private static DateOnly NextWeekday()
    {
        var d = DateOnly.FromDateTime(DateTime.Now).AddDays(2);
        return d.DayOfWeek == DayOfWeek.Sunday ? d.AddDays(1) : d;
    }
}
