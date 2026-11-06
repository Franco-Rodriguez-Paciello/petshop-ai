using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using PetShop.Api.Data;
using PetShop.Api.Endpoints;
using PetShop.Api.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddDbContext<PetShopDbContext>(o =>
    o.UseNpgsql(builder.Configuration.GetConnectionString("PetShop")));
builder.Services.AddSingleton(TimeProvider.System);
builder.Services.AddScoped<PetShopService>();
builder.Services.AddScoped<Seeder>();
builder.Services.AddScoped<Auth.InternalKeyFilter>();
builder.Services.AddHttpClient<AiServiceClient>(c =>
{
    c.BaseAddress = new Uri(builder.Configuration["AiService:BaseUrl"] ?? "http://localhost:8000");
    c.Timeout = TimeSpan.FromMinutes(3);
});

builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme).AddJwtBearer(o =>
{
    o.MapInboundClaims = false;
    o.TokenValidationParameters = new TokenValidationParameters
    {
        ValidIssuer = "petshop",
        ValidAudience = "petshop",
        IssuerSigningKey = Auth.SigningKey(builder.Configuration),
    };
});
builder.Services.AddAuthorization();
builder.Services.AddOpenApi();
builder.Services.AddProblemDetails();

var app = builder.Build();

using (var scope = app.Services.CreateScope())
    await scope.ServiceProvider.GetRequiredService<Seeder>().SeedIfEmptyAsync();

app.MapOpenApi();
app.UseExceptionHandler();
app.UseAuthentication();
app.UseAuthorization();

app.MapGet("/health", () => Results.Ok(new { status = "ok" }));
app.MapAuthEndpoints();
app.MapPetShopEndpoints();
app.MapConfirmationEndpoints();
app.MapChatEndpoint();

app.Run();

public partial class Program;
