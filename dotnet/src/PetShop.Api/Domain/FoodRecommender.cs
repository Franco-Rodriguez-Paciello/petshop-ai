namespace PetShop.Api.Domain;

public record FoodRequest(string Species, int AgeMonths, decimal WeightKg, string? Need = null);

public record FoodRecommendation(string LifeStage, string Size, IReadOnlyList<Product> Products, string Rationale);

/// <summary>
/// Recomendación determinista: las reglas nutricionales viven en código, el LLM solo las explica.
/// </summary>
public static class FoodRecommender
{
    public static readonly string[] SupportedNeeds = ["sin granos", "control de peso", "esterilizado", "urinario", "bolas de pelo"];

    public static string LifeStageFor(string species, int ageMonths) => species switch
    {
        "perro" when ageMonths < 12 => "cachorro",
        "perro" when ageMonths >= 84 => "senior",
        "gato" when ageMonths < 12 => "cachorro",
        "gato" when ageMonths >= 120 => "senior",
        _ => "adulto",
    };

    public static string SizeFor(string species, decimal weightKg) => species switch
    {
        "perro" when weightKg < 10 => "pequeño",
        "perro" when weightKg < 25 => "mediano",
        "perro" => "grande",
        _ => "todos",
    };

    public static FoodRecommendation Recommend(FoodRequest request, IEnumerable<Product> catalog, int take = 5)
    {
        var species = request.Species.Trim().ToLowerInvariant();
        var stage = LifeStageFor(species, request.AgeMonths);
        var size = SizeFor(species, request.WeightKg);
        var need = request.Need?.Trim().ToLowerInvariant();

        var candidates = catalog
            .Where(p => p.Category == "alimento" && p.Species == species && p.Stock > 0)
            .Where(p => p.LifeStage == stage || p.LifeStage == "todos")
            .Where(p => p.Size == size || p.Size == "todos");

        // Las líneas especiales (sin granos, control de peso...) solo se recomiendan si se piden
        candidates = string.IsNullOrEmpty(need)
            ? candidates.Where(p => !SupportedNeeds.Any(n => p.Description.Contains(n, StringComparison.OrdinalIgnoreCase)))
            : candidates.Where(p => p.Description.Contains(need, StringComparison.OrdinalIgnoreCase));

        var products = candidates
            .OrderByDescending(p => p.Size == size)
            .ThenByDescending(p => p.LifeStage == stage)
            .ThenBy(p => p.PriceUsd)
            .Take(take)
            .ToList();

        var rationale = $"{species} de {request.AgeMonths} meses y {request.WeightKg} kg: etapa {stage}" +
                        (size == "todos" ? "" : $", tamaño {size}") +
                        (string.IsNullOrEmpty(need) ? "." : $", necesidad: {need}.");

        return new FoodRecommendation(stage, size, products, rationale);
    }
}
