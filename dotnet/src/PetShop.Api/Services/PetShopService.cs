using Microsoft.EntityFrameworkCore;
using PetShop.Api.Contracts;
using PetShop.Api.Data;
using PetShop.Api.Domain;

namespace PetShop.Api.Services;

/// <summary>Resultado de una operación de dominio: valor o error esperable (404/409/422).</summary>
public record Outcome<T>(T? Value, string? Error = null, int StatusCode = 200)
{
    public bool Ok => Error is null;
    public static Outcome<T> Success(T value) => new(value);
    public static Outcome<T> NotFound(string error) => new(default, error, 404);
    public static Outcome<T> Conflict(string error) => new(default, error, 409);
    public static Outcome<T> Invalid(string error) => new(default, error, 422);
}

/// <summary>
/// Todas las operaciones de cliente reciben el customerId del llamador autenticado, nunca del LLM.
/// </summary>
public class PetShopService(PetShopDbContext db, TimeProvider clock)
{
    private static readonly TimeSpan ActionTtl = TimeSpan.FromHours(24);

    private DateTime Now => clock.GetLocalNow().DateTime;
    private DateOnly Today => DateOnly.FromDateTime(Now);

    public async Task<IReadOnlyList<ProductDto>> SearchProductsAsync(string? query, string? species, string? category, int take = 10)
    {
        var q = db.Products.AsNoTracking();
        if (!string.IsNullOrWhiteSpace(species)) q = q.Where(p => p.Species == species.ToLower());
        if (!string.IsNullOrWhiteSpace(category)) q = q.Where(p => p.Category == category.ToLower());
        if (!string.IsNullOrWhiteSpace(query))
        {
            foreach (var term in query.ToLower().Split(' ', StringSplitOptions.RemoveEmptyEntries))
                q = q.Where(p => EF.Functions.ILike(p.Name + " " + p.Description + " " + p.Brand, $"%{term}%"));
        }
        var items = await q.OrderBy(p => p.Sku).Take(Math.Clamp(take, 1, 25)).ToListAsync();
        return items.Select(ProductDto.From).ToList();
    }

    public async Task<Outcome<ProductDto>> GetProductAsync(string sku)
    {
        var p = await db.Products.AsNoTracking().FirstOrDefaultAsync(p => p.Sku == sku.Trim().ToUpper());
        return p is null ? Outcome<ProductDto>.NotFound($"No existe el producto {sku}.") : Outcome<ProductDto>.Success(ProductDto.From(p));
    }

    public async Task<Customer?> FindCustomerAsync(string customerId) =>
        await db.Customers.AsNoTracking().FirstOrDefaultAsync(c => c.Id == customerId);

    public async Task<Customer?> FindCustomerByEmailAsync(string email) =>
        await db.Customers.AsNoTracking().FirstOrDefaultAsync(c => c.Email == email.Trim().ToLower());

    public async Task<IReadOnlyList<OrderDto>> GetOrdersAsync(string customerId)
    {
        var orders = await db.Orders.AsNoTracking()
            .Include(o => o.Items).ThenInclude(i => i.Product)
            .Where(o => o.CustomerId == customerId)
            .OrderByDescending(o => o.CreatedAt).ToListAsync();
        return orders.Select(OrderDto.From).ToList();
    }

    public async Task<IReadOnlyList<PetDto>> GetPetsAsync(string customerId)
    {
        var pets = await db.Pets.AsNoTracking().Where(p => p.CustomerId == customerId).OrderBy(p => p.Name).ToListAsync();
        return pets.Select(ToDto).ToList();
    }

    private PetDto ToDto(Pet p)
    {
        var months = (Today.Year - p.BirthDate.Year) * 12 + Today.Month - p.BirthDate.Month;
        return new PetDto(p.Id, p.Name, p.Species, p.Breed, Math.Max(0, months), p.WeightKg);
    }

