using PetShop.Api.Domain;

namespace PetShop.Api.Tests;

public class ReturnPolicyTests
{
    private static readonly DateOnly Today = new(2026, 6, 15);

    [Fact]
    public void Order_inside_window_is_eligible() =>
        Assert.Null(ReturnPolicy.WhyNotEligible(new Order { CustomerId = "C", CreatedAt = Today.AddDays(-30) }, Today));

    [Fact]
    public void Order_outside_window_is_not_eligible() =>
        Assert.Contains("venció", ReturnPolicy.WhyNotEligible(new Order { CustomerId = "C", CreatedAt = Today.AddDays(-31) }, Today));

    [Fact]
    public void Returned_order_is_not_eligible() =>
        Assert.Contains("ya fue devuelto", ReturnPolicy.WhyNotEligible(
            new Order { CustomerId = "C", CreatedAt = Today, Status = OrderStatus.Returned }, Today));
}

public class FoodRecommenderTests
{
    private static Product Food(string sku, string species, string stage, string size, string desc = "Alimento", int stock = 10, decimal price = 10) =>
        new() { Sku = sku, Name = sku, Brand = "B", Species = species, Category = "alimento", LifeStage = stage, Size = size, Description = desc, Stock = stock, PriceUsd = price };

    [Theory]
    [InlineData("perro", 5, "cachorro")]
    [InlineData("perro", 40, "adulto")]
    [InlineData("perro", 90, "senior")]
    [InlineData("gato", 100, "adulto")]
    [InlineData("gato", 130, "senior")]
    public void Life_stage_by_species_and_age(string species, int months, string expected) =>
        Assert.Equal(expected, FoodRecommender.LifeStageFor(species, months));

    [Theory]
    [InlineData(6, "pequeño")]
    [InlineData(15, "mediano")]
    [InlineData(28, "grande")]
    public void Dog_size_by_weight(decimal kg, string expected) => Assert.Equal(expected, FoodRecommender.SizeFor("perro", kg));

    [Fact]
    public void Recommends_matching_stage_and_size_in_stock_only()
    {
        var catalog = new[]
        {
            Food("ok", "perro", "adulto", "grande"),
            Food("generic", "perro", "adulto", "todos", price: 20),
            Food("puppy", "perro", "cachorro", "grande"),
            Food("small", "perro", "adulto", "pequeño"),
            Food("nostock", "perro", "adulto", "grande", stock: 0),
            Food("cat", "gato", "adulto", "todos"),
        };
        var rec = FoodRecommender.Recommend(new FoodRequest("perro", 40, 28), catalog);
        Assert.Equal(["ok", "generic"], rec.Products.Select(p => p.Sku));
    }

    [Fact]
    public void Special_lines_only_when_requested()
    {
        var catalog = new[]
        {
            Food("normal", "gato", "adulto", "todos"),
            Food("uri", "gato", "adulto", "todos", "pH controlado, línea urinario"),
        };
        Assert.Equal(["normal"], FoodRecommender.Recommend(new FoodRequest("gato", 30, 4), catalog).Products.Select(p => p.Sku));
        Assert.Equal(["uri"], FoodRecommender.Recommend(new FoodRequest("gato", 30, 4, "urinario"), catalog).Products.Select(p => p.Sku));
    }
}

public class AppointmentSchedulerTests
{
    private static readonly DateTime Now = new(2026, 6, 15, 10, 30, 0); // lunes

    [Fact]
    public void Valid_slot() => Assert.Null(AppointmentScheduler.Validate("baño", new DateTime(2026, 6, 16, 11, 0, 0), Now));

    [Theory]
    [InlineData("2026-06-14T11:00:00", "pasado")]
    [InlineData("2026-06-21T11:00:00", "domingo")]
    [InlineData("2026-06-16T08:00:00", "fuera de horario")]
    [InlineData("2026-06-16T11:30:00", "no es hora exacta")]
    [InlineData("2026-08-01T11:00:00", "muy lejos")]
    public void Invalid_slots(string when, string _) =>
        Assert.NotNull(AppointmentScheduler.Validate("baño", DateTime.Parse(when), Now));

    [Fact]
    public void Unknown_service() => Assert.Contains("desconocido", AppointmentScheduler.Validate("spa", Now.AddDays(1), Now));

    [Fact]
    public void Free_slots_exclude_taken_and_past()
    {
        var today = DateOnly.FromDateTime(Now);
        var slots = AppointmentScheduler.FreeSlots(today, [today.ToDateTime(new TimeOnly(12, 0))], Now);
        Assert.Equal([11, 13, 14, 15, 16, 17], slots.Select(s => s.Hour));
    }
}
