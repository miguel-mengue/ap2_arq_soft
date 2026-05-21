from dataclasses import dataclass, asdict
from typing import List

@dataclass
class Link:
    loja: str
    url: str

@dataclass
class Produto:
    nome: str
    links: List[Link]
    
    @classmethod
    def from_dict(cls, data: dict) -> "Produto":
        links = [Link(**link_data) for link_data in data.get("links", [])]
        return cls(nome=data["nome"], links=links)

@dataclass
class RegistroHistorico:
    produto: str
    preco: float
    loja: str
    data: str
    url: str
    
    def to_dict(self) -> dict:
        return asdict(self)
