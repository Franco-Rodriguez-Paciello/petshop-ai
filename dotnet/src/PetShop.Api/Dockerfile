# Contexto de build: raíz del repo (para copiar data/catalog)
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY dotnet/src/PetShop.Api/PetShop.Api.csproj dotnet/src/PetShop.Api/
RUN dotnet restore dotnet/src/PetShop.Api/PetShop.Api.csproj
COPY dotnet/src/PetShop.Api/ dotnet/src/PetShop.Api/
RUN dotnet publish dotnet/src/PetShop.Api/PetShop.Api.csproj -c Release -o /app --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:10.0
WORKDIR /app
COPY --from=build /app .
COPY data/catalog/products.json /app/data/products.json
ENV ASPNETCORE_URLS=http://+:8080 \
    Seed__CatalogPath=/app/data/products.json
EXPOSE 8080
USER $APP_UID
ENTRYPOINT ["dotnet", "PetShop.Api.dll"]
