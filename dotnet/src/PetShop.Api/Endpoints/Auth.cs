using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using Microsoft.IdentityModel.Tokens;
using PetShop.Api.Contracts;
using PetShop.Api.Services;

namespace PetShop.Api.Endpoints;

public static class Auth
{
    public const string InternalKeyHeader = "X-Internal-Key";
    public const string CustomerIdHeader = "X-Customer-Id";

    public static SymmetricSecurityKey SigningKey(IConfiguration config) =>
        new(Encoding.UTF8.GetBytes(config["Jwt:Key"] ?? throw new InvalidOperationException("Falta Jwt:Key")));

    public static string CustomerId(this ClaimsPrincipal user) =>
        user.FindFirstValue(JwtRegisteredClaimNames.Sub) ?? throw new UnauthorizedAccessException();

    public static void MapAuthEndpoints(this IEndpointRouteBuilder app)
    {
        // Login de DEMO: solo pide el email. En producción iría un proveedor de identidad real (Entra ID, Auth0...).
        app.MapPost("/api/auth/demo-login", async (LoginRequest req, PetShopService svc, IConfiguration config) =>
        {
            var customer = (await svc.FindCustomerByEmailAsync(req.Email));
            if (customer is null) return Results.Unauthorized();

            var token = new JwtSecurityTokenHandler().WriteToken(new JwtSecurityToken(
                issuer: "petshop", audience: "petshop",
                claims: [new Claim(JwtRegisteredClaimNames.Sub, customer.Id), new Claim("name", customer.Name)],
                expires: DateTime.UtcNow.AddHours(8),
                signingCredentials: new SigningCredentials(SigningKey(config), SecurityAlgorithms.HmacSha256)));
            return Results.Ok(new LoginResponse(token, customer.Id, customer.Name));
        }).WithTags("Auth");
    }

    /// <summary>Solo servicios internos (AI service, MCP server) con la clave compartida pueden llamar a /internal.</summary>
    public class InternalKeyFilter(IConfiguration config) : IEndpointFilter
    {
        public async ValueTask<object?> InvokeAsync(EndpointFilterInvocationContext ctx, EndpointFilterDelegate next)
        {
            var expected = config["Internal:ApiKey"];
            var provided = ctx.HttpContext.Request.Headers[InternalKeyHeader].ToString();
            if (string.IsNullOrEmpty(expected) ||
                !System.Security.Cryptography.CryptographicOperations.FixedTimeEquals(
                    Encoding.UTF8.GetBytes(provided), Encoding.UTF8.GetBytes(expected)))
                return Results.Unauthorized();
            return await next(ctx);
        }
    }
}
