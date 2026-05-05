"""
Sistema de auditoria del motor.
Registra que reglas dispararon durante el analisis.
"""
from dataclasses import dataclass, field
from typing import List
from .reglas import buscar_regla


@dataclass
class Trace:
    """Registro de reglas disparadas durante un analisis."""
    reglas: List[str] = field(default_factory=list)

    def disparar(self, regla_id: str) -> None:
        """Marca una regla como disparada."""
        if regla_id not in self.reglas:
            self.reglas.append(regla_id)

    def reglas_de_categoria(self, categoria: str) -> List[str]:
        """Filtra reglas disparadas por categoria."""
        ids = []
        for rid in self.reglas:
            r = buscar_regla(rid)
            if r and r.categoria == categoria:
                ids.append(rid)
        return ids

    def explicar(self) -> str:
        """Genera texto legible explicando que reglas dispararon."""
        if not self.reglas:
            return "Ninguna regla disparada."
        lines = []
        for rid in self.reglas:
            r = buscar_regla(rid)
            if r:
                lines.append(f"  - {r.id} | {r.nombre}: {r.impacto}")
            else:
                lines.append(f"  - {rid} | (regla no encontrada en catalogo)")
        return "\n".join(lines)

    def to_list(self) -> List[str]:
        """Devuelve lista plana de IDs (para serializar)."""
        return list(self.reglas)