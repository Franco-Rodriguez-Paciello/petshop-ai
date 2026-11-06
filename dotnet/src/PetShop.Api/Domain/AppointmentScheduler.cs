namespace PetShop.Api.Domain;

public static class AppointmentScheduler
{
    public static readonly IReadOnlyDictionary<string, string> Services = new Dictionary<string, string>
    {
        ["baño"] = "Baño y secado",
        ["peluqueria"] = "Peluquería y corte de uñas",
        ["veterinaria"] = "Consulta veterinaria general",
    };

    public const int OpeningHour = 9;
    public const int ClosingHour = 18;
    public const int MaxDaysAhead = 30;

    public static string? Validate(string service, DateTime startsAt, DateTime now)
    {
        if (!Services.ContainsKey(service))
            return $"Servicio desconocido '{service}'. Servicios disponibles: {string.Join(", ", Services.Keys)}.";
        if (startsAt <= now)
            return "El turno debe ser en el futuro.";
        if (startsAt > now.AddDays(MaxDaysAhead))
            return $"Solo se pueden reservar turnos con hasta {MaxDaysAhead} días de anticipación.";
        if (startsAt.DayOfWeek == DayOfWeek.Sunday)
            return "Los domingos el local está cerrado.";
        if (startsAt.Minute != 0 || startsAt.Hour < OpeningHour || startsAt.Hour >= ClosingHour)
            return $"Los turnos son en horas exactas entre las {OpeningHour}:00 y las {ClosingHour - 1}:00.";
        return null;
    }

    public static IReadOnlyList<DateTime> FreeSlots(DateOnly day, IEnumerable<DateTime> taken, DateTime now)
    {
        if (day.DayOfWeek == DayOfWeek.Sunday) return [];
        var takenSet = taken.ToHashSet();
        return Enumerable.Range(OpeningHour, ClosingHour - OpeningHour)
            .Select(h => day.ToDateTime(new TimeOnly(h, 0)))
            .Where(s => s > now && !takenSet.Contains(s))
            .ToList();
    }
}
