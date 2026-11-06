using System.Text.Json;
using Microsoft.EntityFrameworkCore;
using PetShop.Api.Domain;

namespace PetShop.Api.Data;

/// <summary>
/// Datos de demo con fechas RELATIVAS a hoy, para que las demos y las evals den siempre el mismo resultado.
/// </summary>
public class Seeder(PetShopDbContext db, IConfiguration config, TimeProvider clock, ILogger<Seeder> logger)
{
    private static readonly JsonSerializerOptions JsonOptions = new() { PropertyNameCaseInsensitive = true };

    public async Task ResetAsync(CancellationToken ct = default)
    {
        await db.Database.EnsureDeletedAsync(ct);
        await SeedIfEmptyAsync(ct);
    }

    public async Task SeedIfEmptyAsync(CancellationToken ct = default)
    {
        await db.Database.EnsureCreatedAsync(ct);
        if (await db.Products.AnyAsync(ct)) return;

        var path = config["Seed:CatalogPath"] ?? "../../../data/catalog/products.json";
        await using var stream = File.OpenRead(path);
        var products = await JsonSerializer.DeserializeAsync<List<Product>>(stream, JsonOptions, ct) ?? [];
        db.Products.AddRange(products);

        var today = DateOnly.FromDateTime(clock.GetLocalNow().DateTime);
        var maria = new Customer
        {
            Id = "C-001", Name = "María Gómez", Email = "maria@example.com",
            Pets =
            [
                new Pet { CustomerId = "C-001", Name = "Luna", Species = "perro", Breed = "Labrador", BirthDate = today.AddMonths(-40), WeightKg = 28 },
                new Pet { CustomerId = "C-001", Name = "Michi", Species = "gato", Breed = "Común europeo", BirthDate = today.AddMonths(-130), WeightKg = 4.5m },
            ],
        };
        var carlos = new Customer
        {
            Id = "C-002", Name = "Carlos Ruiz", Email = "carlos@example.com",
            Pets = [new Pet { CustomerId = "C-002", Name = "Rocky", Species = "perro", Breed = "Beagle", BirthDate = today.AddMonths(-5), WeightKg = 6 }],
        };
        var ana = new Customer
        {
            Id = "C-003", Name = "Ana Torres", Email = "ana@example.com",
            Pets = [new Pet { CustomerId = "C-003", Name = "Kiwi", Species = "ave", Breed = "Periquito", BirthDate = today.AddMonths(-18), WeightKg = 0.04m }],
        };
        db.Customers.AddRange(maria, carlos, ana);

        Order NewOrder(string customer, int daysAgo, OrderStatus status, params (string Sku, int Qty)[] items) => new()
        {
            CustomerId = customer,
            CreatedAt = today.AddDays(-daysAgo),
            Status = status,
            Items = items.Select(i => new OrderItem
            {
                ProductSku = i.Sku, Quantity = i.Qty,
                UnitPriceUsd = products.First(p => p.Sku == i.Sku).PriceUsd,
            }).ToList(),
        };

        // Los IDs (1..5) los usan los tests y el golden set de evals
        db.Orders.AddRange(
            NewOrder("C-001", 10, OrderStatus.Completed, ("JU-101", 1)),               // 1: elegible
            NewOrder("C-001", 45, OrderStatus.Completed, ("AL-101", 1), ("SN-101", 2)), // 2: fuera de ventana
            NewOrder("C-002", 10, OrderStatus.Returned, ("AC-101", 1)),                 // 3: ya devuelto
            NewOrder("C-002", 5, OrderStatus.Completed, ("SN-104", 3)),                 // 4: elegible, de Carlos
            NewOrder("C-003", 2, OrderStatus.Completed, ("AL-171", 1)));                // 5: elegible, de Ana

        await db.SaveChangesAsync(ct);
        logger.LogInformation("Seed completo: {Count} productos", products.Count);
    }
}
