namespace PetShop.Api.Domain;

public static class ReturnPolicy
{
    public const int WindowDays = 30;

    /// <summary>Devuelve null si el pedido es elegible, o el motivo por el que no lo es.</summary>
    public static string? WhyNotEligible(Order order, DateOnly today)
    {
        if (order.Status == OrderStatus.Returned)
            return $"El pedido {order.Id} ya fue devuelto anteriormente.";

        var deadline = order.CreatedAt.AddDays(WindowDays);
        if (today > deadline)
            return $"La devolución no es elegible: el pedido es del {order.CreatedAt:yyyy-MM-dd} " +
                   $"y la ventana de {WindowDays} días venció el {deadline:yyyy-MM-dd}.";

        return null;
    }
}
