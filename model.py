from dataclasses import dataclass


@dataclass()
class Client:

    client_id: str
    country: str
    sector: str
    rating: str
    age : int


@dataclass()
class Exposure:

    client_id: str
    loan_amount: float
    ead: float
    pd: float
    lgd: float


@dataclass()
class Collateral:

    client_id: str
    collateral_value: float

