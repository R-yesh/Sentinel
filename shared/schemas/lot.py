from pydantic import BaseModel, Field


class LotContext(BaseModel):
    lot_id: str

    component_ids: list[str] = Field(
        default_factory=list
    )

    leakage_24h_population: list[float] = Field(
        default_factory=list
    )