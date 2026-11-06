namespace PetShop.Api.Domain;

public class Product
{
    public required string Sku { get; set; }
    public required string Name { get; set; }
    public required string Brand { get; set; }
    public required string Species { get; set; }
    public required string Category { get; set; }
    public required string LifeStage { get; set; }
    public required string Size { get; set; }
    public decimal PriceUsd { get; set; }
    public int Stock { get; set; }
    public required string Description { get; set; }
}

public class Customer
{
    public required string Id { get; set; }
    public required string Name { get; set; }
    public required string Email { get; set; }
    public List<Pet> Pets { get; set; } = [];
}

public class Pet
{
    public int Id { get; set; }
    public required string CustomerId { get; set; }
    public required string Name { get; set; }
    public required string Species { get; set; }
    public string? Breed { get; set; }
    public DateOnly BirthDate { get; set; }
    public decimal WeightKg { get; set; }
}

public enum OrderStatus { Completed, Returned }

public class Order
{
    public int Id { get; set; }
    public required string CustomerId { get; set; }
    public DateOnly CreatedAt { get; set; }
    public OrderStatus Status { get; set; } = OrderStatus.Completed;
    public List<OrderItem> Items { get; set; } = [];

    public decimal Total => Items.Sum(i => i.UnitPriceUsd * i.Quantity);
}

public class OrderItem
{
    public int Id { get; set; }
    public int OrderId { get; set; }
    public required string ProductSku { get; set; }
    public Product? Product { get; set; }
    public int Quantity { get; set; }
    public decimal UnitPriceUsd { get; set; }
}

public enum AppointmentStatus { PendingConfirmation, Confirmed, Cancelled }

public class Appointment
{
    public int Id { get; set; }
    public required string CustomerId { get; set; }
    public int PetId { get; set; }
    public Pet? Pet { get; set; }
    public required string Service { get; set; }
    public DateTime StartsAt { get; set; }
    public AppointmentStatus Status { get; set; } = AppointmentStatus.PendingConfirmation;
}

public enum PendingActionType { Return, Appointment }

public enum PendingActionStatus { Pending, Confirmed, Cancelled }

/// <summary>
/// Acción propuesta por el agente que solo el cliente puede confirmar (human-in-the-loop).
/// El LLM puede crearla, pero nunca ejecutarla.
/// </summary>
public class PendingAction
{
    public int Id { get; set; }
    public required string CustomerId { get; set; }
    public PendingActionType Type { get; set; }
    public PendingActionStatus Status { get; set; } = PendingActionStatus.Pending;
    public int? OrderId { get; set; }
    public int? AppointmentId { get; set; }
    public required string Description { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime ExpiresAt { get; set; }
}
