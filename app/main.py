"""Минимальный HTTP API каталога устройств.

Данные расположены в памяти процесса. Сервер демонстрационный без БД,
авторизации и изменения ресурсов.
"""

from typing import Annotated

from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field


class Product(BaseModel):
    """Представление одного устройства в JSON."""

    id: int = Field(description="Идентификатор устройства", examples=[5])
    name: str = Field(description="Название", examples=["Relay Controller"])
    type: str = Field(description="Тип устройства", examples=["controller"])
    status: str = Field(description="Состояние", examples=["active"])
    price: float = Field(description="Учебная цена", examples=[59.9])
    tags: list[str] = Field(description="Метки устройства", examples=[["power"]])


class CatalogMeta(BaseModel):
    total: int = Field(description="Общее количество устройств")


class ProductCollection(BaseModel):
    data: list[Product]
    meta: CatalogMeta


app = FastAPI(
    title="Учебный API каталога устройств",
    description=(
        "Два GET-маршрута: коллекция и отдельный ресурс. "
        "Пример по HTTP API и FastAPI. "
        "Данные хранятся в памяти, изменить их через API нельзя."
    ),
    version="1.0.0",
    openapi_tags=[{"name": "Устройства", "description": "Операции чтения каталога"}],
)

# Значения сопоставимы с примерами API Academy; это отдельный реальный HTTP-сервер.
_PRODUCTS: tuple[Product, ...] = (
    Product(id=1, name="Humidity Sensor", type="sensor", status="active", price=19.9, tags=["climate", "indoor"]),
    Product(id=2, name="Motion Sensor", type="sensor", status="inactive", price=27.5, tags=["security"]),
    Product(id=3, name="Temperature Sensor", type="sensor", status="active", price=24.5, tags=["climate", "indoor"]),
    Product(id=4, name="Smart Gateway", type="gateway", status="active", price=149.0, tags=["network"]),
    Product(id=5, name="Relay Controller", type="controller", status="active", price=59.9, tags=["power"]),
)


@app.get("/", include_in_schema=False)
def home() -> RedirectResponse:
    """Ссылка на открытый порт сразу ведёт к Swagger UI."""
    return RedirectResponse(url="/docs")


@app.get(
    "/api/products",
    response_model=ProductCollection,
    tags=["Устройства"],
    summary="Получить коллекцию устройств",
    description="Возвращает список пяти устройств и поле meta.total.",
)
def list_products() -> ProductCollection:
    return ProductCollection(data=list(_PRODUCTS), meta=CatalogMeta(total=len(_PRODUCTS)))


@app.get(
    "/api/products/{product_id}",
    response_model=Product,
    tags=["Устройства"],
    summary="Получить устройство по идентификатору",
    description="Параметр product_id берётся из URL. Если устройство отсутствует, сервер возвращает 404.",
    responses={404: {"description": "Устройство с таким идентификатором не найдено"}},
)
def get_product(
    product_id: Annotated[int, Path(ge=1, description="Положительный идентификатор устройства")],
) -> Product:
    for product in _PRODUCTS:
        if product.id == product_id:
            return product
    raise HTTPException(status_code=404, detail=f"Устройство {product_id} не найдено")