    public async Task<Outcome<PendingActionDto>> RequestReturnAsync(string customerId, int orderId)
    {
        var order = await db.Orders.Include(o => o.Items).ThenInclude(i => i.Product)
            .FirstOrDefaultAsync(o => o.Id == orderId && o.CustomerId == customerId);
        if (order is null)
            // Mismo mensaje exista o no el pedido: no revelamos pedidos de otros clientes
            return Outcome<PendingActionDto>.NotFound($"No encontré el pedido {orderId} entre tus pedidos.");

        if (ReturnPolicy.WhyNotEligible(order, Today) is { } reason)
            return Outcome<PendingActionDto>.Conflict(reason);

        var existing = await db.PendingActions.FirstOrDefaultAsync(a =>
            a.OrderId == orderId && a.Status == PendingActionStatus.Pending && a.ExpiresAt > Now);
        if (existing is not null) return Outcome<PendingActionDto>.Success(PendingActionDto.From(existing));

        var items = string.Join(", ", order.Items.Select(i => i.Product?.Name ?? i.ProductSku));
        var action = new PendingAction
        {
            CustomerId = customerId, Type = PendingActionType.Return, OrderId = orderId,
            Description = $"Devolución del pedido {orderId} ({items}) por ${order.Total} USD",
            CreatedAt = Now, ExpiresAt = Now.Add(ActionTtl),
        };
        db.PendingActions.Add(action);
        await db.SaveChangesAsync();
        return Outcome<PendingActionDto>.Success(PendingActionDto.From(action));
    }

    public async Task<Outcome<IReadOnlyList<DateTime>>> GetAvailabilityAsync(string service, DateOnly day)
    {
        if (!AppointmentScheduler.Services.ContainsKey(service))
            return Outcome<IReadOnlyList<DateTime>>.Invalid(
                $"Servicio desconocido '{service}'. Disponibles: {string.Join(", ", AppointmentScheduler.Services.Keys)}.");
        var taken = await TakenSlotsAsync(service, day.ToDateTime(TimeOnly.MinValue), day.ToDateTime(TimeOnly.MaxValue));
        return Outcome<IReadOnlyList<DateTime>>.Success(AppointmentScheduler.FreeSlots(day, taken, Now));
    }

    private Task<List<DateTime>> TakenSlotsAsync(string service, DateTime from, DateTime to)
    {
        var now = Now;
        // Un turno sin confirmar bloquea el horario solo mientras su acción pendiente no venza
        return db.Appointments
            .Where(a => a.Service == service && a.StartsAt >= from && a.StartsAt <= to)
            .Where(a => a.Status == AppointmentStatus.Confirmed ||
                        (a.Status == AppointmentStatus.PendingConfirmation &&
                         db.PendingActions.Any(p => p.AppointmentId == a.Id && p.Status == PendingActionStatus.Pending && p.ExpiresAt > now)))
            .Select(a => a.StartsAt).ToListAsync();
    }

    public async Task<Outcome<PendingActionDto>> RequestAppointmentAsync(string customerId, AppointmentRequest req)
    {
        var pet = await db.Pets.FirstOrDefaultAsync(p => p.CustomerId == customerId && p.Name.ToLower() == req.PetName.Trim().ToLower());
        if (pet is null)
            return Outcome<PendingActionDto>.NotFound($"No encontré una mascota llamada {req.PetName} entre tus mascotas.");

        var service = req.Service.Trim().ToLower();
        if (AppointmentScheduler.Validate(service, req.StartsAt, Now) is { } error)
            return Outcome<PendingActionDto>.Invalid(error);
        if ((await TakenSlotsAsync(service, req.StartsAt, req.StartsAt)).Count > 0)
            return Outcome<PendingActionDto>.Conflict($"El horario {req.StartsAt:yyyy-MM-dd HH:mm} ya está ocupado para {service}.");

        var appointment = new Appointment { CustomerId = customerId, PetId = pet.Id, Service = service, StartsAt = req.StartsAt };
        db.Appointments.Add(appointment);
        await db.SaveChangesAsync();

        var action = new PendingAction
        {
            CustomerId = customerId, Type = PendingActionType.Appointment, AppointmentId = appointment.Id,
            Description = $"Turno de {AppointmentScheduler.Services[service]} para {pet.Name} el {req.StartsAt:yyyy-MM-dd} a las {req.StartsAt:HH:mm}",
            CreatedAt = Now, ExpiresAt = Now.Add(ActionTtl),
        };
        db.PendingActions.Add(action);
        await db.SaveChangesAsync();
        return Outcome<PendingActionDto>.Success(PendingActionDto.From(action));
    }

