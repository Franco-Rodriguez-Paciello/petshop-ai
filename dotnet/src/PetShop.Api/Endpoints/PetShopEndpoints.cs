using System.Security.Claims;
using Microsoft.AspNetCore.Mvc;
using PetShop.Api.Contracts;
using PetShop.Api.Data;
using PetShop.Api.Services;

namespace PetShop.Api.Endpoints;

public static class PetShopEndpoints
{
    private static IResult ToResult<T>(this Outcome<T> o) =>
        o.Ok ? Results.Ok(o.Value) : Results.Json(new ErrorDto(o.Error!), statusCode: o.StatusCode);

    public static void MapPetShopEndpoints(this IEndpointRouteBuilder app)
    {
        var catalog = app.MapGroup("/api/products").WithTags("Catálogo");
        catalog.MapGet("/", (PetShopService svc, string? q, string? species, string? category, int? take) =>
            svc.SearchProductsAsync(q, species, category, take ?? 10));
        catalog.MapGet("/{sku}", async (string sku, PetShopService svc) => (await svc.GetProductAsync(sku)).ToResult());

        // Cliente final autenticado con JWT
        var me = app.MapGroup("/api/me").RequireAuthorization().WithTags("Cliente");
        MapCustomerRoutes(me, ctx => ctx.User.CustomerId());

        // Servicios internos (MCP server, AI service): clave compartida + cliente que ya autenticó la API
        var internalApi = app.MapGroup("/internal").AddEndpointFilter<Auth.InternalKeyFilter>().WithTags("Interno");
        internalApi.MapGet("/products", (PetShopService svc, string? q, string? species, string? category, int? take) =>
            svc.SearchProductsAsync(q, species, category, take ?? 10));
        internalApi.MapGet("/products/{sku}", async (string sku, PetShopService svc) => (await svc.GetProductAsync(sku)).ToResult());
        internalApi.MapGet("/availability", async (PetShopService svc, string service, DateOnly day) =>
            (await svc.GetAvailabilityAsync(service, day)).ToResult());
        internalApi.MapGet("/customers/{customerId}", async (string customerId, PetShopService svc) =>
            await svc.FindCustomerAsync(customerId) is { } c ? Results.Ok(new { c.Id, c.Name }) : Results.NotFound());

        var customer = internalApi.MapGroup("/customers/{customerId}");
        MapCustomerRoutes(customer, ctx => (string)ctx.Request.RouteValues["customerId"]!);

        internalApi.MapPost("/admin/reset-demo", async (Seeder seeder, IConfiguration config) =>
        {
            if (!config.GetValue<bool>("Demo:AllowReset")) return Results.NotFound();
            await seeder.ResetAsync();
            return Results.Ok(new { reset = true });
        });
    }

    private static void MapCustomerRoutes(RouteGroupBuilder g, Func<HttpContext, string> customerId)
    {
        g.MapGet("/orders", (HttpContext ctx, PetShopService svc) => svc.GetOrdersAsync(customerId(ctx)));
        g.MapGet("/pets", (HttpContext ctx, PetShopService svc) => svc.GetPetsAsync(customerId(ctx)));
        g.MapGet("/appointments", (HttpContext ctx, PetShopService svc) => svc.GetAppointmentsAsync(customerId(ctx)));
        g.MapGet("/pending-actions", (HttpContext ctx, PetShopService svc) => svc.GetPendingActionsAsync(customerId(ctx)));

        g.MapPost("/return-requests", async (HttpContext ctx, ReturnRequest req, PetShopService svc) =>
            (await svc.RequestReturnAsync(customerId(ctx), req.OrderId)).ToResult());
        g.MapPost("/appointment-requests", async (HttpContext ctx, AppointmentRequest req, PetShopService svc) =>
            (await svc.RequestAppointmentAsync(customerId(ctx), req)).ToResult());
        g.MapPost("/food-recommendations", async (HttpContext ctx, FoodRecommendationRequest req, PetShopService svc) =>
            (await svc.RecommendFoodAsync(customerId(ctx), req)).ToResult());
    }

    /// <summary>Confirmar/cancelar solo existe para el cliente con JWT: ningún servicio interno (ni el LLM) puede.</summary>
    public static void MapConfirmationEndpoints(this IEndpointRouteBuilder app)
    {
        var g = app.MapGroup("/api/me/pending-actions").RequireAuthorization().WithTags("Cliente");
        g.MapPost("/{id:int}/confirm", async (int id, ClaimsPrincipal user, PetShopService svc) =>
            (await svc.ConfirmAsync(user.CustomerId(), id)).ToResult());
        g.MapPost("/{id:int}/cancel", async (int id, ClaimsPrincipal user, PetShopService svc) =>
            (await svc.CancelAsync(user.CustomerId(), id)).ToResult());
    }

    public static void MapChatEndpoint(this IEndpointRouteBuilder app)
    {
        app.MapPost("/api/chat", async ([FromBody] ChatRequest req, ClaimsPrincipal user, AiServiceClient ai, PetShopService svc, CancellationToken ct) =>
        {
            var reply = await ai.ChatAsync(user.CustomerId(), req, ct);
            var pending = await svc.GetPendingActionsAsync(user.CustomerId());
            return Results.Ok(new { reply.SessionId, reply.Reply, reply.Sources, PendingActions = pending });
        }).RequireAuthorization().WithTags("Chat");
    }
}
