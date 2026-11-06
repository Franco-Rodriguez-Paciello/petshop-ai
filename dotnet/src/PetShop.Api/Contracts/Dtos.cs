using PetShop.Api.Domain;

namespace PetShop.Api.Contracts;

public record ProductDto(string Sku, string Name, string Brand, string Species, string Category,
    string LifeStage, string Size, decimal PriceUsd, int Stock, string Description)
{
    public static ProductDto From(Product p) =>
        new(p.Sku, p.Name, p.Brand, p.Species, p.Category, p.LifeStage, p.Size, p.PriceUsd, p.Stock, p.Description);
}

public record OrderItemDto(string Sku, string Name, int Quantity, decimal UnitPriceUsd);

public record OrderDto(int Id, DateOnly CreatedAt, string Status, decimal TotalUsd, IReadOnlyList<OrderItemDto> Items)
{
    public static OrderDto From(Order o) => new(o.Id, o.CreatedAt, o.Status.ToString(), o.Total,
        o.Items.Select(i => new OrderItemDto(i.ProductSku, i.Product?.Name ?? i.ProductSku, i.Quantity, i.UnitPriceUsd)).ToList());
}

public record PetDto(int Id, string Name, string Species, string? Breed, int AgeMonths, decimal WeightKg);

public record AppointmentDto(int Id, string PetName, string Service, DateTime StartsAt, string Status);

public record PendingActionDto(int Id, string Type, string Description, DateTime ExpiresAt)
{
    public static PendingActionDto From(PendingAction a) => new(a.Id, a.Type.ToString(), a.Description, a.ExpiresAt);
}

public record FoodRecommendationDto(string LifeStage, string Size, string Rationale, IReadOnlyList<ProductDto> Products);

public record ReturnRequest(int OrderId);

public record AppointmentRequest(string PetName, string Service, DateTime StartsAt);

public record FoodRecommendationRequest(string? PetName, string? Species, int? AgeMonths, decimal? WeightKg, string? Need);

public record LoginRequest(string Email);

public record LoginResponse(string Token, string CustomerId, string Name);

public record ChatRequest(string Message, string? SessionId);

public record ErrorDto(string Error);