    public async Task<Outcome<FoodRecommendationDto>> RecommendFoodAsync(string? customerId, FoodRecommendationRequest req)
    {
        FoodRequest request;
        if (!string.IsNullOrWhiteSpace(req.PetName) && customerId is not null)
        {
            var pet = (await GetPetsAsync(customerId)).FirstOrDefault(p => p.Name.Equals(req.PetName.Trim(), StringComparison.OrdinalIgnoreCase));
            if (pet is null)
                return Outcome<FoodRecommendationDto>.NotFound($"No encontré una mascota llamada {req.PetName} entre tus mascotas.");
            request = new FoodRequest(pet.Species, pet.AgeMonths, pet.WeightKg, req.Need);
        }
        else if (req is { Species: not null, AgeMonths: not null, WeightKg: not null })
        {
            request = new FoodRequest(req.Species, req.AgeMonths.Value, req.WeightKg.Value, req.Need);
        }
        else
        {
            return Outcome<FoodRecommendationDto>.Invalid("Indica el nombre de la mascota o su especie, edad en meses y peso en kg.");
        }

        var species = request.Species.ToLower();
        var catalog = await db.Products.AsNoTracking().Where(p => p.Category == "alimento" && p.Species == species).ToListAsync();
        var rec = FoodRecommender.Recommend(request, catalog);
        return Outcome<FoodRecommendationDto>.Success(new FoodRecommendationDto(
            rec.LifeStage, rec.Size, rec.Rationale, rec.Products.Select(ProductDto.From).ToList()));
    }

    public async Task<IReadOnlyList<AppointmentDto>> GetAppointmentsAsync(string customerId) =>
        await db.Appointments.AsNoTracking().Include(a => a.Pet)
            .Where(a => a.CustomerId == customerId && a.Status != AppointmentStatus.Cancelled)
            .OrderBy(a => a.StartsAt)
            .Select(a => new AppointmentDto(a.Id, a.Pet!.Name, a.Service, a.StartsAt, a.Status.ToString()))
            .ToListAsync();

    public async Task<IReadOnlyList<PendingActionDto>> GetPendingActionsAsync(string customerId) =>
        (await db.PendingActions.AsNoTracking()
            .Where(a => a.CustomerId == customerId && a.Status == PendingActionStatus.Pending && a.ExpiresAt > Now)
            .OrderBy(a => a.Id).ToListAsync())
        .Select(PendingActionDto.From).ToList();

    /// <summary>Lo ejecuta el cliente desde la UI (botón "Confirmar"); nunca lo dispara el LLM.</summary>
    public async Task<Outcome<string>> ConfirmAsync(string customerId, int actionId)
    {
        var action = await db.PendingActions.FirstOrDefaultAsync(a =>
            a.Id == actionId && a.CustomerId == customerId && a.Status == PendingActionStatus.Pending);
        if (action is null || action.ExpiresAt <= Now)
            return Outcome<string>.NotFound($"No hay una acción pendiente {actionId} para confirmar.");

        switch (action.Type)
        {
            case PendingActionType.Return:
                var order = await db.Orders.Include(o => o.Items).FirstAsync(o => o.Id == action.OrderId);
                // Se revalida: pudo cambiar algo entre la propuesta y la confirmación
                if (ReturnPolicy.WhyNotEligible(order, Today) is { } reason) return Outcome<string>.Conflict(reason);
                order.Status = OrderStatus.Returned;
                action.Status = PendingActionStatus.Confirmed;
                await db.SaveChangesAsync();
                return Outcome<string>.Success($"Devolución procesada: ${order.Total} USD devueltos.");

            case PendingActionType.Appointment:
                var appointment = await db.Appointments.FirstAsync(a => a.Id == action.AppointmentId);
                appointment.Status = AppointmentStatus.Confirmed;
                action.Status = PendingActionStatus.Confirmed;
                await db.SaveChangesAsync();
                return Outcome<string>.Success($"Turno confirmado: {action.Description}.");

            default:
                return Outcome<string>.Invalid("Tipo de acción desconocido.");
        }
    }

    public async Task<Outcome<string>> CancelAsync(string customerId, int actionId)
    {
        var action = await db.PendingActions.FirstOrDefaultAsync(a =>
            a.Id == actionId && a.CustomerId == customerId && a.Status == PendingActionStatus.Pending);
        if (action is null) return Outcome<string>.NotFound($"No hay una acción pendiente {actionId}.");

        action.Status = PendingActionStatus.Cancelled;
        if (action.AppointmentId is { } appointmentId)
            (await db.Appointments.FirstAsync(a => a.Id == appointmentId)).Status = AppointmentStatus.Cancelled;
        await db.SaveChangesAsync();
        return Outcome<string>.Success("Acción cancelada.");
    }
}
