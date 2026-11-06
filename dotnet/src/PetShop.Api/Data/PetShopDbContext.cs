using Microsoft.EntityFrameworkCore;
using PetShop.Api.Domain;

namespace PetShop.Api.Data;

public class PetShopDbContext(DbContextOptions<PetShopDbContext> options) : DbContext(options)
{
    public DbSet<Product> Products => Set<Product>();
    public DbSet<Customer> Customers => Set<Customer>();
    public DbSet<Pet> Pets => Set<Pet>();
    public DbSet<Order> Orders => Set<Order>();
    public DbSet<OrderItem> OrderItems => Set<OrderItem>();
    public DbSet<Appointment> Appointments => Set<Appointment>();
    public DbSet<PendingAction> PendingActions => Set<PendingAction>();

    protected override void ConfigureConventions(ModelConfigurationBuilder builder)
    {
        // Hora local del local comercial, sin zona horaria
        builder.Properties<DateTime>().HaveColumnType("timestamp without time zone");
        builder.Properties<decimal>().HavePrecision(10, 2);
    }

    protected override void OnModelCreating(ModelBuilder b)
    {
        b.Entity<Product>().HasKey(p => p.Sku);
        b.Entity<Product>().HasIndex(p => new { p.Species, p.Category });

        b.Entity<Customer>().HasIndex(c => c.Email).IsUnique();
        b.Entity<Customer>().HasMany(c => c.Pets).WithOne().HasForeignKey(p => p.CustomerId);

        b.Entity<Order>().HasIndex(o => o.CustomerId);
        b.Entity<Order>().Property(o => o.Status).HasConversion<string>();
        b.Entity<Order>().Ignore(o => o.Total);
        b.Entity<Order>().HasMany(o => o.Items).WithOne().HasForeignKey(i => i.OrderId);

        b.Entity<Appointment>().Property(a => a.Status).HasConversion<string>();
        b.Entity<Appointment>().HasIndex(a => new { a.Service, a.StartsAt });

        b.Entity<PendingAction>().Property(a => a.Type).HasConversion<string>();
        b.Entity<PendingAction>().Property(a => a.Status).HasConversion<string>();
        b.Entity<PendingAction>().HasIndex(a => new { a.CustomerId, a.Status });
    }
}
