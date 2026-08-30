import uuid
from datetime import date as date_type

from pydantic import BaseModel, Field

# ---------------------------------------------------------------- seasons ---


class SeasonCreateIn(BaseModel):
    label: str
    date_debut: date_type
    date_fin: date_type


class SeasonUpdateIn(BaseModel):
    label: str | None = None
    date_debut: date_type | None = None
    date_fin: date_type | None = None
    is_active: bool | None = None


class SeasonOut(BaseModel):
    id: uuid.UUID
    establishment_id: uuid.UUID
    label: str
    date_debut: date_type
    date_fin: date_type
    is_active: bool

    model_config = {"from_attributes": True}


# -------------------------------------------------------------- rate_grid ---


class RateGridCreateIn(BaseModel):
    room_category: str
    season_id: uuid.UUID
    regime: str = Field(pattern="^(BB|DP|PC)$")
    prix_ttc: float = Field(gt=0)
    prix_ht: float = Field(gt=0)
    tva_rate: float = 10.00


class RateGridUpdateIn(BaseModel):
    prix_ttc: float | None = None
    prix_ht: float | None = None
    tva_rate: float | None = None


class RateGridOut(BaseModel):
    id: uuid.UUID
    establishment_id: uuid.UUID
    room_category: str
    season_id: uuid.UUID
    regime: str
    prix_ttc: float
    prix_ht: float
    tva_rate: float

    model_config = {"from_attributes": True}


# ------------------------------------------------------------ taxes_config --


class TaxConfigCreateIn(BaseModel):
    type: str = Field(pattern="^(TVA_HEBERGEMENT|TVA_AUTRE|TS|TPT)$")
    taux_ou_montant: float
    mode_calcul: str = Field(pattern="^(PERCENTAGE|FIXED_PER_PAX)$")
    applicable_from: date_type = date_type(2024, 1, 1)
    applicable_to: date_type | None = None


class TaxConfigUpdateIn(BaseModel):
    taux_ou_montant: float | None = None
    applicable_to: date_type | None = None
    is_active: bool | None = None


class TaxConfigOut(BaseModel):
    id: uuid.UUID
    establishment_id: uuid.UUID
    type: str
    taux_ou_montant: float
    mode_calcul: str
    applicable_from: date_type
    applicable_to: date_type | None
    is_active: bool

    model_config = {"from_attributes": True}


# ----------------------------------------------------------- extras_catalog -


class ExtrasCatalogItemCreateIn(BaseModel):
    categorie: str = Field(pattern="^(Restaurant|Bar|SPA|Activités|Autre)$")
    libelle: str
    description: str | None = None
    prix_ht: float = Field(gt=0)
    tva_rate: float = 20.00


class ExtrasCatalogItemUpdateIn(BaseModel):
    libelle: str | None = None
    description: str | None = None
    is_active: bool | None = None


class ExtrasCatalogItemOut(BaseModel):
    id: uuid.UUID
    establishment_id: uuid.UUID
    categorie: str
    libelle: str
    description: str | None
    prix_ht: float
    tva_rate: float
    prix_ttc: float
    is_active: bool

    model_config = {"from_attributes": True}


# ------------------------------------------------------------ partner_rates -


class PartnerRateCreateIn(BaseModel):
    partner_id: uuid.UUID
    season_id: uuid.UUID
    room_category: str
    regime: str = Field(pattern="^(BB|DP|PC)$")
    tarif_negocie: float = Field(gt=0)
    commission_pct: float = 0


class PartnerRateUpdateIn(BaseModel):
    tarif_negocie: float | None = None
    commission_pct: float | None = None


class PartnerRateOut(BaseModel):
    id: uuid.UUID
    establishment_id: uuid.UUID
    partner_id: uuid.UUID
    season_id: uuid.UUID
    room_category: str
    regime: str
    tarif_negocie: float
    commission_pct: float

    model_config = {"from_attributes": True}


# ----------------------------------------------------------------- packages -


class PackageCreateIn(BaseModel):
    label: str
    description: str | None = None
    prix_global_ttc: float = Field(gt=0)
    ventilation: dict
    valid_from: date_type | None = None
    valid_to: date_type | None = None


class PackageUpdateIn(BaseModel):
    label: str | None = None
    description: str | None = None
    prix_global_ttc: float | None = None
    ventilation: dict | None = None
    is_active: bool | None = None
    valid_from: date_type | None = None
    valid_to: date_type | None = None


class PackageOut(BaseModel):
    id: uuid.UUID
    establishment_id: uuid.UUID
    label: str
    description: str | None
    prix_global_ttc: float
    ventilation: dict
    is_active: bool
    valid_from: date_type | None
    valid_to: date_type | None

    model_config = {"from_attributes": True}


# ------------------------------------------------------------- rate lookup --


class NightRate(BaseModel):
    date: str
    season_id: uuid.UUID
    prix_ttc: float


class RateCalculateOut(BaseModel):
    room_category: str
    regime: str
    nights: list[NightRate]
    total_ttc: float
