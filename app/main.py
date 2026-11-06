"""Учебный каталог устройств: HTTP API, CRUD и браузерный каталог.

Данные содержатся в памяти сервера. Это учебная, а не производственная система.
"""

from pathlib import Path
from threading import RLock
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Path as PathParam, Query, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


ProductType = Literal["sensor", "gateway", "controller", "actuator"]
ProductStatus = Literal["active", "inactive", "archived"]


class ProductFields(BaseModel):
    """Поля, доступные при создании или полной замене устройства."""

    name: str = Field(min_length=2, max_length=100, examples=["CO2 Sensor"])
    type: ProductType = Field(examples=["sensor"])
    status: ProductStatus = Field(default="active")
    price: float = Field(ge=0, examples=[35.5])
    tags: list[str] = Field(default_factory=list, max_length=12)


class Product(ProductFields):
    id: int = Field(ge=1, description="Идентификатор устройства", examples=[5])


class ProductPatch(BaseModel):
    """Для PATCH поля необязательны; переданные null запрещены обработчиком."""

    name: str | None = Field(default=None, min_length=2, max_length=100)
    type: ProductType | None = None
    status: ProductStatus | None = None
    price: float | None = Field(default=None, ge=0)
    tags: list[str] | None = Field(default=None, max_length=12)


class CollectionMeta(BaseModel):
    count: int
    total: int


class ProductCollection(BaseModel):
    data: list[Product]
    meta: CollectionMeta


class ResetResult(BaseModel):
    restored: int
    message: str


INITIAL_PRODUCTS: tuple[Product, ...] = (
    Product(id=1, name="Humidity Sensor", type="sensor", status="active", price=19.9, tags=["climate", "indoor"]),
    Product(id=2, name="Motion Sensor", type="sensor", status="inactive", price=27.5, tags=["security"]),
    Product(id=3, name="Temperature Sensor", type="sensor", status="active", price=24.5, tags=["climate", "indoor"]),
    Product(id=4, name="Smart Gateway", type="gateway", status="active", price=149.0, tags=["network"]),
    Product(id=5, name="Relay Controller", type="controller", status="active", price=59.9, tags=["power"]),
)

_lock = RLock()
_products: dict[int, Product] = {}
_next_id = 6


def _reset_data() -> None:
    global _next_id
    with _lock:
        _products.clear()
        _products.update({p.id: p.model_copy(deep=True) for p in INITIAL_PRODUCTS})
        _next_id = 6


_reset_data()

app = FastAPI(
    title="Учебный API каталога устройств",
    description=(
        "Демонстрация REST-подобных HTTP-операций. "
        "Список устройств, отдельные ресурсы, создание, замена, изменение и удаление. "
        "Данные сохраняются в памяти до перезапуска или сброса."
    ),
    version="2.0.0",
    openapi_tags=[
        {"name": "Каталог", "description": "Получение набора и отдельных ресурсов"},
        {"name": "Изменение", "description": "Создание, замена, изменение и удаление устройств"},
        {"name": "Демонстрация", "description": "Сброс учебных данных"},
    ],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    """Открывает браузерный каталог с ID и ссылками на JSON."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get(
    "/api/products", response_model=ProductCollection, tags=["Каталог"],
    summary="Получить список устройств",
    description="Опциональные query-параметры type и limit позволяют изучить фильтрацию и ограничение ответа.",
)
def list_products(
    type: ProductType | None = Query(default=None, description="Тип устройства для фильтрации"),
    limit: int = Query(default=100, ge=1, le=100, description="Максимум записей в ответе"),
) -> ProductCollection:
    with _lock:
        all_items = [item.model_copy(deep=True) for item in _products.values()]
    filtered = [item for item in all_items if type is None or item.type == type]
    return ProductCollection(
        data=filtered[:limit], meta=CollectionMeta(count=min(len(filtered), limit), total=len(all_items))
    )


@app.get(
    "/api/products/{product_id}", response_model=Product, tags=["Каталог"],
    summary="Получить устройство по ID",
    responses={404: {"description": "Ресурс не найден"}},
)
def get_product(product_id: Annotated[int, PathParam(ge=1)]) -> Product:
    with _lock:
        product = _products.get(product_id)
        if product is None:
            raise HTTPException(status_code=404, detail=f"Устройство {product_id} не найдено")
        return product.model_copy(deep=True)


def _require_distinct_name(name: str, *, excluding_id: int | None = None) -> None:
    if any(item.name.casefold() == name.casefold() and item.id != excluding_id for item in _products.values()):
        raise HTTPException(status_code=409, detail="Устройство с таким названием уже существует")


@app.post(
    "/api/products", response_model=Product, status_code=status.HTTP_201_CREATED,
    tags=["Изменение"], summary="Создать устройство",
    responses={409: {"description": "Название уже используется"}},
)
def create_product(payload: ProductFields, response: Response) -> Product:
    global _next_id
    with _lock:
        _require_distinct_name(payload.name)
        item = Product(id=_next_id, **payload.model_dump())
        _products[_next_id] = item
        _next_id += 1
    response.headers["Location"] = f"/api/products/{item.id}"
    return item.model_copy(deep=True)


@app.put(
    "/api/products/{product_id}", response_model=Product, tags=["Изменение"],
    summary="Полностью заменить устройство",
    responses={404: {"description": "Ресурс не найден"}},
)
def replace_product(product_id: Annotated[int, PathParam(ge=1)], payload: ProductFields) -> Product:
    with _lock:
        if product_id not in _products:
            raise HTTPException(status_code=404, detail=f"Устройство {product_id} не найдено")
        _require_distinct_name(payload.name, excluding_id=product_id)
        item = Product(id=product_id, **payload.model_dump())
        _products[product_id] = item
        return item.model_copy(deep=True)


@app.patch(
    "/api/products/{product_id}", response_model=Product, tags=["Изменение"],
    summary="Изменить отдельные поля устройства",
    responses={404: {"description": "Ресурс не найден"}},
)
def patch_product(product_id: Annotated[int, PathParam(ge=1)], payload: ProductPatch) -> Product:
    changes = payload.model_dump(exclude_unset=True)
    if any(value is None for value in changes.values()):
        raise HTTPException(status_code=422, detail="Переданные поля не должны содержать null")
    with _lock:
        current = _products.get(product_id)
        if current is None:
            raise HTTPException(status_code=404, detail=f"Устройство {product_id} не найдено")
        if "name" in changes:
            _require_distinct_name(changes["name"], excluding_id=product_id)
        changed = current.model_copy(update=changes)
        _products[product_id] = changed
        return changed.model_copy(deep=True)


@app.delete(
    "/api/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT,
    tags=["Изменение"], summary="Удалить устройство",
    responses={404: {"description": "Ресурс не найден"}},
)
def delete_product(product_id: Annotated[int, PathParam(ge=1)]) -> Response:
    with _lock:
        if product_id not in _products:
            raise HTTPException(status_code=404, detail=f"Устройство {product_id} не найдено")
        del _products[product_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post(
    "/api/reset", response_model=ResetResult, tags=["Демонстрация"],
    summary="Восстановить пять исходных устройств",
    description="Учебная служебная операция, чтобы повторить упражнение после POST/PUT/PATCH/DELETE.",
)
def reset_catalog() -> ResetResult:
    _reset_data()
    return ResetResult(restored=len(INITIAL_PRODUCTS), message="Исходный каталог восстановлен")
